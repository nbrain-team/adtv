"""
Video processing using ffmpeg-python (more reliable than moviepy)
"""
import logging
import os
import uuid
import subprocess
import json
from typing import List, Tuple
from datetime import datetime, timedelta
import ffmpeg

from core.database import SessionLocal
from . import models
from . import schemas
from core import llm_handler

logger = logging.getLogger(__name__)


def get_video_info(video_path: str) -> Tuple[float, int, int]:
    """Get video duration and dimensions using ffmpeg-python"""
    try:
        probe = ffmpeg.probe(video_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        duration = float(probe['format']['duration'])
        width = int(video_info['width'])
        height = int(video_info['height'])
        return duration, width, height
    except Exception as e:
        logger.error(f"Error probing video: {e}")
        # Try alternative method using subprocess
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 
                   'format=duration', '-of', 'json', video_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            return duration, 1920, 1080  # Default dimensions
        except:
            raise Exception("Unable to read video file")


def extract_clip(video_path: str, output_path: str, start_time: float, duration: float):
    """Extract a clip from video using ffmpeg"""
    try:
        (
            ffmpeg
            .input(video_path, ss=start_time, t=duration)
            .output(output_path, **{'c:v': 'copy', 'c:a': 'copy'})
            .overwrite_output()
            .run(capture_stderr=True)
        )
        logger.info(f"Successfully extracted clip: {output_path}")
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error: {e.stderr.decode()}")
        raise


def extract_thumbnail(video_path: str, output_path: str, timestamp: float):
    """Extract a thumbnail at specific timestamp"""
    try:
        (
            ffmpeg
            .input(video_path, ss=timestamp)
            .filter('scale', 640, -1)
            .output(output_path, vframes=1)
            .overwrite_output()
            .run(capture_stderr=True)
        )
        logger.info(f"Successfully extracted thumbnail: {output_path}")
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg thumbnail error: {e.stderr.decode()}")
        # Create a simple placeholder if thumbnail fails
        with open(output_path, 'wb') as f:
            f.write(b'')  # Empty file as placeholder


async def process_campaign(
    campaign_id: str,
    video_path: str,
    platforms: List[str],
    duration_weeks: int,
    client_id: str
):
    """Process a video campaign using ffmpeg"""
    logger.info(f"Starting campaign processing with ffmpeg: {campaign_id}")
    logger.info(f"Video path: {video_path}")
    
    with SessionLocal() as db:
        try:
            # Update campaign status
            campaign = db.query(models.Campaign).filter(
                models.Campaign.id == campaign_id
            ).first()
            
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                return
            
            campaign.status = models.CampaignStatus.PROCESSING
            campaign.progress = 10
            db.commit()
            
            # Get video info
            video_duration, width, height = get_video_info(video_path)
            logger.info(f"Video info: duration={video_duration}s, {width}x{height}")
            
            # Create clips directory
            clips_dir = os.path.join('uploads', 'clips', campaign_id)
            os.makedirs(clips_dir, exist_ok=True)
            
            # Calculate clip parameters
            clip_duration = 30.0  # 30 second clips
            num_clips = min(3, int(video_duration / clip_duration))
            
            if num_clips == 0:
                raise Exception(f"Video too short ({video_duration}s), minimum 30s required")
            
            clips = []
            
            # Create clips
            for i in range(num_clips):
                start_time = i * clip_duration
                if start_time >= video_duration:
                    break
                
                # Adjust duration for last clip
                actual_duration = min(clip_duration, video_duration - start_time)
                
                # Generate filenames
                clip_filename = f"clip_{i+1}.mp4"
                clip_path = os.path.join(clips_dir, clip_filename)
                thumbnail_filename = f"thumbnail_{i+1}.jpg"
                thumbnail_path = os.path.join(clips_dir, thumbnail_filename)
                
                # Extract clip
                logger.info(f"Extracting clip {i+1}: {start_time}s - {start_time + actual_duration}s")
                extract_clip(video_path, clip_path, start_time, actual_duration)
                
                # Extract thumbnail from middle of clip
                thumbnail_time = start_time + (actual_duration / 2)
                extract_thumbnail(video_path, thumbnail_path, thumbnail_time)
                
                # Update progress
                campaign.progress = 10 + (i + 1) * 20
                db.commit()
                
                # Create database entry
                db_clip = models.VideoClip(
                    id=str(uuid.uuid4()),
                    campaign_id=campaign.id,
                    title=f"Clip {i+1}",
                    description=f"Segment {i+1} from video",
                    duration=actual_duration,
                    start_time=start_time,
                    end_time=start_time + actual_duration,
                    video_url=clip_path,
                    thumbnail_url=thumbnail_path,
                    content_type="general",
                    suggested_caption=f"Check out this amazing content!",
                    suggested_hashtags=["#video", "#content", "#socialmedia"]
                )
                db.add(db_clip)
                clips.append(db_clip)
            
            db.commit()
            logger.info(f"Created {len(clips)} video clips")
            
            # Generate captions and create posts
            await generate_captions_and_posts(clips, platforms, duration_weeks, client_id, campaign, db)
            
            # Update campaign status
            campaign.status = models.CampaignStatus.READY
            campaign.progress = 100
            db.commit()
            
        except Exception as e:
            logger.error(f"Error processing campaign: {str(e)}", exc_info=True)
            campaign.status = models.CampaignStatus.FAILED
            campaign.error_message = str(e)
            db.commit()
            raise


async def generate_captions_and_posts(clips, platforms, duration_weeks, client_id, campaign, db):
    """Generate styled captions and create social posts"""
    # Generate captions for each clip
    for db_clip in clips:
        # Use the same caption generation logic
        examples = """
🎥 BLOOPERS!! Episode #1 😂
Because not everything goes as planned on American Dream TV… 😂👀😜
Behind the scenes, real moments, and a whole lot of laughs!
🎬 As seen on American Dream TV
📍 Nebraska | Real estate. Culture. Lifestyle.
#AmericanDreamTV #RealEstateLife #BehindTheScenes

--------

The American Dream isn't just about where you're going, it's about the drive to get there.🏁
Proud to represent Valentine on a show that shares real stories, real grit, and the people pushing forward every day.
#AmericanDreamTV #DriveTheDream #RealStories
"""
        
        prompt = f"""Generate a social media caption for this video clip in the style of these examples. Make it engaging with emojis, calls to action, and relevant hashtags.

Examples:
{examples}

Clip details:
Title: {db_clip.title}
Description: {db_clip.description}

Caption:"""
        
        try:
            caption = await llm_handler.generate_text(prompt)
            db_clip.suggested_caption = caption
        except:
            # Fallback caption if LLM fails
            db_clip.suggested_caption = f"🎬 {db_clip.title} - Don't miss this amazing content! 🔥\n\n#VideoContent #SocialMedia #MustWatch"
        
        # Generate hashtags
        hashtag_prompt = f"Generate 10 relevant hashtags for this video clip about: {db_clip.description}"
        try:
            hashtags_text = await llm_handler.generate_text(hashtag_prompt)
            db_clip.suggested_hashtags = [h.strip() for h in hashtags_text.split() if h.startswith('#')][:10]
        except:
            db_clip.suggested_hashtags = ["#video", "#content", "#socialmedia", "#viral", "#trending"]
    
    db.commit()
    
    # Create social posts schedule
    total_clips = len(clips)
    posts_per_week = max(3, total_clips // duration_weeks)
    
    start_date = datetime.utcnow() + timedelta(days=1)
    current_date = start_date
    
    for i, clip in enumerate(clips):
        post = models.SocialPost(
            id=str(uuid.uuid4()),
            client_id=client_id,
            campaign_id=campaign.id,
            video_clip_id=clip.id,
            content=clip.suggested_caption,
            platforms=platforms,
            scheduled_time=current_date,
            status=models.PostStatus.SCHEDULED
        )
        db.add(post)
        
        # Schedule next post 2-3 days later
        current_date += timedelta(days=2 if i % 2 == 0 else 3)
    
    db.commit()
    logger.info(f"Created {len(clips)} scheduled posts") 
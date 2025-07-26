"""
Video processing using Cloudinary - cloud-based solution for reliable video processing
"""
import logging
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid

from core.database import SessionLocal
from . import models
from core import llm_handler

logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET')
)


async def process_campaign(
    campaign_id: str,
    video_path: str,
    platforms: List[str],
    duration_weeks: int,
    client_id: str
):
    """Process a video campaign using Cloudinary"""
    logger.info(f"Starting Cloudinary video processing for campaign: {campaign_id}")
    
    with SessionLocal() as db:
        try:
            # Update campaign status
            campaign = db.query(models.Campaign).filter(
                models.Campaign.id == campaign_id
            ).first()
            
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                return
            
            logger.info(f"Setting campaign {campaign_id} to PROCESSING status")
            campaign.status = models.CampaignStatus.PROCESSING
            campaign.progress = 10
            db.commit()
            logger.info(f"Campaign {campaign_id} progress set to 10%")
            
            # Upload video to Cloudinary
            logger.info(f"Uploading video to Cloudinary from path: {video_path}")
            try:
                upload_result = cloudinary.uploader.upload_large(
                    video_path,
                    resource_type="video",
                    public_id=f"campaigns/{campaign_id}/main_video",
                    overwrite=True
                )
                
                video_url = upload_result['secure_url']
                duration = upload_result.get('duration', 90)  # Video duration in seconds
                logger.info(f"Video uploaded successfully. URL: {video_url}, Duration: {duration}s")
            except Exception as e:
                logger.error(f"Failed to upload video to Cloudinary: {str(e)}")
                campaign.status = models.CampaignStatus.FAILED
                campaign.error_message = f"Video upload failed: {str(e)}"
                db.commit()
                raise
            
            # Generate clips using Cloudinary transformations
            clips = []
            clip_duration = 30  # 30-second clips
            num_clips = min(3, int(duration / clip_duration))
            
            for i in range(num_clips):
                # Check if campaign was cancelled/deleted
                db.refresh(campaign)
                if campaign.status == models.CampaignStatus.FAILED and campaign.error_message == "Cancelled by user":
                    logger.info(f"Campaign {campaign_id} was cancelled, stopping processing")
                    return
                
                start_time = i * clip_duration
                end_time = min(start_time + clip_duration, duration)
                
                # Generate clip URL using Cloudinary transformations
                clip_public_id = f"campaigns/{campaign_id}/clip_{i+1}"
                
                # Create clip transformation
                clip_url, _ = cloudinary_url(
                    upload_result['public_id'],
                    resource_type="video",
                    transformation=[
                        {'start_offset': start_time, 'end_offset': end_time},
                        {'quality': 'auto', 'fetch_format': 'mp4'}
                    ]
                )
                
                # Generate thumbnail at middle of clip
                thumbnail_time = start_time + (end_time - start_time) / 2
                thumbnail_url, _ = cloudinary_url(
                    upload_result['public_id'],
                    resource_type="video",
                    transformation=[
                        {'start_offset': thumbnail_time},
                        {'width': 640, 'height': 360, 'crop': 'fill'},
                        {'quality': 'auto', 'fetch_format': 'jpg'}
                    ]
                )
                
                # Create database entry
                db_clip = models.VideoClip(
                    id=str(uuid.uuid4()),
                    campaign_id=campaign.id,
                    title=f"Clip {i+1}",
                    description=f"Segment {i+1} from video",
                    duration=end_time - start_time,
                    start_time=start_time,
                    end_time=end_time,
                    video_url=clip_url,
                    thumbnail_url=thumbnail_url,
                    content_type="general",
                    suggested_caption=f"Check out this amazing content!",
                    suggested_hashtags=["#video", "#content", "#socialmedia"]
                )
                db.add(db_clip)
                clips.append(db_clip)
                
                # Update progress
                campaign.progress = 30 + (i + 1) * 20
                db.commit()
            
            logger.info(f"Created {len(clips)} video clips")
            
            # Generate AI captions and create posts
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
    """Generate AI-powered captions and create social posts"""
    for db_clip in clips:
        # Generate engaging caption
        prompt = f"""Generate a social media caption for this video clip in an engaging, authentic style.

Clip details:
Title: {db_clip.title}
Description: {db_clip.description}
Duration: {db_clip.duration} seconds

Make it conversational, include relevant emojis, a call to action, and 5-7 relevant hashtags.
Keep it under 280 characters for Twitter compatibility.

Caption:"""
        
        try:
            caption = await llm_handler.generate_text(prompt)
            db_clip.suggested_caption = caption
            
            # Extract hashtags
            import re
            hashtags = re.findall(r'#\w+', caption)
            db_clip.suggested_hashtags = hashtags[:10]
        except:
            # Fallback caption
            db_clip.suggested_caption = f"🎬 {db_clip.title} - Don't miss this! 🔥\n\n#VideoContent #SocialMedia #MustWatch"
            db_clip.suggested_hashtags = ["#video", "#content", "#socialmedia", "#viral", "#trending"]
    
    db.commit()
    
    # Create social posts schedule
    start_date = datetime.utcnow() + timedelta(days=1)
    posts_per_week = max(1, len(clips) // duration_weeks)
    
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
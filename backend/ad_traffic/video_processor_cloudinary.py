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

# Add this constant at the top after imports
PLATFORM_ASPECT_RATIOS = {
    "facebook": [
        {"name": "desktop", "ratio": "16:9", "width": 1920, "height": 1080},  # Desktop-focused
        {"name": "feed", "ratio": "1:1", "width": 1080, "height": 1080}
    ],
    "instagram": [
        {"name": "mobile", "ratio": "9:16", "width": 1080, "height": 1920},  # Mobile-focused
        {"name": "feed", "ratio": "1:1", "width": 1080, "height": 1080}
    ],
    "tiktok": [
        {"name": "video", "ratio": "9:16", "width": 1080, "height": 1920}
    ]
}


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
            campaign = db.query(models.AdTrafficCampaign).filter(
                models.AdTrafficCampaign.id == campaign_id
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
            
            # Analyze video content and generate AI captions
            await analyze_and_generate_captions(clips, platforms, duration_weeks, client_id, campaign, db, upload_result)
            
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


async def analyze_and_generate_captions(clips, platforms, duration_weeks, client_id, campaign, db, cloudinary_upload=None):
    """Analyze video content and generate contextual AI-powered captions"""
    import base64
    
    # Get video metadata for context
    video_context = f"""
Video Title: {campaign.name}
Duration: {cloudinary_upload.get('duration', 0) if cloudinary_upload else 'Multiple videos'} seconds
Platforms: {', '.join(platforms)}
"""
    
    for i, db_clip in enumerate(clips):
        try:
            # For multiple videos, we need to extract the public_id from the clip's source URL
            if not cloudinary_upload and db_clip.source_video_url:
                # Extract public_id from the Cloudinary URL
                # URL format: https://res.cloudinary.com/{cloud_name}/video/upload/v{version}/{public_id}.mp4
                url_parts = db_clip.source_video_url.split('/')
                if 'upload' in url_parts:
                    upload_idx = url_parts.index('upload')
                    if upload_idx + 2 < len(url_parts):
                        public_id = url_parts[upload_idx + 2].rsplit('.', 1)[0]
                else:
                    logger.warning(f"Could not extract public_id from URL: {db_clip.source_video_url}")
                    public_id = None
            elif cloudinary_upload:
                public_id = cloudinary_upload['public_id']
            else:
                public_id = None
                
            # Extract a frame from the middle of the clip for analysis
            frame_time = db_clip.start_time + (db_clip.duration / 2)
            
            if public_id:
                # Generate a frame URL using Cloudinary transformation
                frame_url, _ = cloudinary_url(
                    public_id,
                    resource_type="video",
                    transformation=[
                        {'start_offset': frame_time, 'duration': 1},  # Extract 1 second frame
                        {'width': 800, 'height': 450, 'crop': 'fill'},
                        {'quality': 'auto', 'fetch_format': 'jpg'}
                    ]
                )
                
                logger.info(f"Generated frame URL for clip {i+1}: {frame_url[:100]}...")
                
                # Download and encode the frame for vision analysis
                try:
                    response = requests.get(frame_url, timeout=10)
                    if response.status_code == 200:
                        frame_base64 = base64.b64encode(response.content).decode('utf-8')
                        logger.info(f"Successfully downloaded frame for clip {i+1}, size: {len(response.content)} bytes")
                        
                        # Use vision-capable LLM to analyze the frame
                        vision_prompt = f"""Analyze this video frame and describe what's happening in the scene. 
Focus on:
- Main subjects or people
- Actions taking place  
- Setting/location
- Key objects or details
- Overall mood/tone

This is frame from timestamp {frame_time:.1f}s of a video titled "{campaign.name}"."""
                        
                        try:
                            # Get frame analysis from vision model
                            frame_description = await llm_handler.analyze_image(frame_base64, vision_prompt)
                            logger.info(f"Frame analysis for clip {i+1}: {frame_description[:100]}...")
                        except Exception as e:
                            logger.error(f"Vision analysis failed for clip {i+1}: {str(e)}")
                            frame_description = f"Clip showing content from {db_clip.start_time:.0f}s to {db_clip.end_time:.0f}s"
                    else:
                        logger.warning(f"Failed to download frame for clip {i+1}, status code: {response.status_code}")
                        frame_description = f"Video segment {i+1}"
                except Exception as e:
                    logger.error(f"Error downloading frame for clip {i+1}: {str(e)}")
                    frame_description = f"Video segment {i+1}"
            else:
                logger.warning(f"No public_id available for clip {i+1}")
                frame_description = f"Video segment {i+1} - {db_clip.title}"
                
        except Exception as e:
            logger.warning(f"Could not analyze frame for clip {i+1}: {str(e)}")
            frame_description = f"Video segment {i+1}"
        
        # Generate contextual caption based on actual content
        # If we don't have a good frame description, use campaign context
        if frame_description.startswith("Video segment") or frame_description.startswith("Clip showing"):
            # Use campaign name and details for context
            # Vary the caption style based on clip index
            caption_styles = [
                "storytelling", "question-based", "inspirational", 
                "behind-the-scenes", "educational", "call-to-action focused"
            ]
            style = caption_styles[i % len(caption_styles)]
            
            prompt = f"""Generate an engaging social media caption for this video clip using a {style} approach.

Campaign: {campaign.name}
Client: {campaign.client_id}
Platforms: {', '.join(platforms)}
Clip: {i+1} of {len(clips)}
Duration: {db_clip.duration:.0f} seconds

Style Guide for {style}:
- Storytelling: Start with a compelling hook, share a brief story or moment
- Question-based: Ask an engaging question to drive comments and engagement
- Inspirational: Share motivating message with powerful language
- Behind-the-scenes: Give insider perspective, use casual tone
- Educational: Share a tip, fact, or insight that provides value
- Call-to-action focused: Direct viewers to take specific action

Create a caption that:
- Uses the {style} approach
- Includes 2-3 relevant emojis
- Has natural, conversational language
- Ends with 5-7 hashtags
- Stays under 280 characters

Examples of great captions:
🎬 Ever wonder what goes into creating the perfect shot? Here's a sneak peek behind the lens! 👀✨ #BehindTheScenes #VideoProduction #ContentCreation #CreativeProcess #FilmMaking

What's your biggest challenge when creating content? 🤔 Drop a comment below - we'd love to help! 💡 #ContentStrategy #CreatorCommunity #VideoMarketing #SocialMediaTips #AskUsAnything

The best stories aren't scripted - they're discovered. 🎯 Watch how we captured this authentic moment... #Storytelling #AuthenticContent #VideoMarketing #RealMoments #ContentCreators

Caption:"""
        else:
            # We have good frame analysis, use it
            prompt = f"""Generate an engaging social media caption for this specific video clip.

CONTEXT:
{video_context}

WHAT'S IN THIS CLIP:
{frame_description}

Clip timing: {db_clip.start_time:.0f}s - {db_clip.end_time:.0f}s (clip {i+1} of {len(clips)})

Create a caption that:
- Directly relates to what's shown in this specific clip
- Uses natural, conversational language
- Includes 2-3 relevant emojis
- Has a clear call to action
- Ends with 5-7 hashtags relevant to the content
- Stays under 280 characters for Twitter

Caption:"""
        
        try:
            caption = await llm_handler.generate_text(prompt)
            db_clip.suggested_caption = caption
            
            # Extract hashtags
            import re
            hashtags = re.findall(r'#\w+', caption)
            db_clip.suggested_hashtags = hashtags[:10]
            
            # Update clip with content description
            db_clip.description = frame_description[:200]  # Store abbreviated description
            
        except Exception as e:
            logger.error(f"Error generating caption for clip {i+1}: {str(e)}")
            # Fallback caption
            db_clip.suggested_caption = f"🎬 {campaign.name} - Part {i+1} 🔥\n\nDon't miss this moment!\n\n#VideoContent #SocialMedia #MustWatch"
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


async def process_campaign_with_multiple_videos(
    campaign_id: str,
    video_paths: List[str],
    platforms: List[str],
    duration_weeks: int,
    client_id: str
):
    """Process multiple videos for a campaign with platform-specific versions"""
    logger.info(f"Starting Cloudinary processing for {len(video_paths)} videos")
    
    with SessionLocal() as db:
        try:
            campaign = db.query(models.AdTrafficCampaign).filter(
                models.AdTrafficCampaign.id == campaign_id
            ).first()
            
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                return
            
            campaign.status = models.CampaignStatus.PROCESSING
            campaign.progress = 10
            db.commit()
            
            all_clips = []
            total_videos = len(video_paths)
            video_urls = []  # Store all video URLs
            
            for video_idx, video_path in enumerate(video_paths):
                logger.info(f"Processing video {video_idx + 1}/{total_videos}: {video_path}")
                
                # Upload video to Cloudinary
                try:
                    upload_result = cloudinary.uploader.upload_large(
                        video_path,
                        resource_type="video",
                        public_id=f"campaigns/{campaign_id}/video_{video_idx + 1}",
                        overwrite=True
                    )
                    
                    video_url = upload_result['secure_url']
                    video_urls.append(video_url)  # Store the URL
                    duration = upload_result.get('duration', 90)
                    logger.info(f"Video {video_idx + 1} uploaded. Duration: {duration}s")
                except Exception as e:
                    logger.error(f"Failed to upload video {video_idx + 1}: {str(e)}")
                    continue
                
                # Generate clips from this video
                clip_duration = 30  # 30-second clips
                num_clips = min(3, int(duration / clip_duration))
                
                for clip_idx in range(num_clips):
                    start_time = clip_idx * clip_duration
                    end_time = min(start_time + clip_duration, duration)
                    
                    # Create platform-specific versions
                    platform_versions = {}
                    
                    # Default clip URL (original aspect ratio)
                    default_clip_url, _ = cloudinary_url(
                        upload_result['public_id'],
                        resource_type="video",
                        transformation=[
                            {'start_offset': start_time, 'end_offset': end_time},
                            {'quality': 'auto', 'fetch_format': 'mp4'}
                        ]
                    )
                    
                    for platform in platforms:
                        platform_lower = platform.lower()
                        if platform_lower in PLATFORM_ASPECT_RATIOS:
                            for aspect_config in PLATFORM_ASPECT_RATIOS[platform_lower]:
                                version_key = f"{platform_lower}_{aspect_config['name']}"
                                
                                # Generate clip URL with platform-specific transformation
                                clip_url, _ = cloudinary_url(
                                    upload_result['public_id'],
                                    resource_type="video",
                                    transformation=[
                                        {'start_offset': start_time, 'end_offset': end_time},
                                        {
                                            'width': aspect_config['width'],
                                            'height': aspect_config['height'],
                                            'crop': 'fill',
                                            'gravity': 'center'
                                        },
                                        {'quality': 'auto', 'fetch_format': 'mp4'}
                                    ]
                                )
                                
                                platform_versions[version_key] = {
                                    "url": clip_url,
                                    "aspect_ratio": aspect_config['ratio'],
                                    "dimensions": f"{aspect_config['width']}x{aspect_config['height']}"
                                }
                    
                    # Generate thumbnail
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
                        source_video_url=video_url,
                        title=f"Video {video_idx + 1} - Clip {clip_idx + 1}",
                        description=f"Segment from video {video_idx + 1}",
                        duration=end_time - start_time,
                        start_time=start_time,
                        end_time=end_time,
                        video_url=default_clip_url,  # Use the default clip URL
                        thumbnail_url=thumbnail_url,
                        platform_versions=platform_versions,
                        content_type="general",
                        aspect_ratio="original",
                        suggested_caption=f"Check out this amazing content!",
                        suggested_hashtags=["#video", "#content", "#socialmedia"]
                    )
                    db.add(db_clip)
                    all_clips.append(db_clip)
                
                # Update progress
                progress = 30 + (video_idx + 1) * (60 / total_videos)
                campaign.progress = int(progress)
                db.commit()
            
            # Store video URLs in the campaign
            campaign.video_urls = video_urls
            db.commit()
            
            logger.info(f"Created {len(all_clips)} total clips from {total_videos} videos")
            
            # Analyze and generate captions for all clips
            await analyze_and_generate_captions(
                all_clips, platforms, duration_weeks, client_id, campaign, db, None
            )
            
            # Create social posts schedule
            start_date = datetime.utcnow() + timedelta(days=1)
            posts_per_week = max(1, len(all_clips) // duration_weeks)
            
            current_date = start_date
            for i, clip in enumerate(all_clips):
                # Create separate posts for each platform
                for platform in platforms:
                    # Determine which video version to use based on platform
                    platform_lower = platform.lower()
                    video_url = clip.video_url  # Default
                    
                    # Use platform-specific version if available
                    if platform_lower == "facebook" and clip.platform_versions:
                        # Use desktop version for Facebook
                        fb_desktop = clip.platform_versions.get("facebook_desktop")
                        if fb_desktop and isinstance(fb_desktop, dict):
                            video_url = fb_desktop.get("url", clip.video_url)
                    elif platform_lower == "instagram" and clip.platform_versions:
                        # Use mobile version for Instagram
                        ig_mobile = clip.platform_versions.get("instagram_mobile")
                        if ig_mobile and isinstance(ig_mobile, dict):
                            video_url = ig_mobile.get("url", clip.video_url)
                    
                    post = models.SocialPost(
                        id=str(uuid.uuid4()),
                        client_id=client_id,
                        campaign_id=campaign.id,
                        video_clip_id=clip.id,
                        content=clip.suggested_caption,
                        platforms=[platform],  # Single platform per post
                        scheduled_time=current_date,
                        status=models.PostStatus.SCHEDULED,
                        media_urls=[video_url]  # Include the platform-specific video URL
                    )
                    db.add(post)
                
                # Schedule next post 2-3 days later
                current_date += timedelta(days=2 if i % 2 == 0 else 3)
            
            db.commit()
            logger.info(f"Created {len(all_clips)} scheduled posts")
            
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
"""
Actual video processing with moviepy
"""
import logging
from typing import List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import os
import uuid

# Check if moviepy is available
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("moviepy not installed! Video processing will create mock data.")
    MOVIEPY_AVAILABLE = False

from core.database import SessionLocal
from . import models
from . import schemas
from core import llm_handler

logger = logging.getLogger(__name__)

async def process_campaign(
    campaign_id: str,
    video_path: str,
    platforms: List[str],
    duration_weeks: int,
    client_id: str
):
    """Process a video campaign - extract clips and create social posts"""
    logger.info(f"Starting campaign processing: {campaign_id}")
    logger.info(f"Video path: {video_path}")
    logger.info(f"Platforms: {platforms}, Duration: {duration_weeks} weeks")
    logger.info(f"Moviepy available: {MOVIEPY_AVAILABLE}")
    
    with SessionLocal() as db:
        try:
            # Update campaign status
            logger.info(f"Fetching campaign {campaign_id} from database...")
            campaign = db.query(models.Campaign).filter(
                models.Campaign.id == campaign_id
            ).first()
            
            if not campaign:
                logger.error(f"Campaign {campaign_id} not found")
                return
            
            logger.info(f"Updating campaign status to PROCESSING...")
            campaign.status = models.CampaignStatus.PROCESSING
            campaign.progress = 10
            db.commit()
            logger.info(f"Campaign status updated successfully")
            
            # Create clips directory
            clips_dir = os.path.join('uploads', 'clips', campaign_id)
            os.makedirs(clips_dir, exist_ok=True)
            
            if MOVIEPY_AVAILABLE:
                # Process with actual video
                await process_with_moviepy(campaign, video_path, clips_dir, platforms, duration_weeks, client_id, db)
            else:
                # Fallback: Create mock data
                await process_with_mock_data(campaign, video_path, clips_dir, platforms, duration_weeks, client_id, db)
            
        except Exception as e:
            logger.error(f"Error processing campaign: {str(e)}", exc_info=True)
            campaign.status = models.CampaignStatus.FAILED
            campaign.error_message = str(e)
            db.commit()


async def process_with_moviepy(campaign, video_path, clips_dir, platforms, duration_weeks, client_id, db):
    """Process video using moviepy"""
    # Load the video
    video = VideoFileClip(video_path)
    video_duration = video.duration
    logger.info(f"Video duration: {video_duration} seconds")
    
    # Create 3 clips of 30 seconds each
    clip_duration = 30
    clips = []
    for i in range(3):
        start_time = i * clip_duration
        if start_time >= video_duration:
            break
        
        end_time = min(start_time + clip_duration, video_duration)
        clip = video.subclip(start_time, end_time)
        
        # Save clip
        clip_filename = f"clip_{i+1}.mp4"
        clip_path = os.path.join(clips_dir, clip_filename)
        clip.write_videofile(clip_path, codec='libx264', audio_codec='aac')
        logger.info(f"Created clip {clip_filename}")
        
        # Generate thumbnail
        thumbnail_time = start_time + (end_time - start_time) / 2
        thumbnail_filename = f"thumbnail_{i+1}.jpg"
        thumbnail_path = os.path.join(clips_dir, thumbnail_filename)
        clip.save_frame(thumbnail_path, t=thumbnail_time)
        logger.info(f"Created thumbnail {thumbnail_filename}")
        
        # Create db entry
        db_clip = models.VideoClip(
            id=str(uuid.uuid4()),
            campaign_id=campaign.id,
            title=f"Clip {i+1}",
            description=f"Segment {i+1} from video",
            duration=end_time - start_time,
            start_time=start_time,
            end_time=end_time,
            video_url=clip_path,
            thumbnail_url=thumbnail_path,
            content_type="general",
            suggested_caption=f"Check out this clip!",
            suggested_hashtags=["#adtraffic", "#video"]
        )
        db.add(db_clip)
        clips.append(db_clip)
    
    # Generate captions and create posts
    await generate_captions_and_posts(clips, platforms, duration_weeks, client_id, campaign, db)


async def process_with_mock_data(campaign, video_path, clips_dir, platforms, duration_weeks, client_id, db):
    """Create mock data when moviepy is not available"""
    logger.warning("Creating mock video clips due to missing moviepy")
    
    # Create 3 mock clips
    clips = []
    for i in range(3):
        # Create mock clip entry
        db_clip = models.VideoClip(
            id=str(uuid.uuid4()),
            campaign_id=campaign.id,
            title=f"Clip {i+1}",
            description=f"Segment {i+1} from video (mock data)",
            duration=30.0,
            start_time=i * 30,
            end_time=(i + 1) * 30,
            video_url=video_path,  # Use original video path
            thumbnail_url=f"mock_thumbnail_{i+1}.jpg",
            content_type="general",
            suggested_caption=f"Check out this amazing content!",
            suggested_hashtags=["#adtraffic", "#video", "#marketing"]
        )
        db.add(db_clip)
        clips.append(db_clip)
    
    # Generate captions and create posts
    await generate_captions_and_posts(clips, platforms, duration_weeks, client_id, campaign, db)


async def generate_captions_and_posts(clips, platforms, duration_weeks, client_id, campaign, db):
    """Generate styled captions and create social posts"""
    # After creating clips
    for db_clip in clips:
        # Generate styled caption
        examples = """
🎥 BLOOPERS!! Episode #1 😂
Because not everything goes as planned on American Dream TV… 😂👀😜
Behind the scenes, real moments, and a whole lot of laughs!
Sometimes the best parts never make the final cut — so here’s a sneak peek at the real real estate life.
🎬 As seen on American Dream TV
📍 Nebraska | Real estate. Culture. Lifestyle.
✨ Hosted by yours truly — Dodi Osburn
Follow for more behind-the-scenes, real estate tips, and a few more bloopers too!
#DodiOsburn #AmericanDreamTV #PFY #ADTV #RealEstateLife #RealtorReels #BuildYourOwnHome #RealEstateHumor #FunnyReel #LOLReels #RelatableRealtor #RealEstateTips #HousingMarket2025 #LowInventory #LandForSale #FirstTimeBuyer #RealEstateForSale #MidwestRealEstate #NebraskaLiving #WesternNebraska #SandhillsLiving #SmallTownCharm #SmallTownBigHeart #PositiveMedia #Lifestyle #CommunitySpotlight #ComedyContent #RealEstateInfluencer #RealtorLife

--------

𝐕𝐚𝐥𝐞𝐧𝐭𝐢𝐧𝐞—𝐂𝐚𝐥𝐥𝐢𝐧𝐠 𝐀𝐥𝐥 𝐒𝐭𝐨𝐫𝐲𝐭𝐞𝐥𝐥𝐞𝐫𝐬!
I’m searching for stories that bring out the soul of Nebraska. Ranchers, artists, local legends, this is your time.
📬 DM me if you’re ready for the spotlight.
#ValentineNE #NebraskaStories #PFY #TheAmericanDream #HeartlandLiving

--------

The American Dream isn’t just about where you’re going, it’s about the drive to get there.🏁
Proud to represent Valentine on a show that shares real stories, real grit, and the people pushing forward every day. 
Catch the energy in this new ADTV feature, and let’s keep driving forward.
#AmericanDreamTV #PFY #PositiveMedia #RealEstate #Lifestyle #DriveTheDream #Valentine #CommunityConnection #CarCulture #GritAndDrive

-------

Thinking about buying land or building your dream home?  😅🏠🚗💥🐶Watch till the end 👀📩 DM me — I’ll help you do it the safe way!Find more info at my website I❤️🏠🏜️-Dodi Osburn.com Nebraska Realty @americandreamtv 

-------

Thinking about buying land or building your dream home?  😅🏠🚗💥🐶Watch till the end 👀📩 DM me — I’ll help you do it the safe way!Find more info at my website I❤️🏠🏜️-Dodi Osburn.com Nebraska Realty @americandreamtv  #DodiOsburn 💼 #AmericanDreamTV #ADTV #ADTVHost #PFY😂 #RealEstateHumor #FunnyReel #LOLReels #PlotTwist #ComedyContent📈 #RelatableRealtor #RealEstateTips #BuildYourOwnHome #LowInventory #HousingMarket2025📍 #ValentineNebraska #HeartCity #HistoricMainStreet #SmallTownCharm🌾 #SandhillsLiving #WesternNebraska #MidwestRealEstate #NebraskaLiving❤️ #SmallTownBigHeart #Lifestyle #CommunitySpotlight #PositiveMedia🏡 #RealtorReels #RealEstateLife #RealEstate #LandForSale📝 #FirstTimeBuyer #RealEstateForSale #DodiOsburn

------

New owners, same historic charm.
The Old Mill Restaurant is serving up tradition with a fresh new twist—come for the classics, stay for the story.
Tag someone you’d bring here for comfort food! 🥪
#OldMillEats #HistoricDining #ComfortFoodCravings #FamilyTableVibes #PFY #AmericanDreamTV
The Twister 
KVSH Radio  
Visit Valentine & Cherry County

------

Small-town love, big heart vibes 🤍
Valentine truly showed up—from charming boutiques to unforgettable bites.
Have you watched it yet? Let’s celebrate the magic of small towns!
#PFY #ValentineNebraska #ShopLocal #HeartlandVibes #MidwestMoments #HiddenGems Broken Spoke Boutique  Visit Valentine & Cherry County

"""
        prompt = f"""Generate a social media caption for this video clip in the style of these examples. Make it engaging with emojis, bold text, calls to action, and relevant hashtags.

Examples:
{examples}

Clip details:
Title: {db_clip.title}
Description: {db_clip.description}
Content Type: {db_clip.content_type}

Caption:"""
        caption = await llm_handler.generate_text(prompt)
        db_clip.suggested_caption = caption
        
        # Generate hashtags
        hashtag_prompt = f"Generate 10-15 relevant hashtags for this clip: {db_clip.description}"
        hashtags = await llm_handler.generate_text(hashtag_prompt)
        db_clip.suggested_hashtags = [h.strip() for h in hashtags.split() if h.startswith('#')]

    db.commit()
    logger.info(f"Created {len(clips)} video clips")
    
    # Create social posts
    total_clips = len(clips)
    start_date = datetime.utcnow() + timedelta(days=1)
    current_date = start_date
    clip_index = 0
    while clip_index < total_clips:
        clip = clips[clip_index]
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
        clip_index += 1
        current_date += timedelta(days=2)
    
    db.commit()
    
    # Update campaign
    campaign.status = models.CampaignStatus.READY
    campaign.progress = 100
    db.commit() 
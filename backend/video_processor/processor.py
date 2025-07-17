import os
import cv2
import subprocess
import tempfile
import base64
import json
from typing import List, Dict, Tuple
from datetime import datetime
import logging

from openai import OpenAI
from sqlalchemy.orm import Session
from core.database import SessionLocal
from . import models

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Platform specifications
PLATFORM_SPECS = {
    "instagram": {
        "max_duration": 60,  # 60 seconds for Reels
        "aspect_ratio": "9:16",
        "resolution": "1080x1920"
    },
    "youtube": {
        "max_duration": 60,  # 60 seconds for Shorts
        "aspect_ratio": "9:16",
        "resolution": "1080x1920"
    },
    "facebook": {
        "max_duration": 120,  # 2 minutes for short videos
        "aspect_ratio": "1:1",
        "resolution": "1080x1080"
    }
}

def extract_frames(video_path: str, interval_seconds: int = 5) -> List[Tuple[float, str]]:
    """Extract frames from video at specified intervals"""
    frames = []
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    # Extract frames at intervals
    for timestamp in range(0, int(duration), interval_seconds):
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        success, frame = cap.read()
        
        if success:
            # Encode frame to base64
            _, buffer = cv2.imencode('.jpg', frame)
            base64_image = base64.b64encode(buffer).decode('utf-8')
            frames.append((timestamp, base64_image))
    
    cap.release()
    return frames

def analyze_frames_with_vision(frames: List[Tuple[float, str]]) -> List[Dict]:
    """Analyze frames using OpenAI Vision API to identify key segments"""
    
    # Prepare messages for Vision API
    messages = [
        {
            "role": "system",
            "content": """You are analyzing a realtor promotional video. Identify distinct segments that would make good social media clips:
            
            Types of segments to identify:
            1. Client testimonials - clients speaking about their experience
            2. Property showcases - realtor showing property features
            3. Process explanations - realtor explaining buying/selling process
            4. Market insights - realtor discussing market trends
            5. Success stories - celebrating closings or achievements
            6. Personal introductions - realtor introducing themselves
            7. Call-to-action segments - asking viewers to contact/follow
            
            For each segment, provide:
            - start_time: when the segment begins (seconds)
            - end_time: when the segment ends (seconds)
            - type: the segment type from above
            - title: a catchy title for the clip
            - description: what happens in this segment
            - key_moment: the most impactful moment timestamp
            - speaker: who is speaking (realtor/client/both)
            
            Return as JSON array."""
        }
    ]
    
    # Add frames to the message
    frame_descriptions = []
    for timestamp, base64_image in frames:
        frame_descriptions.append(f"Frame at {timestamp}s")
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": f"Frame at {timestamp} seconds:"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "low"
                    }
                }
            ]
        })
    
    messages.append({
        "role": "user",
        "content": "Based on these frames, identify all the distinct segments that would make good social media clips. Focus on complete thoughts and conversations."
    })
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Latest multimodal model - faster and more accurate
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )
        
        # Parse the response
        content = response.choices[0].message.content
        # Extract JSON from the response
        import re
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            segments = json.loads(json_match.group())
            return segments
        else:
            logger.error("No JSON found in Vision API response")
            return []
            
    except Exception as e:
        logger.error(f"Vision API error: {str(e)}")
        return []

def extract_clip(video_path: str, start_time: float, end_time: float, output_path: str, platform: str):
    """Extract a clip from the video using ffmpeg"""
    
    spec = PLATFORM_SPECS[platform]
    duration = end_time - start_time
    
    # Ensure clip doesn't exceed platform limits
    if duration > spec["max_duration"]:
        duration = spec["max_duration"]
    
    # Build ffmpeg command
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-ss", str(start_time),
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k"
    ]
    
    # Add platform-specific filters
    if platform in ["instagram", "youtube"]:
        # Vertical video (9:16)
        cmd.extend([
            "-vf", f"scale={spec['resolution'].split('x')[0]}:-2,crop={spec['resolution'].replace('x', ':')}",
        ])
    elif platform == "facebook":
        # Square video (1:1)
        cmd.extend([
            "-vf", f"crop=min(iw\\,ih):min(iw\\,ih),scale={spec['resolution'].split('x')[0]}:{spec['resolution'].split('x')[0]}",
        ])
    
    cmd.extend(["-y", output_path])
    
    # Run ffmpeg
    subprocess.run(cmd, check=True, capture_output=True)

def generate_thumbnail(video_path: str, timestamp: float, output_path: str):
    """Generate a thumbnail from the video at specified timestamp"""
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-ss", str(timestamp),
        "-vframes", "1",
        "-q:v", "2",
        "-y", output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def process_video(job_id: str, video_path: str, platforms: List[str]):
    """Main video processing function"""
    db = SessionLocal()
    
    try:
        # Update job status
        job = db.query(models.VideoProcessingJob).filter_by(id=job_id).first()
        job.status = "analyzing"
        job.progress = 10
        db.commit()
        
        logger.info(f"Starting video processing for job {job_id}")
        
        # Extract frames for analysis
        frames = extract_frames(video_path, interval_seconds=5)
        logger.info(f"Extracted {len(frames)} frames")
        
        job.progress = 30
        db.commit()
        
        # Analyze with Vision API
        segments = analyze_frames_with_vision(frames)
        logger.info(f"Identified {len(segments)} segments")
        
        job.status = "extracting"
        job.progress = 50
        db.commit()
        
        # Create output directories
        clips_dir = os.path.join("uploads", "clips", job_id)
        thumbs_dir = os.path.join("uploads", "thumbnails", job_id)
        os.makedirs(clips_dir, exist_ok=True)
        os.makedirs(thumbs_dir, exist_ok=True)
        
        # Process each segment for each platform
        total_clips = len(segments) * len(platforms)
        clips_processed = 0
        
        for segment in segments[:10]:  # Limit to 10 segments max
            for platform in platforms:
                clip_id = f"{job_id}_{clips_processed}"
                
                # Generate clip
                clip_path = os.path.join(clips_dir, f"{clip_id}_{platform}.mp4")
                thumb_path = os.path.join(thumbs_dir, f"{clip_id}.jpg")
                
                try:
                    # Extract clip
                    extract_clip(
                        video_path,
                        segment["start_time"],
                        segment["end_time"],
                        clip_path,
                        platform
                    )
                    
                    # Generate thumbnail
                    generate_thumbnail(
                        video_path,
                        segment.get("key_moment", segment["start_time"]),
                        thumb_path
                    )
                    
                    # Save to database
                    clip = models.VideoClip(
                        job_id=job_id,
                        title=f"{segment['title']} ({platform.capitalize()})",
                        description=segment["description"],
                        duration=segment["end_time"] - segment["start_time"],
                        start_time=segment["start_time"],
                        end_time=segment["end_time"],
                        platform=platform,
                        file_path=clip_path,
                        thumbnail_path=thumb_path,
                        clip_metadata={
                            "type": segment.get("type"),
                            "speaker": segment.get("speaker")
                        }
                    )
                    db.add(clip)
                    
                except Exception as e:
                    logger.error(f"Error processing clip {clip_id}: {str(e)}")
                
                clips_processed += 1
                job.progress = 50 + int((clips_processed / total_clips) * 40)
                db.commit()
        
        # Mark job as complete
        job.status = "complete"
        job.progress = 100
        db.commit()
        
        logger.info(f"Completed processing job {job_id}")
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        job = db.query(models.VideoProcessingJob).filter_by(id=job_id).first()
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        
    finally:
        db.close() 
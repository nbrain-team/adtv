#!/usr/bin/env python3
"""Test the ad-traffic posts endpoint to diagnose issues"""
import os
import sys
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from core.database import SessionLocal
from ad_traffic import models, schemas, services

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_posts_endpoint():
    """Test fetching posts for a client"""
    db = SessionLocal()
    
    try:
        # Find a client with posts
        client = db.query(models.AdTrafficClient).first()
        if not client:
            logger.info("No clients found")
            return
            
        logger.info(f"Testing with client: {client.id} - {client.name}")
        
        # Get posts using the service function
        posts = services.get_client_posts(db, client.id)
        logger.info(f"Found {len(posts)} posts")
        
        # Try to serialize each post
        for i, post in enumerate(posts):
            logger.info(f"\nPost {i+1}:")
            logger.info(f"  ID: {post.id}")
            logger.info(f"  Platforms: {post.platforms} (type: {type(post.platforms)})")
            logger.info(f"  Media URLs: {post.media_urls} (type: {type(post.media_urls)})")
            logger.info(f"  Status: {post.status}")
            
            # Try to convert to schema
            try:
                post_dict = {
                    "id": post.id,
                    "client_id": post.client_id,
                    "campaign_id": post.campaign_id,
                    "content": post.content,
                    "platforms": post.platforms,
                    "scheduled_time": post.scheduled_time,
                    "status": post.status,
                    "published_time": post.published_time,
                    "platform_post_ids": post.platform_post_ids or {},
                    "media_urls": post.media_urls or [],
                    "approved_by": post.approved_by,
                    "approved_at": post.approved_at,
                    "metrics": post.metrics or {},
                    "budget_spent": post.budget_spent or 0.0,
                    "created_at": post.created_at,
                    "updated_at": post.updated_at,
                }
                
                # Validate with schema
                validated = schemas.SocialPost(**post_dict)
                logger.info("  ✓ Successfully validated with schema")
                
            except Exception as e:
                logger.error(f"  ✗ Schema validation failed: {e}")
                logger.error(f"    Error type: {type(e).__name__}")
                
    except Exception as e:
        logger.error(f"Error testing posts: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    test_posts_endpoint() 
"""
Improved batch saving for the realtor scraper
"""

# Reduced batch size for more frequent saves
BATCH_SIZE = 20  # Reduced from 50

def save_batch_immediately(session, job_id, batch):
    """
    Save a batch of contacts immediately without waiting for full batch
    """
    from core.database import RealtorContact
    import logging
    
    logger = logging.getLogger(__name__)
    
    if not batch:
        return
        
    logger.info(f"Saving batch of {len(batch)} contacts immediately...")
    
    try:
        for profile in batch:
            contact = RealtorContact(
                job_id=job_id,
                first_name=profile.get('first_name', ''),
                last_name=profile.get('last_name', ''),
                company=profile.get('company', ''),
                city=profile.get('city', ''),
                state=profile.get('state', ''),
                dma=profile.get('dma', ''),
                cell_phone=profile.get('cell_phone', ''),
                phone2=profile.get('phone2', ''),
                email=profile.get('email', ''),
                personal_email=profile.get('personal_email', ''),
                agent_website=profile.get('agent_website', ''),
                facebook_profile=profile.get('facebook_profile', ''),
                fb_or_website=profile.get('fb_or_website', ''),
                years_exp=profile.get('years_exp'),
                seller_deals_total_deals=profile.get('seller_deals_total_deals'),
                seller_deals_total_value=profile.get('seller_deals_total_value'),
                seller_deals_avg_price=profile.get('seller_deals_avg_price'),
                buyer_deals_total_deals=profile.get('buyer_deals_total_deals'),
                buyer_deals_total_value=profile.get('buyer_deals_total_value'),
                buyer_deals_avg_price=profile.get('buyer_deals_avg_price'),
                profile_url=profile.get('profile_url', ''),
                source=profile.get('source', 'realtor.com')
            )
            session.add(contact)
        
        # Commit immediately
        session.commit()
        logger.info(f"✅ Successfully saved {len(batch)} contacts")
        
        # Update job timestamp to show activity
        from sqlalchemy import text
        session.execute(text("""
            UPDATE scraping_jobs 
            SET updated_at = NOW() 
            WHERE id = :job_id
        """), {"job_id": job_id})
        session.commit()
        
    except Exception as e:
        logger.error(f"Error saving batch: {e}")
        session.rollback()
        raise 
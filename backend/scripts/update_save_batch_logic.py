#!/usr/bin/env python3
"""
Update the save_batch function to handle profile updates properly
"""
import os

def create_improved_save_batch():
    """Create an improved save_batch function that updates existing profiles"""
    
    improved_code = '''def save_batch(session: Session, job_id: str, batch: List[Dict[str, Any]]):
    """Save a batch of scraped data - creates new or updates existing profiles"""
    logger.info(f"\\n{'='*50}")
    logger.info(f"SAVING BATCH: {len(batch)} profiles")
    logger.info(f"Job ID: {job_id}")
    logger.info(f"{'='*50}")
    
    saved_count = 0
    updated_count = 0
    
    for i, data in enumerate(batch):
        try:
            # Ensure profile_url exists (it's required)
            profile_url = data.get('profile_url')
            if not profile_url:
                logger.warning(f"  WARNING: Skipping profile without profile_url: {data}")
                continue
            
            # Log the data being saved for debugging
            logger.info(f"  Profile {i+1}: {data.get('first_name', 'Unknown')} {data.get('last_name', 'Unknown')} - {profile_url}")
            
            # Check if profile already exists (from URL save phase)
            existing_contact = session.query(RealtorContact).filter_by(
                job_id=job_id,
                profile_url=profile_url
            ).first()
            
            if existing_contact:
                # Update existing profile with full data
                logger.info(f"    Updating existing profile...")
                for key, value in data.items():
                    if value is not None and value != 'Pending':  # Don't overwrite with placeholder values
                        setattr(existing_contact, key, value)
                updated_count += 1
            else:
                # Create new profile
                logger.info(f"    Creating new profile...")
                contact = RealtorContact(
                    job_id=job_id,
                    **data
                )
                session.add(contact)
                saved_count += 1
                
        except Exception as e:
            logger.error(f"  ERROR saving profile {i+1}: {str(e)}")
            logger.error(f"  Data: {data}")
            # Continue with other profiles instead of failing the whole batch
            continue
    
    try:
        session.commit()
        logger.info(f"✓ Batch processed successfully:")
        logger.info(f"  - New profiles: {saved_count}")
        logger.info(f"  - Updated profiles: {updated_count}")
        
        # Get total count for this job
        total_count = session.query(RealtorContact).filter_by(job_id=job_id).count()
        logger.info(f"Total profiles saved for this job: {total_count}")
        
        # Update job's updated_at to show activity
        job = session.query(ScrapingJob).filter_by(id=job_id).first()
        if job:
            job.updated_at = datetime.utcnow()
            session.commit()
            
    except Exception as e:
        logger.error(f"ERROR committing batch: {str(e)}")
        session.rollback()
        raise
'''
    
    print("Improved save_batch function created!")
    print("\nThis function will:")
    print("1. Check if a profile already exists (by URL)")
    print("2. Update existing profiles with new data")
    print("3. Create new profiles only if they don't exist")
    print("4. Skip placeholder values like 'Pending'")
    
    # Save to a file for reference
    with open('improved_save_batch.py', 'w') as f:
        f.write(improved_code)
    
    print("\nSaved to: improved_save_batch.py")

if __name__ == "__main__":
    create_improved_save_batch() 
#!/usr/bin/env python3
"""
Add contact enricher tables to the database
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_contact_enricher_tables():
    """Add tables for contact enricher module"""
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Create enrichment_projects table
            logger.info("Creating enrichment_projects table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS enrichment_projects (
                    id VARCHAR PRIMARY KEY,
                    user_id VARCHAR NOT NULL REFERENCES users(id),
                    name VARCHAR NOT NULL,
                    description TEXT,
                    original_filename VARCHAR,
                    original_row_count INTEGER DEFAULT 0,
                    status VARCHAR DEFAULT 'pending',
                    processed_rows INTEGER DEFAULT 0,
                    enriched_rows INTEGER DEFAULT 0,
                    emails_found INTEGER DEFAULT 0,
                    phones_found INTEGER DEFAULT 0,
                    facebook_data_found INTEGER DEFAULT 0,
                    websites_scraped INTEGER DEFAULT 0,
                    config JSON DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """))
            
            # Create enriched_contacts table
            logger.info("Creating enriched_contacts table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS enriched_contacts (
                    id VARCHAR PRIMARY KEY,
                    project_id VARCHAR NOT NULL REFERENCES enrichment_projects(id) ON DELETE CASCADE,
                    original_data JSON,
                    name VARCHAR,
                    company VARCHAR,
                    city VARCHAR,
                    state VARCHAR,
                    agent_website VARCHAR,
                    facebook_profile VARCHAR,
                    
                    -- Enriched email data
                    email_found VARCHAR,
                    email_confidence FLOAT DEFAULT 0.0,
                    email_source VARCHAR,
                    email_valid BOOLEAN,
                    email_validation_details JSON,
                    
                    -- Enriched phone data
                    phone_found VARCHAR,
                    phone_confidence FLOAT DEFAULT 0.0,
                    phone_source VARCHAR,
                    phone_formatted VARCHAR,
                    
                    -- Facebook data
                    facebook_followers INTEGER,
                    facebook_recent_post TEXT,
                    facebook_post_date TIMESTAMP,
                    facebook_engagement JSON,
                    facebook_page_info JSON,
                    facebook_last_checked TIMESTAMP,
                    
                    -- Website scraping data
                    website_emails JSON DEFAULT '[]',
                    website_phones JSON DEFAULT '[]',
                    website_social_links JSON DEFAULT '{}',
                    website_scraped BOOLEAN DEFAULT FALSE,
                    website_scrape_date TIMESTAMP,
                    
                    -- Quality metrics
                    data_completeness_score FLOAT DEFAULT 0.0,
                    confidence_score FLOAT DEFAULT 0.0,
                    
                    -- Processing metadata
                    enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    errors JSON DEFAULT '[]'
                )
            """))
            
            # Create enrichment_api_configs table
            logger.info("Creating enrichment_api_configs table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS enrichment_api_configs (
                    id VARCHAR PRIMARY KEY,
                    user_id VARCHAR NOT NULL REFERENCES users(id),
                    
                    -- Google SERP API
                    serp_api_key VARCHAR,
                    serp_api_endpoint VARCHAR DEFAULT 'https://serpapi.com/search',
                    serp_daily_limit INTEGER DEFAULT 100,
                    serp_used_today INTEGER DEFAULT 0,
                    
                    -- Facebook API
                    facebook_app_id VARCHAR,
                    facebook_app_secret VARCHAR,
                    facebook_access_token TEXT,
                    facebook_token_expires TIMESTAMP,
                    
                    -- Rate limiting
                    last_reset_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes
            logger.info("Creating indexes...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_enrichment_projects_user_id ON enrichment_projects(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_enriched_contacts_project_id ON enriched_contacts(project_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_enriched_contacts_email ON enriched_contacts(email_found)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_enriched_contacts_phone ON enriched_contacts(phone_found)"))
            
            trans.commit()
            logger.info("✅ Contact enricher tables created successfully!")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"❌ Error creating contact enricher tables: {e}")
            raise


if __name__ == "__main__":
    add_contact_enricher_tables() 
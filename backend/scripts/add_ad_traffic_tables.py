"""
Migration script to add ad traffic tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import inspect
from core.database import engine, Base
from ad_traffic.models import AdTrafficClient, Campaign, VideoClip, SocialPost
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_ad_traffic_tables():
    """Add the Ad Traffic module tables to the database"""
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    tables_to_create = [
        AdTrafficClient.__table__,
        Campaign.__table__,
        VideoClip.__table__,
        SocialPost.__table__
    ]
    
    for table in tables_to_create:
        if table.name not in existing_tables:
            logger.info(f"Creating table: {table.name}")
            try:
                table.create(bind=engine)
                logger.info(f"Successfully created table: {table.name}")
            except Exception as e:
                logger.error(f"Error creating table {table.name}: {e}")
        else:
            logger.info(f"Table {table.name} already exists")

if __name__ == "__main__":
    add_ad_traffic_tables()
    logger.info("Ad Traffic tables migration completed") 
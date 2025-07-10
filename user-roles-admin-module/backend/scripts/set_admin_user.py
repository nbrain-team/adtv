#!/usr/bin/env python3
"""
Script to manually set danny@nbrain.ai as admin with all permissions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_admin_user():
    """Set danny@nbrain.ai as admin with all permissions"""
    
    with SessionLocal() as db:
        try:
            # Check if user exists
            result = db.execute(text("SELECT id, email, role FROM users WHERE email = 'danny@nbrain.ai'"))
            user = result.fetchone()
            
            if not user:
                logger.error("User danny@nbrain.ai not found!")
                return
            
            logger.info(f"Found user: {user[1]} with current role: {user[2]}")
            
            # Update to admin with all permissions
            db.execute(text("""
                UPDATE users 
                SET role = 'admin',
                    permissions = '{"chat": true, "history": true, "knowledge": true, "agents": true, "data-lake": true, "user-management": true}'::json
                WHERE email = 'danny@nbrain.ai'
            """))
            
            db.commit()
            logger.info("Successfully updated danny@nbrain.ai to admin with all permissions!")
            
            # Verify the update
            result = db.execute(text("SELECT role, permissions FROM users WHERE email = 'danny@nbrain.ai'"))
            updated_user = result.fetchone()
            logger.info(f"Verified - Role: {updated_user[0]}, Permissions: {updated_user[1]}")
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            db.rollback()
            raise

if __name__ == "__main__":
    logger.info("Setting admin user...")
    set_admin_user()
    logger.info("Done!") 
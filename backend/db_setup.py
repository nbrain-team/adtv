import logging
from sqlalchemy import inspect, text
from core.database import Base, engine, SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_db_schema(db):
    logger.info("Checking for 'is_active' column in 'users' table...")
    inspector = inspect(db.get_bind())
    try:
        users_columns = [c['name'] for c in inspector.get_columns('users')]
        if 'is_active' not in users_columns:
            logger.info("Adding 'is_active' column to 'users' table.")
            db.execute(text('ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE'))
            logger.info("Successfully added 'is_active' column.")
    except Exception as e:
        logger.info(f"Could not check 'users' table, likely doesn't exist yet. Details: {e}")

def migrate_data(db):
    logger.info("Checking for legacy 'chat_conversations' table...")
    inspector = inspect(db.get_bind())
    if not inspector.has_table("chat_conversations"):
        logger.info("Legacy table not found. Skipping migration.")
        return
    
    try:
        count_result = db.execute(text("SELECT COUNT(*) FROM chat_conversations")).scalar_one_or_none()
        if count_result == 0:
            logger.info("Legacy table is empty. Dropping it.")
            db.execute(text('DROP TABLE chat_conversations'))
            return

        logger.info(f"Found {count_result} records in legacy table. Attempting migration.")
        cols = [c['name'] for c in inspector.get_columns('chat_conversations')]
        if 'user_id' not in cols:
            logger.warning("Legacy table is pre-authentication. Renaming to '_pre_auth'.")
            db.execute(text('ALTER TABLE chat_conversations RENAME TO chat_conversations_pre_auth'))
        else:
            logger.info("Migrating data to new 'chat_sessions' table.")
            db.execute(text("""
                INSERT INTO chat_sessions (id, title, created_at, messages, user_id)
                SELECT id, title, created_at, messages, user_id FROM chat_conversations
                ON CONFLICT (id) DO NOTHING
            """))
            logger.info("Migration successful. Renaming old table to '_migrated'.")
            db.execute(text('ALTER TABLE chat_conversations RENAME TO chat_conversations_migrated'))
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise

def main():
    logger.info("--- Starting Database Setup ---")
    db = SessionLocal()
    try:
        logger.info("1. Creating all tables from metadata...")
        Base.metadata.create_all(bind=engine)
        logger.info("   ...tables created successfully.")

        logger.info("2. Applying schema updates...")
        update_db_schema(db)
        logger.info("   ...schema updates applied.")
        
        logger.info("3. Running data migration...")
        migrate_data(db)
        logger.info("   ...data migration complete.")

        db.commit()
        logger.info("--- Database setup finished successfully! ---")
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main() 
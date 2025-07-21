#!/usr/bin/env python3
"""Add personalizer_projects table"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine, SessionLocal

def add_personalizer_projects_table():
    """Create the personalizer_projects table"""
    with engine.connect() as conn:
        try:
            # Create the table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS personalizer_projects (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    user_id VARCHAR NOT NULL REFERENCES users(id),
                    template_used TEXT,
                    generation_goal TEXT,
                    csv_headers JSON,
                    row_count INTEGER,
                    original_csv_url VARCHAR,
                    generated_csv_url VARCHAR,
                    status VARCHAR DEFAULT 'completed',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            conn.commit()
            print("✅ Successfully created personalizer_projects table!")
        except Exception as e:
            print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    add_personalizer_projects_table() 
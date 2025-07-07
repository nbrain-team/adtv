#!/usr/bin/env python3
"""
Script to fix admin permissions for danny@nbrain.ai
This script connects directly to the database and ensures proper JSON formatting
"""

import os
import psycopg2
import json
from urllib.parse import urlparse

# Get database URL from environment or use the production URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://adtv_user:1OsPV3CLzqLfgBR8G39Rd2qsGXx6y18R@dpg-cqt5c6ogph6c73fl5nr0-a.oregon-postgres.render.com/adtv")

# Parse the database URL
result = urlparse(DATABASE_URL)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

# Connect to the database
print(f"Connecting to database at {hostname}...")
conn = psycopg2.connect(
    database=database,
    user=username,
    password=password,
    host=hostname,
    port=port,
    sslmode='require'  # Add SSL mode for Render
)

cur = conn.cursor()

try:
    # First, check the current state
    cur.execute("SELECT id, email, role, permissions FROM users WHERE email = 'danny@nbrain.ai'")
    user = cur.fetchone()
    
    if not user:
        print("User danny@nbrain.ai not found!")
    else:
        print(f"Found user: {user[1]}")
        print(f"Current role: {user[2]}")
        print(f"Current permissions: {user[3]}")
        
        # Update to admin with all permissions
        all_permissions = {
            "chat": True,
            "history": True,
            "knowledge": True,
            "agents": True,
            "data-lake": True,
            "user-management": True
        }
        
        cur.execute("""
            UPDATE users 
            SET role = 'admin',
                permissions = %s
            WHERE email = 'danny@nbrain.ai'
        """, (json.dumps(all_permissions),))
        
        conn.commit()
        print("Successfully updated user to admin with all permissions!")
        
        # Verify the update
        cur.execute("SELECT role, permissions FROM users WHERE email = 'danny@nbrain.ai'")
        updated_user = cur.fetchone()
        print(f"New role: {updated_user[0]}")
        print(f"New permissions: {updated_user[1]}")
        
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()

print("Done!") 
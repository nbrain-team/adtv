#!/usr/bin/env python3
"""Fix foreign key constraint mismatch - campaigns should reference ad_traffic_clients, not clients"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def fix_foreign_key_constraints():
    """Fix foreign key constraints that reference wrong tables"""
    
    with engine.connect() as conn:
        print("=== FIXING FOREIGN KEY CONSTRAINTS ===\n")
        
        # 1. Drop the incorrect foreign key constraint
        print("1. Dropping incorrect foreign key constraint on campaigns table...")
        try:
            with engine.begin() as trans_conn:
                # First, check if the constraint exists
                result = trans_conn.execute(text("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'campaigns' 
                    AND constraint_type = 'FOREIGN KEY'
                    AND constraint_name = 'campaigns_client_id_fkey'
                """))
                
                if result.rowcount > 0:
                    trans_conn.execute(text("""
                        ALTER TABLE campaigns 
                        DROP CONSTRAINT campaigns_client_id_fkey
                    """))
                    print("✅ Dropped incorrect constraint")
                else:
                    print("✅ Constraint already removed")
        except Exception as e:
            print(f"⚠️  Could not drop constraint: {e}")
        
        # 2. Add the correct foreign key constraint
        print("\n2. Adding correct foreign key constraint...")
        try:
            with engine.begin() as trans_conn:
                # Check if campaigns table references ad_traffic_clients
                result = trans_conn.execute(text("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'campaigns' 
                    AND constraint_type = 'FOREIGN KEY'
                    AND constraint_name LIKE '%client%'
                """))
                
                has_correct_fk = False
                for row in result:
                    # Check if this constraint references ad_traffic_clients
                    detail_result = trans_conn.execute(text("""
                        SELECT referenced_table_name 
                        FROM information_schema.key_column_usage 
                        WHERE constraint_name = :constraint_name
                        AND table_name = 'campaigns'
                    """), {"constraint_name": row[0]})
                    
                    for detail in detail_result:
                        if detail[0] == 'ad_traffic_clients':
                            has_correct_fk = True
                            print(f"✅ Found correct foreign key: {row[0]}")
                            break
                
                if not has_correct_fk:
                    trans_conn.execute(text("""
                        ALTER TABLE campaigns 
                        ADD CONSTRAINT campaigns_client_id_ad_traffic_fkey 
                        FOREIGN KEY (client_id) REFERENCES ad_traffic_clients(id)
                    """))
                    print("✅ Added correct foreign key constraint")
        except Exception as e:
            print(f"⚠️  Could not add correct constraint: {e}")
        
        # 3. Fix social_posts foreign key as well
        print("\n3. Fixing social_posts foreign key constraints...")
        try:
            with engine.begin() as trans_conn:
                # Drop incorrect constraint if exists
                result = trans_conn.execute(text("""
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'social_posts' 
                    AND constraint_type = 'FOREIGN KEY'
                    AND constraint_name = 'social_posts_client_id_fkey'
                """))
                
                if result.rowcount > 0:
                    trans_conn.execute(text("""
                        ALTER TABLE social_posts 
                        DROP CONSTRAINT social_posts_client_id_fkey
                    """))
                    print("✅ Dropped incorrect social_posts constraint")
                
                # Add correct constraint
                trans_conn.execute(text("""
                    ALTER TABLE social_posts 
                    ADD CONSTRAINT social_posts_client_id_ad_traffic_fkey 
                    FOREIGN KEY (client_id) REFERENCES ad_traffic_clients(id)
                """))
                print("✅ Added correct social_posts foreign key")
        except Exception as e:
            print(f"⚠️  Social posts constraint issue: {e}")
        
        # 4. Check if the client exists in ad_traffic_clients
        print("\n4. Checking for the client in ad_traffic_clients...")
        result = conn.execute(text("""
            SELECT id, name FROM ad_traffic_clients 
            WHERE id = '5e1bc9aa-a1e3-4c91-85bd-679ddf871867'
        """))
        
        if result.rowcount == 0:
            print("❌ Client 5e1bc9aa-a1e3-4c91-85bd-679ddf871867 does NOT exist in ad_traffic_clients!")
            print("   You need to create a new client in the Ad Traffic module.")
        else:
            for row in result:
                print(f"✅ Found client: {row[1]} (ID: {row[0]})")
        
        # 5. List all existing clients
        print("\n5. Existing clients in ad_traffic_clients:")
        result = conn.execute(text("""
            SELECT id, name, created_at FROM ad_traffic_clients 
            ORDER BY created_at DESC
            LIMIT 10
        """))
        
        if result.rowcount == 0:
            print("   No clients found. You need to create a client first!")
        else:
            for row in result:
                print(f"   - {row[1]} (ID: {row[0]}, Created: {row[2]})")
        
        print("\n✅ Foreign key fix completed!")
        print("\nIMPORTANT: If you're still seeing errors, make sure to:")
        print("1. Create a new client in the Ad Traffic module")
        print("2. Use that client's ID when creating campaigns")

if __name__ == "__main__":
    try:
        fix_foreign_key_constraints()
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 
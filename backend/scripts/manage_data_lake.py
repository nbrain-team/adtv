#!/usr/bin/env python3
"""
Script to manage Data Lake data - clear all records or import from CSV
Usage:
    python manage_data_lake.py --clear
    python manage_data_lake.py --import path/to/file.csv
"""

import os
import sys
import csv
import argparse
from datetime import datetime
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base
from core.data_lake_models import DataLakeRecord

# Get database URL from environment or use default
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/adtv')

def clear_all_records():
    """Delete all records from data_lake_records table"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        count = session.query(DataLakeRecord).count()
        if count == 0:
            print("No records to delete.")
            return
            
        confirm = input(f"Are you sure you want to delete {count} records? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
            
        session.query(DataLakeRecord).delete()
        session.commit()
        print(f"Successfully deleted {count} records.")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

def import_csv(file_path, batch_size=1000):
    """Import CSV file in batches with smart record matching"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get the highest existing unique_id
        max_unique_id = session.query(func.max(DataLakeRecord.unique_id)).scalar() or 0
        next_unique_id = max_unique_id + 1
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch_new = []
            batch_update = []
            total_imported = 0
            total_updated = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Map your CSV columns to database fields
                    # This is a template - adjust field names to match your CSV
                    record_data = {
                        'first_name': row.get('First Name', '').strip(),
                        'last_name': row.get('Last Name', '').strip(),
                        'phone': row.get('Phone', '').strip(),
                        'email': row.get('Email', '').strip(),
                        'company': row.get('Company', '').strip(),
                        'city': row.get('City', '').strip(),
                        'lead_source': row.get('Lead Source', '').strip(),
                        'tier': int(row.get('Tier')) if row.get('Tier') and row.get('Tier').strip() else None,
                        # Add more field mappings as needed
                    }
                    
                    # Extract key fields for matching
                    first_name = record_data.get('first_name', '').lower()
                    last_name = record_data.get('last_name', '').lower()
                    phone = record_data.get('phone', '')
                    
                    # Try to find existing record
                    existing_record = None
                    if first_name and last_name and phone:
                        existing_record = session.query(DataLakeRecord).filter(
                            func.lower(DataLakeRecord.first_name) == first_name,
                            func.lower(DataLakeRecord.last_name) == last_name,
                            DataLakeRecord.phone == phone
                        ).first()
                    
                    if existing_record:
                        # Update existing record
                        for field, new_value in record_data.items():
                            if field == 'unique_id':
                                continue
                            
                            current_value = getattr(existing_record, field, None)
                            
                            # Update logic: overwrite if current has value, append if current is empty
                            if new_value is not None:
                                if current_value:
                                    # Overwrite existing data
                                    setattr(existing_record, field, new_value)
                                else:
                                    # Append to empty field
                                    setattr(existing_record, field, new_value)
                        
                        existing_record.updated_at = datetime.utcnow()
                        batch_update.append(existing_record)
                    else:
                        # Create new record with auto-generated unique_id
                        if 'unique_id' not in record_data or not record_data.get('unique_id'):
                            record_data['unique_id'] = next_unique_id
                            next_unique_id += 1
                        
                        new_record = DataLakeRecord(**record_data)
                        batch_new.append(new_record)
                    
                    # Commit batches
                    if len(batch_new) >= batch_size:
                        session.bulk_save_objects(batch_new)
                        session.commit()
                        total_imported += len(batch_new)
                        print(f"Imported {total_imported} new records...")
                        batch_new = []
                    
                    if len(batch_update) >= batch_size:
                        session.commit()
                        total_updated += len(batch_update)
                        print(f"Updated {total_updated} existing records...")
                        batch_update = []
                        
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            # Commit remaining records
            if batch_new:
                session.bulk_save_objects(batch_new)
                session.commit()
                total_imported += len(batch_new)
            
            if batch_update:
                session.commit()
                total_updated += len(batch_update)
            
            print(f"\nImport complete!")
            print(f"New records imported: {total_imported}")
            print(f"Existing records updated: {total_updated}")
            print(f"Total processed: {total_imported + total_updated}")
            print(f"Errors: {len(errors)}")
            if errors:
                print("\nFirst 10 errors:")
                for error in errors[:10]:
                    print(f"  {error}")
                    
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

def main():
    parser = argparse.ArgumentParser(description='Manage Data Lake data')
    parser.add_argument('--clear', action='store_true', help='Clear all records')
    parser.add_argument('--import', dest='import_file', help='Import CSV file')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for import (default: 1000)')
    
    args = parser.parse_args()
    
    if args.clear:
        clear_all_records()
    elif args.import_file:
        if not os.path.exists(args.import_file):
            print(f"Error: File '{args.import_file}' not found")
            sys.exit(1)
        import_csv(args.import_file, args.batch_size)
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 
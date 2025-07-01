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
from sqlalchemy import create_engine
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
    """Import CSV file in batches"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            total_imported = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Create record (add your field mapping logic here)
                    record = DataLakeRecord(
                        # Map your CSV columns to database fields
                        # Example:
                        # unique_id=int(row.get('Unique ID', 0)) if row.get('Unique ID') else None,
                        # first_name=row.get('First Name', '').strip(),
                        # last_name=row.get('Last Name', '').strip(),
                        # Add all your field mappings here
                    )
                    batch.append(record)
                    
                    # Commit batch
                    if len(batch) >= batch_size:
                        session.bulk_save_objects(batch)
                        session.commit()
                        total_imported += len(batch)
                        print(f"Imported {total_imported} records...")
                        batch = []
                        
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            # Commit remaining records
            if batch:
                session.bulk_save_objects(batch)
                session.commit()
                total_imported += len(batch)
            
            print(f"\nImport complete!")
            print(f"Total imported: {total_imported}")
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
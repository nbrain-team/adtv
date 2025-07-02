#!/usr/bin/env python3
"""
Script to import MasterProspects.csv with unique IDs starting from 100001
"""

import os
import sys
import csv
import argparse
from datetime import datetime
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import re

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Base
from core.data_lake_models import DataLakeRecord

# Get database URL from environment or use default
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/adtv')

def clean_phone(phone_str):
    """Clean phone number to match format 000-000-0000"""
    if not phone_str:
        return None
    
    # Remove all non-digits
    digits = re.sub(r'\D', '', phone_str)
    
    # If we have 10 digits, format them
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    
    return None  # Invalid phone number

def import_master_prospects(file_path, batch_size=1000):
    """Import MasterProspects.csv with unique IDs starting from 100001"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Starting unique ID
        next_unique_id = 100001
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            batch = []
            total_imported = 0
            total_updated = 0
            total_errors = 0
            
            print(f"Starting import from {file_path}...")
            print(f"Unique IDs will start from {next_unique_id}")
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Map CSV columns to database fields
                    record_data = {
                        'unique_id': next_unique_id,
                        'speaker_source': row.get('Speaker/Source', '').strip() if row.get('Speaker/Source') else None,
                        'profession': row.get('Profession', '').strip() if row.get('Profession') else None,
                        'city': row.get('City', '').strip() if row.get('City') else None,
                        'state_spelled_out': row.get('State', '').strip() if row.get('State') else None,
                        'first_name': row.get('First Name', '').strip() if row.get('First Name') else None,
                        'last_name': row.get('Last Name', '').strip() if row.get('Last Name') else None,
                        'company': row.get('Company', '').strip() if row.get('Company') else None,
                        'phone': clean_phone(row.get('Phone', '')),
                        'email': row.get('Email Address', '').strip() if row.get('Email Address') else None,
                    }
                    
                    # Convert state name to initials if needed
                    state_map = {
                        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
                        'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
                        'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
                        'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
                        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
                        'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
                        'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
                        'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
                        'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
                        'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
                    }
                    
                    # If state is already 2 letters, use it as initials
                    state = record_data.get('state_spelled_out', '')
                    if state and len(state) == 2:
                        record_data['state_initials'] = state.upper()
                    elif state in state_map:
                        record_data['state_initials'] = state_map[state]
                    
                    # Handle numeric fields
                    for field in ['1YR Total Sales $', '1YR Total Transactions #', 'Lender 1YR Volume $', 
                                  'Lender 1YR Closed Loans #', 'Years Experience']:
                        value = row.get(field, '').strip()
                        if value:
                            # Remove $ and commas, convert to appropriate type
                            value = value.replace('$', '').replace(',', '')
                            if field == '1YR Total Sales $':
                                record_data['one_yr_total_sales_usd'] = float(value)
                            elif field == '1YR Total Transactions #':
                                record_data['one_yr_total_transactions_count'] = int(value)
                            elif field == 'Lender 1YR Volume $':
                                record_data['lender_one_yr_volume_usd'] = float(value)
                            elif field == 'Lender 1YR Closed Loans #':
                                record_data['lender_one_yr_closed_loans_count'] = int(value)
                            elif field == 'Years Experience':
                                record_data['years_experience'] = int(value)
                    
                    # Handle Lender type
                    lender_type = row.get('Lender- Banker or Broker', '').strip()
                    if lender_type:
                        record_data['lender_banker_or_broker'] = lender_type
                    
                    # Check for existing record by first_name + last_name + phone
                    first_name = record_data.get('first_name', '').lower() if record_data.get('first_name') else ''
                    last_name = record_data.get('last_name', '').lower() if record_data.get('last_name') else ''
                    phone = record_data.get('phone', '')
                    
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
                                continue  # Don't update unique_id
                            
                            current_value = getattr(existing_record, field, None)
                            
                            # Update logic: overwrite if new value exists
                            if new_value is not None:
                                setattr(existing_record, field, new_value)
                        
                        existing_record.updated_at = datetime.utcnow()
                        total_updated += 1
                    else:
                        # Create new record
                        new_record = DataLakeRecord(**record_data)
                        batch.append(new_record)
                        total_imported += 1
                        next_unique_id += 1
                    
                    # Commit batch when it reaches batch_size
                    if len(batch) >= batch_size:
                        session.add_all(batch)
                        session.commit()
                        print(f"Imported {total_imported} new records, updated {total_updated} existing records...")
                        batch = []
                        
                except Exception as e:
                    total_errors += 1
                    print(f"Error on row {row_num}: {str(e)}")
                    continue
            
            # Commit remaining records
            if batch:
                session.add_all(batch)
                session.commit()
            
            print(f"\nImport complete!")
            print(f"Total new records imported: {total_imported}")
            print(f"Total existing records updated: {total_updated}")
            print(f"Total errors: {total_errors}")
            
    except Exception as e:
        session.rollback()
        print(f"Error during import: {e}")
        raise
    finally:
        session.close()

def main():
    parser = argparse.ArgumentParser(description='Import MasterProspects.csv')
    parser.add_argument('--file', default='/Users/dannydemichele/Adstv/data lake/MasterProspects.csv', 
                        help='Path to MasterProspects.csv file')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for import (default: 1000)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    import_master_prospects(args.file, args.batch_size)

if __name__ == "__main__":
    main() 
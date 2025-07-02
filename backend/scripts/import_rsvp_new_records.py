#!/usr/bin/env python3
"""
Script to import new RSVP records directly without matching
"""

import os
import sys
import csv
import json
import requests
import argparse
from time import sleep
import re
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API configuration
API_BASE_URL = "https://adtv-backend.onrender.com"

def clean_phone(phone_str):
    """Clean phone number to match format 000-000-0000"""
    if not phone_str:
        return None
    
    # Remove all non-digits
    digits = re.sub(r'\D', '', str(phone_str))
    
    # If we have 10 digits, format them
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    
    return None  # Invalid phone number

def login(username, password):
    """Login and get access token"""
    print("Logging in to API...")
    response = requests.post(
        f"{API_BASE_URL}/login",
        data={"username": username, "password": password}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("Login successful!")
        return token
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        sys.exit(1)

def get_next_unique_id(token):
    """Get the next available unique ID"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get the highest unique_id
    params = {
        "skip": 0,
        "limit": 1,
        "columns": "unique_id"
    }
    
    response = requests.get(
        f"{API_BASE_URL}/data-lake/records",
        headers=headers,
        params=params
    )
    
    if response.status_code == 200:
        data = response.json()
        total = data.get("total", 0)
        
        # For simplicity, use total + 200000 to ensure we're beyond existing IDs
        return 200001 + total
    else:
        # Default starting point if we can't determine
        return 200001

def create_batch(token, batch_records):
    """Create multiple records via CSV import API"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create CSV content from batch
    import io
    csv_buffer = io.StringIO()
    
    if batch_records:
        # Get all unique fieldnames across all records
        all_fields = set()
        for record in batch_records:
            all_fields.update(record.keys())
        fieldnames = sorted(list(all_fields))
        
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in batch_records:
            writer.writerow(record)
    
    # Convert to bytes
    csv_content = csv_buffer.getvalue().encode('utf-8')
    csv_buffer.close()
    
    # Column mapping for import
    column_mapping = {
        'unique_id': 'unique_id',
        'first_name': 'first_name',
        'last_name': 'last_name',
        'phone': 'phone',
        'email': 'email',
        'city': 'city',
        'company': 'company',
        'profession': 'profession',
        'appointment_set_date': 'appointment_set_date',
        'b2b_call_center_vsa': 'b2b_call_center_vsa',
        'interest_level': 'interest_level',
        'attendance': 'attendance',
        'account_manager_notes': 'account_manager_notes',
        'craigs_notes': 'craigs_notes',
        'dma_market': 'dma_market',
        'start_date': 'start_date',
        'hotel_name': 'hotel_name',
        'hotel_street_address': 'hotel_street_address',
        'hotel_city': 'hotel_city',
        'hotel_state': 'hotel_state',
        'hotel_zip': 'hotel_zip',
        'hotel_meeting_room_name': 'hotel_meeting_room_name'
    }
    
    # Send to API
    files = {'file': ('batch.csv', csv_content, 'text/csv')}
    params = {'mapping': json.dumps(column_mapping)}
    
    response = requests.post(
        f"{API_BASE_URL}/data-lake/import-csv",
        headers=headers,
        files=files,
        params=params
    )
    
    return response

def import_rsvp_new_records(file_path, username, password, batch_size=100):
    """Import new RSVP records"""
    # Login
    token = login(username, password)
    
    # Get next unique ID for new records
    next_unique_id = get_next_unique_id(token)
    
    # Track statistics
    stats = {
        'total': 0,
        'imported': 0,
        'errors': 0
    }
    
    print(f"\nProcessing new RSVP records from: {file_path}")
    print("="*50)
    
    batch_records = []
    batch_num = 0
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, start=2):
            stats['total'] += 1
            
            # Extract key fields
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()
            phone = row.get('Phone', '').strip()
            
            if not first_name or not last_name:
                print(f"Row {row_num}: Skipping - missing name")
                stats['errors'] += 1
                continue
            
            # Create record data
            record_data = {
                'unique_id': next_unique_id,
                'first_name': first_name,
                'last_name': last_name,
                'phone': clean_phone(phone) if phone else None,
                'email': row.get('Email', '').strip() or None,
                'city': row.get('City', '').strip() or None,
                'company': row.get('Company', '').strip() or None,
                'profession': row.get('Profession', '').strip() or None,
            }
            
            # Process date fields
            for csv_field, db_field in [('Appointment Set Date', 'appointment_set_date'), 
                                       ('Start Date', 'start_date')]:
                date_value = row.get(csv_field, '').strip()
                if date_value:
                    try:
                        # Parse M/D/YYYY format
                        date_obj = datetime.strptime(date_value, '%m/%d/%Y')
                        record_data[db_field] = date_obj.isoformat()
                    except ValueError:
                        pass
            
            # Other RSVP fields
            if row.get('B2B Call Center (VSA)', '').strip():
                record_data['b2b_call_center_vsa'] = True
            
            for field in ['Interest Level', 'Attendance', 'Account Manager Notes', 
                         "Craig's Notes", 'Hotel Name', 'Hotel Street Address',
                         'Hotel City', 'Hotel State', 'Hotel Zip', 'Hotel Meeting Room Name']:
                value = row.get(field, '').strip()
                if value:
                    db_field = field.lower().replace(' ', '_').replace("'s", "s")
                    record_data[db_field] = value
            
            # Handle DMA
            dma = row.get('DMA', '').strip()
            if dma:
                if dma.startswith('#'):
                    dma = dma[1:]
                record_data['dma_market'] = dma
            
            batch_records.append(record_data)
            next_unique_id += 1
            
            # Process batch when it reaches the size limit
            if len(batch_records) >= batch_size:
                batch_num += 1
                print(f"\nImporting batch {batch_num} ({len(batch_records)} records)...")
                
                response = create_batch(token, batch_records)
                
                if response.status_code == 200:
                    result = response.json()
                    imported = result.get('imported', 0)
                    updated = result.get('updated', 0)
                    print(f"  Batch {batch_num}: {imported} imported, {updated} updated")
                    stats['imported'] += imported + updated
                else:
                    print(f"  Batch {batch_num} failed: {response.status_code}")
                    stats['errors'] += len(batch_records)
                
                batch_records = []
                sleep(1)  # Small delay between batches
        
        # Process any remaining records
        if batch_records:
            batch_num += 1
            print(f"\nImporting final batch {batch_num} ({len(batch_records)} records)...")
            
            response = create_batch(token, batch_records)
            
            if response.status_code == 200:
                result = response.json()
                imported = result.get('imported', 0)
                updated = result.get('updated', 0)
                print(f"  Batch {batch_num}: {imported} imported, {updated} updated")
                stats['imported'] += imported + updated
            else:
                print(f"  Batch {batch_num} failed: {response.status_code}")
                stats['errors'] += len(batch_records)
    
    # Print summary
    print("\n" + "="*50)
    print("IMPORT SUMMARY")
    print("="*50)
    print(f"Total rows processed: {stats['total']}")
    print(f"Records imported: {stats['imported']}")
    print(f"Errors: {stats['errors']}")
    print("="*50)

def main():
    parser = argparse.ArgumentParser(description='Import new RSVP records')
    parser.add_argument('--file', required=True, help='Path to the RSVP new records CSV file')
    parser.add_argument('--username', required=True, help='API username/email')
    parser.add_argument('--password', required=True, help='API password')
    parser.add_argument('--batch-size', type=int, default=100, help='Records per batch')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    import_rsvp_new_records(args.file, args.username, args.password, args.batch_size)

if __name__ == "__main__":
    main() 
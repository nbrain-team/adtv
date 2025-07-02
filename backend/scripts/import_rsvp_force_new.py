#!/usr/bin/env python3
"""
Script to import ALL RSVP records as NEW records without matching
This allows us to import all data and deduplicate later
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
import io

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

def get_max_unique_id(token):
    """Get the highest unique ID in the database"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get total count first
    response = requests.get(
        f"{API_BASE_URL}/data-lake/records",
        headers=headers,
        params={"skip": 0, "limit": 1}
    )
    
    if response.status_code == 200:
        data = response.json()
        total = data.get("total", 0)
        
        # Start from a safe high number
        return 300000 + total
    else:
        # Default starting point
        return 300001

def create_records_direct(token, records):
    """Create multiple records using direct API calls"""
    headers = {"Authorization": f"Bearer {token}"}
    created = 0
    failed = 0
    
    for record in records:
        response = requests.post(
            f"{API_BASE_URL}/data-lake/records",
            headers=headers,
            json=record
        )
        
        if response.status_code == 200:
            created += 1
        else:
            failed += 1
            print(f"  Failed to create record: {response.status_code}")
    
    return created, failed

def import_rsvp_as_new(file_path, username, password, batch_size=50):
    """Import all RSVP records as NEW records"""
    # Login
    token = login(username, password)
    
    # Get next unique ID
    next_unique_id = get_max_unique_id(token)
    
    # Track statistics
    stats = {
        'total': 0,
        'created': 0,
        'skipped': 0,
        'failed': 0
    }
    
    print(f"\nImporting ALL RSVP records as NEW from: {file_path}")
    print(f"Starting unique_id: {next_unique_id}")
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
            phone_raw = row.get('Phone', '').strip()
            
            if not first_name or not last_name:
                print(f"Row {row_num}: Skipping - missing name")
                stats['skipped'] += 1
                continue
            
            # Clean phone
            phone = clean_phone(phone_raw)
            
            # Create record data
            record_data = {
                'unique_id': next_unique_id,
                'first_name': first_name,
                'last_name': last_name,
                'phone': phone,
                'email': row.get('Email', '').strip() or None,
                'city': row.get('City', '').strip() or None,
                'company': row.get('Company', '').strip() or None,
                'profession': row.get('Profession', '').strip() or None,
            }
            
            # Process date fields
            appointment_date = row.get('Appointment Set Date', '').strip()
            if appointment_date:
                try:
                    date_obj = datetime.strptime(appointment_date, '%m/%d/%Y')
                    record_data['appointment_set_date'] = date_obj.isoformat()
                except ValueError:
                    pass
            
            start_date = row.get('Start Date', '').strip()
            if start_date:
                try:
                    date_obj = datetime.strptime(start_date, '%m/%d/%Y')
                    record_data['start_date'] = date_obj.isoformat()
                except ValueError:
                    pass
            
            # Handle B2B Call Center field
            b2b_value = row.get('B2B Call Center (VSA)', '').strip()
            if b2b_value and b2b_value.lower() in ['yes', 'true', '1']:
                record_data['b2b_call_center_vsa'] = True
            
            # Other text fields
            interest_level = row.get('Interest Level', '').strip()
            if interest_level:
                record_data['interest_level'] = interest_level
            
            attendance = row.get('Attendance', '').strip()
            if attendance:
                record_data['attendance'] = attendance
                
            account_notes = row.get('Account Manager Notes', '').strip()
            if account_notes:
                record_data['account_manager_notes'] = account_notes
                
            craigs_notes = row.get("Craig's Notes", '').strip()
            if craigs_notes:
                record_data['craigs_notes'] = craigs_notes
            
            # Hotel fields
            hotel_name = row.get('Hotel Name', '').strip()
            if hotel_name:
                record_data['hotel_name'] = hotel_name
                
            hotel_address = row.get('Hotel Street Address', '').strip()
            if hotel_address:
                record_data['hotel_street_address'] = hotel_address
                
            hotel_city = row.get('Hotel City', '').strip()
            if hotel_city:
                record_data['hotel_city'] = hotel_city
                
            hotel_state = row.get('Hotel State', '').strip()
            if hotel_state:
                record_data['hotel_state'] = hotel_state
                
            hotel_zip = row.get('Hotel Zip', '').strip()
            if hotel_zip:
                record_data['hotel_zip'] = hotel_zip
                
            meeting_room = row.get('Hotel Meeting Room Name', '').strip()
            if meeting_room:
                record_data['hotel_meeting_room_name'] = meeting_room
            
            # Handle DMA
            dma = row.get('DMA', '').strip()
            if dma:
                if dma.startswith('#'):
                    dma = dma[1:]
                record_data['dma_market'] = dma
            
            # Add to batch
            batch_records.append(record_data)
            next_unique_id += 1
            
            # Process batch when it reaches the size limit
            if len(batch_records) >= batch_size:
                batch_num += 1
                print(f"\nProcessing batch {batch_num} ({len(batch_records)} records)...")
                
                created, failed = create_records_direct(token, batch_records)
                stats['created'] += created
                stats['failed'] += failed
                
                print(f"  Batch {batch_num}: {created} created, {failed} failed")
                
                batch_records = []
                sleep(0.5)  # Small delay between batches
        
        # Process any remaining records
        if batch_records:
            batch_num += 1
            print(f"\nProcessing final batch {batch_num} ({len(batch_records)} records)...")
            
            created, failed = create_records_direct(token, batch_records)
            stats['created'] += created
            stats['failed'] += failed
            
            print(f"  Batch {batch_num}: {created} created, {failed} failed")
    
    # Print summary
    print("\n" + "="*50)
    print("IMPORT SUMMARY")
    print("="*50)
    print(f"Total rows processed: {stats['total']}")
    print(f"Records created: {stats['created']}")
    print(f"Records skipped: {stats['skipped']}")
    print(f"Records failed: {stats['failed']}")
    print("="*50)

def main():
    parser = argparse.ArgumentParser(description='Import all RSVP records as new entries')
    parser.add_argument('--file', required=True, help='Path to the RSVP CSV file')
    parser.add_argument('--username', required=True, help='API username/email')
    parser.add_argument('--password', required=True, help='API password')
    parser.add_argument('--batch-size', type=int, default=50, help='Records per batch')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    import_rsvp_as_new(args.file, args.username, args.password, args.batch_size)

if __name__ == "__main__":
    main() 
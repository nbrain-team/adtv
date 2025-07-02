#!/usr/bin/env python3
"""
Script to import RSVP data with smart matching logic
- Matches records by First Name + Last Name + Phone
- Appends data to existing records or creates new ones
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
    digits = re.sub(r'\D', '', phone_str)
    
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

def find_matching_record(token, first_name, last_name, phone):
    """Find a record by First Name, Last Name, and Phone"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Clean the phone for comparison
    clean_phone_number = clean_phone(phone)
    if not clean_phone_number:
        return None
    
    print(f"  Searching for: {first_name} {last_name}, Phone: {clean_phone_number}")
    
    # First try searching by last name to narrow down results
    skip = 0
    limit = 500
    found = False
    
    while True:
        params = {
            "skip": skip,
            "limit": limit,
            "search": last_name  # Search by last name first
        }
        
        response = requests.get(
            f"{API_BASE_URL}/data-lake/records",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            records = data.get("records", [])
            
            # Look for exact match
            for record in records:
                if (record.get('first_name', '').lower() == first_name.lower() and
                    record.get('last_name', '').lower() == last_name.lower() and
                    record.get('phone') == clean_phone_number):
                    print(f"  Found matching record ID: {record['id']} (unique_id: {record.get('unique_id')})")
                    return record
            
            # If we've seen all records with this last name, stop
            if len(records) < limit:
                break
                
            skip += limit
        else:
            print(f"  Error searching records: {response.status_code}")
            break
    
    # If not found by last name search, try a broader search
    if not found:
        print(f"  No match found in targeted search, trying broader search...")
        
        skip = 0
        while skip < 40000:  # Reasonable limit to avoid infinite loop
            params = {
                "skip": skip,
                "limit": 1000,
            }
            
            response = requests.get(
                f"{API_BASE_URL}/data-lake/records",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                records = data.get("records", [])
                
                # Look for exact match
                for record in records:
                    if (record.get('first_name', '').lower() == first_name.lower() and
                        record.get('last_name', '').lower() == last_name.lower() and
                        record.get('phone') == clean_phone_number):
                        print(f"  Found matching record ID: {record['id']} (unique_id: {record.get('unique_id')})")
                        return record
                
                # If we've seen all records, stop
                if len(records) < 1000:
                    break
                    
                skip += 1000
                
                # Show progress
                if skip % 5000 == 0:
                    print(f"    Searched {skip} records so far...")
            else:
                print(f"  Error in broader search: {response.status_code}")
                break
    
    print("  No matching record found")
    return None

def get_next_unique_id(token):
    """Get the next available unique ID"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get the highest unique_id
    params = {
        "skip": 0,
        "limit": 1,
        "columns": "unique_id"
    }
    
    # Note: This assumes the API returns records sorted by unique_id desc
    # If not, we'd need to fetch all and find max
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

def update_record(token, record_id, new_data):
    """Update an existing record with new data"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.put(
        f"{API_BASE_URL}/data-lake/records/{record_id}",
        headers=headers,
        json=new_data
    )
    
    return response

def create_record(token, record_data):
    """Create a new record"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{API_BASE_URL}/data-lake/records",
        headers=headers,
        json=record_data
    )
    
    return response

def process_rsvp_data(file_path, username, password, test_mode=False):
    """Process RSVP data with matching logic"""
    # Login
    token = login(username, password)
    
    # Track statistics
    stats = {
        'total': 0,
        'matched': 0,
        'created': 0,
        'errors': 0
    }
    
    # Get next unique ID for new records
    next_unique_id = get_next_unique_id(token)
    
    print(f"\nProcessing RSVP file: {file_path}")
    print("="*50)
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, start=2):
            stats['total'] += 1
            
            # Extract key fields
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()
            phone = row.get('Phone', '').strip()
            
            if not first_name or not last_name or not phone:
                print(f"\nRow {row_num}: Skipping - missing required fields")
                stats['errors'] += 1
                continue
            
            print(f"\nRow {row_num}: Processing {first_name} {last_name}")
            
            # Look for matching record
            existing_record = find_matching_record(token, first_name, last_name, phone)
            
            # Prepare the data to update/create
            update_data = {}
            
            # Map RSVP fields to database fields
            field_mapping = {
                'Appointment Set Date': 'appointment_set_date',
                'B2B Call Center (VSA)': 'b2b_call_center_vsa',
                'Interest Level': 'interest_level',
                'Attendance': 'attendance',
                'Account Manager Notes': 'account_manager_notes',
                "Craig's Notes": 'craigs_notes',
                'Profession': 'profession',
                'City': 'city',
                'Company': 'company',
                'Email': 'email',
                'DMA': 'dma_market',
                'Start Date': 'start_date',
                'Hotel Name': 'hotel_name',
                'Hotel Street Address': 'hotel_street_address',
                'Hotel City': 'hotel_city',
                'Hotel State': 'hotel_state',
                'Hotel Zip': 'hotel_zip',
                'Hotel Meeting Room Name': 'hotel_meeting_room_name'
            }
            
            # Process each field
            for csv_field, db_field in field_mapping.items():
                value = row.get(csv_field, '').strip()
                if value:
                    # Special handling for DMA field
                    if csv_field == 'DMA' and value.startswith('#'):
                        value = value[1:]  # Remove the # prefix
                    
                    # Special handling for date fields
                    if 'date' in db_field.lower() and value:
                        try:
                            # Parse M/D/YYYY format
                            date_obj = datetime.strptime(value, '%m/%d/%Y')
                            value = date_obj.isoformat()
                        except ValueError:
                            # Try other common formats
                            try:
                                date_obj = datetime.strptime(value, '%Y-%m-%d')
                                value = date_obj.isoformat()
                            except ValueError:
                                print(f"  Warning: Could not parse date '{value}' for field '{csv_field}'")
                                continue
                    
                    update_data[db_field] = value
            
            if existing_record:
                # Update existing record
                print(f"  Updating existing record ID: {existing_record['id']}")
                
                if test_mode:
                    print("  TEST MODE: Would update with:", json.dumps(update_data, indent=2))
                    stats['matched'] += 1
                else:
                    response = update_record(token, existing_record['id'], update_data)
                    
                    if response.status_code == 200:
                        print("  ✓ Successfully updated record")
                        stats['matched'] += 1
                    else:
                        print(f"  ✗ Failed to update: {response.status_code} - {response.text[:200]}")
                        stats['errors'] += 1
            else:
                # Create new record
                print(f"  Creating new record with unique_id: {next_unique_id}")
                
                # Add required fields for new record
                new_record = {
                    'unique_id': next_unique_id,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': clean_phone(phone),
                    **update_data
                }
                
                if test_mode:
                    print("  TEST MODE: Would create:", json.dumps(new_record, indent=2))
                    stats['created'] += 1
                else:
                    response = create_record(token, new_record)
                    
                    if response.status_code == 200:
                        print("  ✓ Successfully created new record")
                        stats['created'] += 1
                        next_unique_id += 1
                    else:
                        print(f"  ✗ Failed to create: {response.status_code} - {response.text[:200]}")
                        stats['errors'] += 1
            
            # Add delay to avoid overwhelming the server
            if not test_mode:
                sleep(0.5)
    
    # Print summary
    print("\n" + "="*50)
    print("IMPORT SUMMARY")
    print("="*50)
    print(f"Total rows processed: {stats['total']}")
    print(f"Records matched and updated: {stats['matched']}")
    print(f"New records created: {stats['created']}")
    print(f"Errors: {stats['errors']}")
    print("="*50)

def main():
    parser = argparse.ArgumentParser(description='Import RSVP data with smart matching')
    parser.add_argument('--file', required=True, help='Path to the RSVP CSV file')
    parser.add_argument('--username', required=True, help='API username/email')
    parser.add_argument('--password', required=True, help='API password')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no actual changes)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    process_rsvp_data(args.file, args.username, args.password, args.test)

if __name__ == "__main__":
    main() 
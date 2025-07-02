#!/usr/bin/env python3
"""
Script to diagnose which specific records are failing and why
"""

import os
import sys
import csv
import json
import requests
import argparse
from time import sleep
import re

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

def get_existing_unique_ids(token):
    """Get all existing unique IDs from the database"""
    headers = {"Authorization": f"Bearer {token}"}
    existing_ids = set()
    skip = 0
    limit = 1000
    
    print("Fetching existing records...")
    
    while True:
        response = requests.get(
            f"{API_BASE_URL}/data-lake/records",
            headers=headers,
            params={"skip": skip, "limit": limit, "columns": "unique_id"}
        )
        
        if response.status_code == 200:
            data = response.json()
            records = data.get("records", [])
            
            for record in records:
                if record.get("unique_id"):
                    existing_ids.add(record["unique_id"])
            
            if len(records) < limit:
                break
            
            skip += limit
        else:
            print(f"Error fetching records: {response.status_code}")
            break
    
    print(f"Found {len(existing_ids)} existing records")
    return existing_ids

def test_single_record(token, record):
    """Test importing a single record"""
    # Column mapping
    column_mapping = {
        'unique_id': 'unique_id',
        'speaker_source': 'speaker_source',
        'profession': 'profession',
        'city': 'city',
        'state_spelled_out': 'state_spelled_out',
        'state_initials': 'state_initials',
        'first_name': 'first_name',
        'last_name': 'last_name',
        'company': 'company',
        'phone': 'phone',
        'email': 'email',
        'one_yr_total_sales_usd': 'one_yr_total_sales_usd',
        'one_yr_total_transactions_count': 'one_yr_total_transactions_count',
        'lender_one_yr_volume_usd': 'lender_one_yr_volume_usd',
        'lender_one_yr_closed_loans_count': 'lender_one_yr_closed_loans_count',
        'years_experience': 'years_experience',
        'lender_banker_or_broker': 'lender_banker_or_broker'
    }
    
    # Create CSV content for single record
    import io
    csv_buffer = io.StringIO()
    
    fieldnames = list(column_mapping.keys())
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    
    row = {k: v for k, v in record.items() if v is not None and k in fieldnames}
    writer.writerow(row)
    
    # Convert to bytes
    csv_content = csv_buffer.getvalue().encode('utf-8')
    csv_buffer.close()
    
    # Send to API
    headers = {"Authorization": f"Bearer {token}"}
    files = {'file': ('single_record.csv', csv_content, 'text/csv')}
    params = {'mapping': json.dumps(column_mapping)}
    
    response = requests.post(
        f"{API_BASE_URL}/data-lake/import-csv",
        headers=headers,
        files=files,
        params=params
    )
    
    return response.status_code, response.text

def diagnose_failed_records(file_path, username, password, sample_size=10):
    """Diagnose why records are failing"""
    # Login
    token = login(username, password)
    
    # Get existing unique IDs
    existing_ids = get_existing_unique_ids(token)
    
    # State mapping
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
    
    # Read CSV and find missing records
    missing_records = []
    next_unique_id = 100001
    total_processed = 0
    
    print(f"\nReading {file_path} to find missing records...")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, start=2):
            # Check if this unique_id exists
            if next_unique_id not in existing_ids:
                try:
                    # Process row data
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
                        'csv_row': row_num  # Keep track of original row
                    }
                    
                    # Handle state initials
                    state = record_data.get('state_spelled_out', '')
                    if state and len(state) == 2:
                        record_data['state_initials'] = state.upper()
                    elif state in state_map:
                        record_data['state_initials'] = state_map[state]
                    
                    # Handle numeric fields
                    for csv_field, db_field in [
                        ('1YR Total Sales $', 'one_yr_total_sales_usd'),
                        ('1YR Total Transactions #', 'one_yr_total_transactions_count'),
                        ('Lender 1YR Volume $', 'lender_one_yr_volume_usd'),
                        ('Lender 1YR Closed Loans #', 'lender_one_yr_closed_loans_count'),
                        ('Years Experience', 'years_experience')
                    ]:
                        value = row.get(csv_field, '').strip()
                        if value:
                            value = value.replace('$', '').replace(',', '')
                            try:
                                if 'usd' in db_field:
                                    record_data[db_field] = float(value)
                                else:
                                    record_data[db_field] = int(value)
                            except ValueError:
                                pass
                    
                    # Handle Lender type
                    lender_type = row.get('Lender- Banker or Broker', '').strip()
                    if lender_type:
                        record_data['lender_banker_or_broker'] = lender_type
                    
                    missing_records.append(record_data)
                    
                except Exception as e:
                    print(f"Error processing row {row_num}: {str(e)}")
            
            next_unique_id += 1
            total_processed += 1
            
            if len(missing_records) >= sample_size:
                break
    
    print(f"\nTesting {len(missing_records)} sample records individually...")
    
    failed_records = []
    
    for i, record in enumerate(missing_records):
        print(f"\nTesting record {i+1}/{len(missing_records)} (Row {record['csv_row']}, ID: {record['unique_id']})")
        print(f"  Name: {record.get('first_name')} {record.get('last_name')}")
        print(f"  Company: {record.get('company')}")
        print(f"  Phone: {record.get('phone')}")
        print(f"  Email: {record.get('email')}")
        
        # Remove csv_row from the record before testing
        csv_row = record.pop('csv_row')
        
        status_code, response_text = test_single_record(token, record)
        
        if status_code == 200:
            print("  ✓ SUCCESS")
        else:
            print(f"  ✗ FAILED: {status_code}")
            print(f"  Error: {response_text[:200]}...")
            failed_records.append({
                'csv_row': csv_row,
                'record': record,
                'error': response_text
            })
        
        sleep(1)  # Small delay between tests
    
    if failed_records:
        print(f"\n{'='*50}")
        print(f"FAILED RECORDS ANALYSIS:")
        print(f"{'='*50}")
        
        for failed in failed_records:
            print(f"\nRow {failed['csv_row']} (ID: {failed['record']['unique_id']}):")
            print(f"  Data: {json.dumps(failed['record'], indent=2)}")
            print(f"  Error: {failed['error'][:500]}")
    else:
        print("\nAll tested records imported successfully!")

def main():
    parser = argparse.ArgumentParser(description='Diagnose failed record imports')
    parser.add_argument('--file', default='/Users/dannydemichele/Adstv/data lake/MasterProspects.csv', 
                        help='Path to MasterProspects.csv file')
    parser.add_argument('--sample-size', type=int, default=10, 
                        help='Number of missing records to test (default: 10)')
    parser.add_argument('--username', required=True, help='API username/email')
    parser.add_argument('--password', required=True, help='API password')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    diagnose_failed_records(args.file, args.username, args.password, args.sample_size)

if __name__ == "__main__":
    main() 
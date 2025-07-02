#!/usr/bin/env python3
"""
Script to import only the failed records from MasterProspects.csv
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
    
    print("Fetching existing records to identify missing ones...")
    
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
            print(f"  Fetched {len(existing_ids)} unique IDs so far...")
        else:
            print(f"Error fetching records: {response.status_code}")
            break
    
    print(f"Found {len(existing_ids)} existing records")
    return existing_ids

def import_batch_via_api(token, records):
    """Import a batch of records via API"""
    # Create CSV content
    if not records:
        return {"imported": 0, "updated": 0, "total_errors": 0}
    
    # Create column mapping
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
    
    # Create CSV in memory
    import io
    csv_buffer = io.StringIO()
    
    fieldnames = list(column_mapping.keys())
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    
    for record in records:
        row = {k: v for k, v in record.items() if v is not None and k in fieldnames}
        writer.writerow(row)
    
    # Convert to bytes
    csv_content = csv_buffer.getvalue().encode('utf-8')
    csv_buffer.close()
    
    # Send to API
    headers = {"Authorization": f"Bearer {token}"}
    files = {'file': ('batch.csv', csv_content, 'text/csv')}
    params = {'mapping': json.dumps(column_mapping)}
    
    response = requests.post(
        f"{API_BASE_URL}/data-lake/import-csv",
        headers=headers,
        files=files,
        params=params
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Import failed: {response.status_code} - {response.text}")
        return None

def import_failed_records(file_path, username, password, batch_size=100):
    """Import only the records that failed in the initial import"""
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
            
            if total_processed % 1000 == 0:
                print(f"  Processed {total_processed} records, found {len(missing_records)} missing...")
    
    print(f"\nFound {len(missing_records)} missing records to import")
    
    if not missing_records:
        print("No missing records found!")
        return
    
    # Import missing records in batches
    total_imported = 0
    total_errors = 0
    batch_num = 0
    
    for i in range(0, len(missing_records), batch_size):
        batch = missing_records[i:i + batch_size]
        batch_num += 1
        
        print(f"\nImporting batch {batch_num} ({len(batch)} records)...")
        result = import_batch_via_api(token, batch)
        
        if result:
            imported = result.get('imported', 0)
            updated = result.get('updated', 0)
            errors = result.get('total_errors', 0)
            total_imported += imported + updated
            total_errors += errors
            print(f"  Batch {batch_num}: {imported} imported, {updated} updated, {errors} errors")
        else:
            # Retry once
            print("  Retrying batch...")
            sleep(5)
            result = import_batch_via_api(token, batch)
            if result:
                imported = result.get('imported', 0)
                updated = result.get('updated', 0)
                errors = result.get('total_errors', 0)
                total_imported += imported + updated
                total_errors += errors
                print(f"  Batch {batch_num} (retry): {imported} imported, {updated} updated, {errors} errors")
            else:
                print(f"  Batch {batch_num} failed after retry")
                total_errors += len(batch)
        
        # Small delay between batches
        sleep(1)
    
    print(f"\n{'='*50}")
    print(f"Import of missing records complete!")
    print(f"Total records imported: {total_imported}")
    print(f"Total errors: {total_errors}")
    print(f"{'='*50}")

def main():
    parser = argparse.ArgumentParser(description='Import failed/missing records from MasterProspects.csv')
    parser.add_argument('--file', default='/Users/dannydemichele/Adstv/data lake/MasterProspects.csv', 
                        help='Path to MasterProspects.csv file')
    parser.add_argument('--batch-size', type=int, default=100, 
                        help='Batch size for import (default: 100)')
    parser.add_argument('--username', required=True, help='API username/email')
    parser.add_argument('--password', required=True, help='API password')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    import_failed_records(args.file, args.username, args.password, args.batch_size)

if __name__ == "__main__":
    main() 
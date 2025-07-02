#!/usr/bin/env python3
"""
Script to import the fixed CSV file with cleaned data
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

def import_batch(token, batch_data, column_mapping):
    """Import a batch of records via API"""
    # Create CSV content from batch
    import io
    csv_buffer = io.StringIO()
    
    if batch_data:
        # Get all unique fieldnames across all records in the batch
        all_fields = set()
        for record in batch_data:
            all_fields.update(record.keys())
        fieldnames = sorted(list(all_fields))
        
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in batch_data:
            writer.writerow(record)
    
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
    
    return response

def import_fixed_csv(file_path, username, password, batch_size=100):
    """Import the fixed CSV file"""
    # Login
    token = login(username, password)
    
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
    
    # Column mapping for the fixed CSV
    column_mapping = {
        'unique_id': 'unique_id',
        'speaker_source': 'speaker_source',
        'profession': 'profession',
        'city': 'city',
        'state': 'state_spelled_out',
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
    
    # Process the CSV
    batch_data = []
    batch_num = 0
    total_imported = 0
    total_errors = 0
    
    print(f"\nReading {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Process the record
            record = {
                'unique_id': row.get('unique_id', '').strip(),
                'speaker_source': row.get('speaker_source', '').strip(),
                'profession': row.get('profession', '').strip(),
                'city': row.get('city', '').strip(),
                'state': row.get('state', '').strip(),
                'first_name': row.get('first_name', '').strip(),
                'last_name': row.get('last_name', '').strip(),
                'company': row.get('company', '').strip(),
                'phone': clean_phone(row.get('phone', '')),
                'email': row.get('email', '').strip(),
            }
            
            # Handle state initials
            state = record.get('state', '')
            if state and len(state) == 2:
                record['state_initials'] = state.upper()
            elif state in state_map:
                record['state_initials'] = state_map[state]
            else:
                record['state_initials'] = ''
            
            # Handle numeric fields
            for field in ['one_yr_total_sales_usd', 'one_yr_total_transactions_count',
                         'lender_one_yr_volume_usd', 'lender_one_yr_closed_loans_count',
                         'years_experience']:
                value = row.get(field, '').strip()
                if value:
                    value = value.replace('$', '').replace(',', '')
                    try:
                        if 'usd' in field:
                            record[field] = float(value)
                        else:
                            record[field] = int(value)
                    except ValueError:
                        record[field] = None
                else:
                    record[field] = None
            
            # Handle lender type
            record['lender_banker_or_broker'] = row.get('lender_banker_or_broker', '').strip()
            
            # Remove None values and empty strings for cleaner import
            record = {k: v for k, v in record.items() if v is not None and v != ''}
            
            batch_data.append(record)
            
            # Process batch when it reaches the size limit
            if len(batch_data) >= batch_size:
                batch_num += 1
                print(f"\nImporting batch {batch_num} ({len(batch_data)} records)...")
                
                response = import_batch(token, batch_data, column_mapping)
                
                if response.status_code == 200:
                    result = response.json()
                    imported = result.get('imported', 0)
                    updated = result.get('updated', 0)
                    errors = result.get('errors', 0)
                    print(f"  Batch {batch_num}: {imported} imported, {updated} updated, {errors} errors")
                    total_imported += imported + updated
                else:
                    print(f"Import failed: {response.status_code} - {response.text[:200]}...")
                    total_errors += len(batch_data)
                    
                    # Retry with smaller batch if it fails
                    if batch_size > 10:
                        print("  Retrying with smaller batches...")
                        sub_batch_size = 10
                        for i in range(0, len(batch_data), sub_batch_size):
                            sub_batch = batch_data[i:i+sub_batch_size]
                            print(f"    Retrying sub-batch of {len(sub_batch)} records...")
                            sub_response = import_batch(token, sub_batch, column_mapping)
                            if sub_response.status_code == 200:
                                sub_result = sub_response.json()
                                imported = sub_result.get('imported', 0)
                                updated = sub_result.get('updated', 0)
                                print(f"    Success: {imported} imported, {updated} updated")
                                total_imported += imported + updated
                                total_errors -= len(sub_batch)
                            else:
                                print(f"    Sub-batch failed: {sub_response.status_code}")
                            sleep(1)
                
                batch_data = []
                sleep(2)  # Wait between batches
        
        # Process any remaining records
        if batch_data:
            batch_num += 1
            print(f"\nImporting final batch {batch_num} ({len(batch_data)} records)...")
            
            response = import_batch(token, batch_data, column_mapping)
            
            if response.status_code == 200:
                result = response.json()
                imported = result.get('imported', 0)
                updated = result.get('updated', 0)
                errors = result.get('errors', 0)
                print(f"  Batch {batch_num}: {imported} imported, {updated} updated, {errors} errors")
                total_imported += imported + updated
            else:
                print(f"Import failed: {response.status_code} - {response.text[:200]}...")
                total_errors += len(batch_data)
    
    print("\n" + "="*50)
    print("Import complete!")
    print(f"Total records imported/updated: {total_imported}")
    print(f"Total errors: {total_errors}")
    print("="*50)

def main():
    parser = argparse.ArgumentParser(description='Import fixed CSV file')
    parser.add_argument('--file', required=True, help='Path to the fixed CSV file')
    parser.add_argument('--batch-size', type=int, default=100, 
                        help='Number of records per batch (default: 100)')
    parser.add_argument('--username', required=True, help='API username/email')
    parser.add_argument('--password', required=True, help='API password')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    import_fixed_csv(args.file, args.username, args.password, args.batch_size)

if __name__ == "__main__":
    main() 
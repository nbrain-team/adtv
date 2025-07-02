#!/usr/bin/env python3
"""
Script to import MasterProspects.csv using the API endpoint
"""

import os
import sys
import csv
import json
import requests
import argparse
from time import sleep
import re

# API configuration
API_BASE_URL = "https://adtv-backend.onrender.com"
USERNAME = os.getenv('ADTV_USERNAME', 'admin@example.com')
PASSWORD = os.getenv('ADTV_PASSWORD', 'admin123')

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

def login():
    """Login and get access token"""
    print("Logging in to API...")
    # OAuth2PasswordRequestForm expects 'username' field but we use email
    response = requests.post(
        f"{API_BASE_URL}/login",
        data={"username": USERNAME, "password": PASSWORD}  # 'username' field contains email
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("Login successful!")
        return token
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        sys.exit(1)

def create_batch_csv(records, csv_path):
    """Create a temporary CSV file for batch import"""
    fieldnames = [
        'unique_id', 'speaker_source', 'profession', 'city', 'state_spelled_out',
        'state_initials', 'first_name', 'last_name', 'company', 'phone', 'email',
        'one_yr_total_sales_usd', 'one_yr_total_transactions_count',
        'lender_one_yr_volume_usd', 'lender_one_yr_closed_loans_count',
        'years_experience', 'lender_banker_or_broker'
    ]
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            # Only write non-None values
            row = {k: v for k, v in record.items() if v is not None}
            writer.writerow(row)

def import_batch(token, csv_path, column_mapping):
    """Import a batch using the API"""
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(csv_path, 'rb') as f:
        files = {'file': ('batch.csv', f, 'text/csv')}
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

def import_master_prospects(file_path, batch_size=500):
    """Import MasterProspects.csv using API in batches"""
    # Login first
    token = login()
    
    # Column mapping for the API
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
    
    try:
        next_unique_id = 100001
        total_imported = 0
        total_updated = 0
        total_errors = 0
        batch_num = 0
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            batch = []
            
            print(f"Starting import from {file_path}...")
            print(f"Unique IDs will start from {next_unique_id}")
            print(f"Using batch size of {batch_size} records per API call")
            
            for row_num, row in enumerate(reader, start=2):
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
                    for field, csv_field, db_field in [
                        ('1YR Total Sales $', '1YR Total Sales $', 'one_yr_total_sales_usd'),
                        ('1YR Total Transactions #', '1YR Total Transactions #', 'one_yr_total_transactions_count'),
                        ('Lender 1YR Volume $', 'Lender 1YR Volume $', 'lender_one_yr_volume_usd'),
                        ('Lender 1YR Closed Loans #', 'Lender 1YR Closed Loans #', 'lender_one_yr_closed_loans_count'),
                        ('Years Experience', 'Years Experience', 'years_experience')
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
                    
                    batch.append(record_data)
                    next_unique_id += 1
                    
                    # Import batch when it reaches batch_size
                    if len(batch) >= batch_size:
                        batch_num += 1
                        print(f"\nImporting batch {batch_num} ({len(batch)} records)...")
                        
                        # Create temporary CSV
                        temp_csv = f"temp_batch_{batch_num}.csv"
                        create_batch_csv(batch, temp_csv)
                        
                        # Import via API
                        result = import_batch(token, temp_csv, column_mapping)
                        
                        if result:
                            total_imported += result.get('imported', 0)
                            total_updated += result.get('updated', 0)
                            total_errors += result.get('total_errors', 0)
                            print(f"Batch {batch_num} complete: {result.get('imported', 0)} imported, {result.get('updated', 0)} updated")
                        else:
                            print(f"Batch {batch_num} failed - retrying...")
                            sleep(5)  # Wait before retry
                            result = import_batch(token, temp_csv, column_mapping)
                            if result:
                                total_imported += result.get('imported', 0)
                                total_updated += result.get('updated', 0)
                                total_errors += result.get('total_errors', 0)
                            else:
                                print(f"Batch {batch_num} failed after retry")
                                total_errors += len(batch)
                        
                        # Clean up temp file
                        os.remove(temp_csv)
                        batch = []
                        
                        # Small delay between batches
                        sleep(2)
                        
                except Exception as e:
                    total_errors += 1
                    print(f"Error processing row {row_num}: {str(e)}")
                    continue
            
            # Import remaining records
            if batch:
                batch_num += 1
                print(f"\nImporting final batch {batch_num} ({len(batch)} records)...")
                
                temp_csv = f"temp_batch_{batch_num}.csv"
                create_batch_csv(batch, temp_csv)
                
                result = import_batch(token, temp_csv, column_mapping)
                
                if result:
                    total_imported += result.get('imported', 0)
                    total_updated += result.get('updated', 0)
                    total_errors += result.get('total_errors', 0)
                
                os.remove(temp_csv)
            
            print(f"\n{'='*50}")
            print(f"Import complete!")
            print(f"Total new records imported: {total_imported}")
            print(f"Total existing records updated: {total_updated}")
            print(f"Total errors: {total_errors}")
            print(f"{'='*50}")
            
    except Exception as e:
        print(f"Error during import: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Import MasterProspects.csv via API')
    parser.add_argument('--file', default='/Users/dannydemichele/Adstv/data lake/MasterProspects.csv', 
                        help='Path to MasterProspects.csv file')
    parser.add_argument('--batch-size', type=int, default=500, 
                        help='Batch size for import (default: 500)')
    parser.add_argument('--username', help='API username (or set ADTV_USERNAME env var)')
    parser.add_argument('--password', help='API password (or set ADTV_PASSWORD env var)')
    
    args = parser.parse_args()
    
    if args.username:
        global USERNAME
        USERNAME = args.username
    if args.password:
        global PASSWORD
        PASSWORD = args.password
    
    if not os.path.exists(args.file):
        print(f"Error: File '{args.file}' not found")
        sys.exit(1)
    
    import_master_prospects(args.file, args.batch_size)

if __name__ == "__main__":
    main() 
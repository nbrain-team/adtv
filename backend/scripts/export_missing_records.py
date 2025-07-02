#!/usr/bin/env python3
"""
Script to export missing records to a CSV file for manual correction
"""

import os
import sys
import csv
import requests
import argparse
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
    
    return phone_str  # Return original if can't format

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

def export_missing_records(input_file, output_file, username, password):
    """Export missing records to a CSV file"""
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
    email_issues = 0
    
    print(f"\nReading {input_file} to find missing records...")
    
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, start=2):
            # Check if this unique_id exists
            if next_unique_id not in existing_ids:
                # Process row data
                record_data = {
                    'unique_id': next_unique_id,
                    'original_row': row_num,
                    'speaker_source': row.get('Speaker/Source', '').strip() if row.get('Speaker/Source') else '',
                    'profession': row.get('Profession', '').strip() if row.get('Profession') else '',
                    'city': row.get('City', '').strip() if row.get('City') else '',
                    'state': row.get('State', '').strip() if row.get('State') else '',
                    'first_name': row.get('First Name', '').strip() if row.get('First Name') else '',
                    'last_name': row.get('Last Name', '').strip() if row.get('Last Name') else '',
                    'company': row.get('Company', '').strip() if row.get('Company') else '',
                    'phone': row.get('Phone', '').strip() if row.get('Phone') else '',
                    'email': row.get('Email Address', '').strip() if row.get('Email Address') else '',
                    'one_yr_total_sales_usd': row.get('1YR Total Sales $', '').strip() if row.get('1YR Total Sales $') else '',
                    'one_yr_total_transactions_count': row.get('1YR Total Transactions #', '').strip() if row.get('1YR Total Transactions #') else '',
                    'lender_one_yr_volume_usd': row.get('Lender 1YR Volume $', '').strip() if row.get('Lender 1YR Volume $') else '',
                    'lender_one_yr_closed_loans_count': row.get('Lender 1YR Closed Loans #', '').strip() if row.get('Lender 1YR Closed Loans #') else '',
                    'years_experience': row.get('Years Experience', '').strip() if row.get('Years Experience') else '',
                    'lender_banker_or_broker': row.get('Lender- Banker or Broker', '').strip() if row.get('Lender- Banker or Broker') else '',
                }
                
                # Check for email issues
                email = record_data['email']
                if email and ('@' in email):
                    # Check for multiple emails concatenated
                    if email.count('@') > 1:
                        record_data['email_issue'] = 'Multiple emails concatenated'
                        email_issues += 1
                    # Check for invalid format
                    elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                        record_data['email_issue'] = 'Invalid email format'
                        email_issues += 1
                    else:
                        record_data['email_issue'] = ''
                else:
                    record_data['email_issue'] = ''
                
                missing_records.append(record_data)
            
            next_unique_id += 1
            total_processed += 1
            
            if total_processed % 1000 == 0:
                print(f"  Processed {total_processed} records, found {len(missing_records)} missing...")
    
    print(f"\nFound {len(missing_records)} missing records")
    print(f"Found {email_issues} records with email issues")
    
    # Write missing records to CSV
    if missing_records:
        fieldnames = [
            'unique_id', 'original_row', 'speaker_source', 'profession', 'city', 'state',
            'first_name', 'last_name', 'company', 'phone', 'email', 'email_issue',
            'one_yr_total_sales_usd', 'one_yr_total_transactions_count',
            'lender_one_yr_volume_usd', 'lender_one_yr_closed_loans_count',
            'years_experience', 'lender_banker_or_broker'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in missing_records:
                writer.writerow(record)
        
        print(f"\nExported {len(missing_records)} missing records to: {output_file}")
        print(f"\nNOTE: Records with email issues have been marked in the 'email_issue' column")
        print("Please fix any email issues before re-importing.")
    else:
        print("\nNo missing records found!")

def main():
    parser = argparse.ArgumentParser(description='Export missing records to CSV for manual correction')
    parser.add_argument('--input', default='/Users/dannydemichele/Adstv/data lake/MasterProspects.csv', 
                        help='Path to original MasterProspects.csv file')
    parser.add_argument('--output', default='missing_records_to_fix.csv', 
                        help='Output CSV file name (default: missing_records_to_fix.csv)')
    parser.add_argument('--username', required=True, help='API username/email')
    parser.add_argument('--password', required=True, help='API password')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        sys.exit(1)
    
    export_missing_records(args.input, args.output, args.username, args.password)

if __name__ == "__main__":
    main() 
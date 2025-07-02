#!/usr/bin/env python3
"""
Script to find duplicate records in the Data Lake
"""

import os
import sys
import csv
import requests
import argparse
from collections import defaultdict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API configuration
API_BASE_URL = "https://adtv-backend.onrender.com"

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

def find_duplicates(username, password):
    """Find all duplicate records in the database"""
    # Login
    token = login(username, password)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Dictionary to store records by key
    records_by_key = defaultdict(list)
    
    # Fetch all records
    print("\nFetching all records from database...")
    skip = 0
    limit = 1000
    total_records = 0
    
    while True:
        params = {
            "skip": skip,
            "limit": limit,
        }
        
        response = requests.get(
            f"{API_BASE_URL}/data-lake/records",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            records = data.get("records", [])
            
            for record in records:
                first_name = (record.get('first_name') or '').lower().strip()
                last_name = (record.get('last_name') or '').lower().strip()
                phone = record.get('phone') or ''
                
                if first_name and last_name and phone:
                    key = f"{first_name}|{last_name}|{phone}"
                    records_by_key[key].append(record)
                
                total_records += 1
            
            if len(records) < limit:
                break
                
            skip += limit
            if skip % 5000 == 0:
                print(f"  Processed {skip} records...")
        else:
            print(f"Error fetching records: {response.status_code}")
            break
    
    print(f"Total records processed: {total_records}")
    
    # Find duplicates
    duplicates = []
    for key, record_list in records_by_key.items():
        if len(record_list) > 1:
            duplicates.append({
                'key': key,
                'records': record_list,
                'count': len(record_list)
            })
    
    # Sort by number of duplicates
    duplicates.sort(key=lambda x: x['count'], reverse=True)
    
    print(f"\nFound {len(duplicates)} sets of duplicate records")
    
    # Write duplicates report
    if duplicates:
        output_file = 'duplicate_records_report.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'duplicate_set', 'record_id', 'unique_id', 'first_name', 'last_name', 
                'phone', 'email', 'company', 'city', 'created_at', 
                'appointment_set_date', 'hotel_name', 'interest_level'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, dup_set in enumerate(duplicates, 1):
                for record in dup_set['records']:
                    row = {
                        'duplicate_set': i,
                        'record_id': record.get('id'),
                        'unique_id': record.get('unique_id'),
                        'first_name': record.get('first_name'),
                        'last_name': record.get('last_name'),
                        'phone': record.get('phone'),
                        'email': record.get('email'),
                        'company': record.get('company'),
                        'city': record.get('city'),
                        'created_at': record.get('created_at'),
                        'appointment_set_date': record.get('appointment_set_date'),
                        'hotel_name': record.get('hotel_name'),
                        'interest_level': record.get('interest_level')
                    }
                    writer.writerow(row)
        
        print(f"Duplicate report written to: {output_file}")
        
        # Show sample duplicates
        print("\nSample duplicate sets:")
        for i, dup_set in enumerate(duplicates[:5], 1):
            print(f"\nDuplicate Set {i}:")
            first_record = dup_set['records'][0]
            print(f"  Name: {first_record.get('first_name')} {first_record.get('last_name')}")
            print(f"  Phone: {first_record.get('phone')}")
            print(f"  Records:")
            for record in dup_set['records']:
                print(f"    - ID: {record.get('id')}, Unique ID: {record.get('unique_id')}, "
                      f"Created: {record.get('created_at')}, "
                      f"RSVP Date: {record.get('appointment_set_date', 'N/A')}")
    
    return duplicates

def main():
    parser = argparse.ArgumentParser(description='Find duplicate records in Data Lake')
    parser.add_argument('--username', required=True, help='API username/email')
    parser.add_argument('--password', required=True, help='API password')
    
    args = parser.parse_args()
    
    find_duplicates(args.username, args.password)

if __name__ == "__main__":
    main() 
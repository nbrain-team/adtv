#!/usr/bin/env python3
"""
Script to analyze RSVP data and split into:
1. Matches - records that exist in both Master and RSVP (for updating)
2. New - records only in RSVP (for creating)
"""

import os
import sys
import csv
import re
from collections import defaultdict

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

def create_match_key(first_name, last_name, phone):
    """Create a key for matching records"""
    if not first_name or not last_name or not phone:
        return None
    
    clean_phone_num = clean_phone(phone)
    if not clean_phone_num:
        return None
        
    return f"{first_name.lower().strip()}|{last_name.lower().strip()}|{clean_phone_num}"

def analyze_files(master_file, rsvp_file, output_dir="."):
    """Analyze master and RSVP files to find matches"""
    
    # First, load all master records into memory for matching
    print("Loading master prospects file...")
    master_records = {}
    master_count = 0
    
    with open(master_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            master_count += 1
            # Extract key fields from master
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()
            phone = row.get('Phone', '').strip()
            
            key = create_match_key(first_name, last_name, phone)
            if key:
                master_records[key] = row
            
            if master_count % 5000 == 0:
                print(f"  Loaded {master_count} master records...")
    
    print(f"Loaded {master_count} total master records")
    print(f"Found {len(master_records)} records with valid matching keys")
    
    # Now process RSVP file
    print("\nProcessing RSVP file...")
    matches = []
    new_records = []
    invalid_records = []
    rsvp_count = 0
    
    with open(rsvp_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rsvp_headers = reader.fieldnames
        
        for row in reader:
            rsvp_count += 1
            
            # Extract key fields from RSVP
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()
            phone = row.get('Phone', '').strip()
            
            if not first_name or not last_name or not phone:
                invalid_records.append(row)
                continue
            
            key = create_match_key(first_name, last_name, phone)
            if not key:
                invalid_records.append(row)
                continue
            
            if key in master_records:
                # Found a match!
                master_row = master_records[key]
                # Add master unique_id to the RSVP record for reference
                row['_master_unique_id'] = master_row.get('unique_id', '')
                row['_match_status'] = 'MATCHED'
                matches.append(row)
            else:
                # New record
                row['_match_status'] = 'NEW'
                new_records.append(row)
            
            if rsvp_count % 1000 == 0:
                print(f"  Processed {rsvp_count} RSVP records...")
    
    print(f"\nAnalysis complete!")
    print(f"Total RSVP records: {rsvp_count}")
    print(f"Matched records: {len(matches)}")
    print(f"New records: {len(new_records)}")
    print(f"Invalid records (missing required fields): {len(invalid_records)}")
    
    # Write output files
    # 1. Matched records (for updating)
    matches_file = os.path.join(output_dir, 'rsvp_matches.csv')
    if matches:
        with open(matches_file, 'w', newline='', encoding='utf-8') as f:
            # Include all original RSVP fields plus our match info
            fieldnames = rsvp_headers + ['_master_unique_id', '_match_status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(matches)
        print(f"\nMatched records written to: {matches_file}")
    
    # 2. New records (for creating)
    new_file = os.path.join(output_dir, 'rsvp_new.csv')
    if new_records:
        with open(new_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = rsvp_headers + ['_match_status']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(new_records)
        print(f"New records written to: {new_file}")
    
    # 3. Invalid records (for review)
    invalid_file = os.path.join(output_dir, 'rsvp_invalid.csv')
    if invalid_records:
        with open(invalid_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rsvp_headers)
            writer.writeheader()
            writer.writerows(invalid_records)
        print(f"Invalid records written to: {invalid_file}")
    
    # Print sample matches for verification
    if matches:
        print("\nSample matched records:")
        for i, match in enumerate(matches[:5]):
            print(f"  {i+1}. {match.get('First Name')} {match.get('Last Name')} - Phone: {match.get('Phone')} - Master ID: {match.get('_master_unique_id')}")
    
    return len(matches), len(new_records), len(invalid_records)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze RSVP data against master prospects')
    parser.add_argument('--master', default='/Users/dannydemichele/Adstv/data lake/MasterProspects.csv',
                        help='Path to MasterProspects.csv')
    parser.add_argument('--rsvp', default='/Users/dannydemichele/Downloads/RSVPmaster.csv',
                        help='Path to RSVPmaster.csv')
    parser.add_argument('--output-dir', default='.',
                        help='Directory for output files')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.master):
        print(f"Error: Master file not found: {args.master}")
        sys.exit(1)
    
    if not os.path.exists(args.rsvp):
        print(f"Error: RSVP file not found: {args.rsvp}")
        sys.exit(1)
    
    analyze_files(args.master, args.rsvp, args.output_dir)

if __name__ == "__main__":
    main() 
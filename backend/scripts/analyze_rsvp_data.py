#!/usr/bin/env python3
"""
Script to analyze RSVP CSV file to understand its structure and content
"""

import csv
import sys
import argparse
from collections import Counter

def analyze_rsvp_file(file_path):
    """Analyze RSVP file structure and content"""
    
    print(f"Analyzing RSVP file: {file_path}")
    print("="*60)
    
    # Counters and tracking
    total_rows = 0
    rows_with_names = 0
    rows_missing_first_name = 0
    rows_missing_last_name = 0
    rows_with_phone = 0
    rows_with_email = 0
    unique_fields = set()
    field_counts = Counter()
    sample_rows = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        
        print(f"\nCSV Headers ({len(headers)} fields):")
        for i, header in enumerate(headers, 1):
            print(f"  {i}. {header}")
        
        for row_num, row in enumerate(reader, start=2):
            total_rows += 1
            
            # Collect sample rows
            if total_rows <= 5:
                sample_rows.append(row)
            
            # Check key fields
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()
            phone = row.get('Phone', '').strip()
            email = row.get('Email', '').strip()
            
            if first_name and last_name:
                rows_with_names += 1
            else:
                if not first_name:
                    rows_missing_first_name += 1
                if not last_name:
                    rows_missing_last_name += 1
                    
            if phone:
                rows_with_phone += 1
            if email:
                rows_with_email += 1
            
            # Count non-empty fields
            for field, value in row.items():
                if value and value.strip():
                    field_counts[field] += 1
                    unique_fields.add(field)
            
            # Show progress
            if total_rows % 1000 == 0:
                print(f"  Processed {total_rows} rows...")
    
    # Print analysis results
    print(f"\n{'='*60}")
    print("ANALYSIS RESULTS")
    print(f"{'='*60}")
    
    print(f"\nTotal rows: {total_rows}")
    print(f"Rows with both first and last name: {rows_with_names}")
    print(f"Rows missing first name: {rows_missing_first_name}")
    print(f"Rows missing last name: {rows_missing_last_name}")
    print(f"Rows with phone: {rows_with_phone}")
    print(f"Rows with email: {rows_with_email}")
    
    print(f"\nField population (non-empty values):")
    for field in headers:
        count = field_counts.get(field, 0)
        percentage = (count / total_rows * 100) if total_rows > 0 else 0
        print(f"  {field}: {count} ({percentage:.1f}%)")
    
    # Show sample rows
    print(f"\n{'='*60}")
    print("SAMPLE ROWS")
    print(f"{'='*60}")
    
    for i, row in enumerate(sample_rows, 1):
        print(f"\nRow {i}:")
        for field, value in row.items():
            if value and value.strip():
                print(f"  {field}: {value}")
    
    # Check for potential issues at the end of file
    if rows_missing_first_name > 100 or rows_missing_last_name > 100:
        print(f"\n{'='*60}")
        print("WARNING: Many rows missing names!")
        print(f"{'='*60}")
        print("This often indicates:")
        print("1. Empty rows at the end of the file")
        print("2. Data quality issues")
        print("3. Different data format in later rows")

def main():
    parser = argparse.ArgumentParser(description='Analyze RSVP CSV file')
    parser.add_argument('--file', required=True, help='Path to the RSVP CSV file')
    
    args = parser.parse_args()
    
    try:
        analyze_rsvp_file(args.file)
    except Exception as e:
        print(f"Error analyzing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
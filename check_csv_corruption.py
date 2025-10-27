#!/usr/bin/env python3
"""Check for CSV corruption issues."""

import pandas as pd
import csv

csv_file = "data/output/dual_engine_results_with_u1_FIXED_20251027_114015_DEDUPLICATED_20251027_114318.csv"

print(f"📊 Analyzing CSV: {csv_file}\n")

try:
    # Try to load with pandas
    df = pd.read_csv(csv_file, low_memory=False)
    print(f"✅ Pandas loaded {len(df)} rows successfully")
    
    # Check item_id column
    print(f"\n🔍 Checking item_id column...")
    
    # Find non-numeric item_ids
    bad_ids = df[~df['item_id'].astype(str).str.match(r'^\d+$|^$', na=False)]
    
    if len(bad_ids) > 0:
        print(f"❌ Found {len(bad_ids)} rows with invalid item_id")
        print(f"\nFirst 3 bad rows:")
        for idx, row in bad_ids.head(3).iterrows():
            print(f"\n  Row {idx}:")
            print(f"    item_id: {str(row['item_id'])[:100]}...")
            print(f"    title: {str(row.get('title', 'N/A'))[:80]}...")
    else:
        print(f"✅ All item_ids are valid")
    
    # Check for rows that might be malformed
    print(f"\n🔍 Checking for malformed rows...")
    print(f"Expected columns: {len(df.columns)}")
    
except Exception as e:
    print(f"❌ Error loading CSV: {e}")
    print(f"\n📝 Trying to read raw CSV...")
    
    # Read raw CSV to find issues
    with open(csv_file, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        headers = next(reader)
        print(f"Headers found: {len(headers)}")
        
        for i, row in enumerate(reader):
            if len(row) != len(headers):
                print(f"\n❌ Row {i+2} has {len(row)} columns, expected {len(headers)}")
                if len(row) > 0:
                    print(f"   First column: {row[0][:100]}...")
                if i > 10:  # Check first 10 problematic rows
                    break

#!/usr/bin/env python3
"""
Remove duplicate rows from CSV based on U1 ID, keeping first occurrence.
"""

import pandas as pd
import sys
from datetime import datetime

def deduplicate_csv(input_csv, output_csv=None):
    """Remove duplicate U1 IDs from CSV, keeping first occurrence."""
    
    print(f"📄 Loading CSV: {input_csv}")
    df = pd.read_csv(input_csv)
    
    original_count = len(df)
    print(f"   Original rows: {original_count:,}")
    
    # Count duplicates
    duplicate_u1s = df[df['item_id'] != ''].groupby('item_id').size()
    duplicates = duplicate_u1s[duplicate_u1s > 1]
    print(f"   Duplicate U1 IDs: {len(duplicates)}")
    print(f"   Total duplicate rows: {sum(duplicates) - len(duplicates)}")
    
    # Remove duplicates, keeping first occurrence
    df_dedup = df.drop_duplicates(subset=['item_id'], keep='first')
    
    final_count = len(df_dedup)
    removed = original_count - final_count
    
    print(f"\n✂️ Deduplication complete:")
    print(f"   Rows removed: {removed:,}")
    print(f"   Final rows: {final_count:,}")
    
    # Generate output filename if not provided
    if not output_csv:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv = input_csv.replace('.csv', f'_DEDUPLICATED_{timestamp}.csv')
    
    # Save
    df_dedup.to_csv(output_csv, index=False, quoting=1, escapechar='\\', doublequote=True)
    
    print(f"\n💾 Saved to: {output_csv}")
    
    return output_csv

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python deduplicate_csv.py <input_csv> [output_csv]")
        print("Example: python deduplicate_csv.py data/output/dual_engine_results_with_u1_FIXED_20251027_114015.csv")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else None
    
    deduplicate_csv(input_csv, output_csv)

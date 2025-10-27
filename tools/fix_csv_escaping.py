#!/usr/bin/env python3
"""
Re-export CSV with better escaping to prevent corruption in Excel/other readers.
"""

import pandas as pd
from datetime import datetime

def fix_csv_escaping(input_csv, output_csv=None):
    """Re-export CSV with proper escaping and quoting."""
    
    print(f"📄 Loading CSV: {input_csv}")
    df = pd.read_csv(input_csv, low_memory=False)
    
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")
    
    # Generate output filename if not provided
    if not output_csv:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv = input_csv.replace('.csv', f'_FIXED_ESCAPING_{timestamp}.csv')
    
    print(f"\n🔧 Re-exporting with improved escaping...")
    
    # Clean any problematic characters
    for col in df.columns:
        if df[col].dtype == 'object':  # String columns
            # Replace problematic characters
            df[col] = df[col].astype(str).str.replace('\x00', '', regex=False)  # Remove null bytes
            df[col] = df[col].str.replace('\r\n', ' ', regex=False)  # Replace CRLF
            df[col] = df[col].str.replace('\r', ' ', regex=False)  # Replace CR
            df[col] = df[col].str.replace('\n', ' ', regex=False)  # Replace LF
            df[col] = df[col].str.replace('\t', ' ', regex=False)  # Replace tabs
            # Normalize whitespace
            df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
    
    # Export with QUOTE_ALL to ensure everything is quoted
    df.to_csv(
        output_csv, 
        index=False, 
        quoting=2,  # QUOTE_NONNUMERIC - quote all non-numeric fields
        encoding='utf-8-sig',  # Add BOM for Excel compatibility
        lineterminator='\n'  # Use Unix line endings
    )
    
    print(f"✅ Fixed CSV saved to: {output_csv}")
    
    # Verify
    print(f"\n🔍 Verifying fixed CSV...")
    df_verify = pd.read_csv(output_csv, low_memory=False)
    
    if len(df_verify) == len(df):
        print(f"✅ Verification passed: {len(df_verify):,} rows")
    else:
        print(f"❌ Verification failed: {len(df_verify):,} rows (expected {len(df):,})")
    
    return output_csv

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fix_csv_escaping.py <input_csv> [output_csv]")
        print("Example: python fix_csv_escaping.py data/output/results.csv")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else None
    
    fix_csv_escaping(input_csv, output_csv)

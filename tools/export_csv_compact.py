#!/usr/bin/env python3
"""
Export CSV without large text fields that cause corruption.
Removes abstract and detailed reasoning columns to ensure CSV stability.
"""

import pandas as pd
import sys
from datetime import datetime

def export_csv_compact(input_csv, output_csv=None):
    """Export CSV without large text fields."""
    
    print(f"📄 Loading CSV: {input_csv}")
    df = pd.read_csv(input_csv, low_memory=False)
    
    print(f"   Original rows: {len(df):,}")
    print(f"   Original columns: {len(df.columns)}")
    
    # Columns to REMOVE (large text fields that cause problems)
    columns_to_remove = [
        'abstract',  # Very long text
        'engine1_reasoning',  # Long reasoning text
        'engine2_reasoning',  # Long reasoning text
        # Keep individual criterion reasoning as they're shorter
    ]
    
    # Also remove detailed criterion reasoning columns (optional)
    criterion_reasoning_cols = [col for col in df.columns if '_reasoning' in col and col not in ['engine1_reasoning', 'engine2_reasoning']]
    
    print(f"\n🗑️ Removing large text columns:")
    removed_cols = []
    for col in columns_to_remove:
        if col in df.columns:
            removed_cols.append(col)
            print(f"   - {col}")
    
    print(f"\n❓ Also remove detailed criterion reasoning? ({len(criterion_reasoning_cols)} columns)")
    print(f"   These are like: engine1_participants_lmic_reasoning, etc.")
    
    # For safety, remove them too
    print(f"   Removing criterion reasoning columns for compact export")
    removed_cols.extend(criterion_reasoning_cols)
    
    # Drop columns
    df_compact = df.drop(columns=removed_cols, errors='ignore')
    
    print(f"\n📊 Compact dataset:")
    print(f"   Rows: {len(df_compact):,}")
    print(f"   Columns: {len(df_compact.columns)} (removed {len(removed_cols)})")
    
    # Generate output filename if not provided
    if not output_csv:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv = input_csv.replace('.csv', f'_COMPACT_{timestamp}.csv')
    
    # Clean remaining text fields
    print(f"\n🧹 Cleaning remaining text fields...")
    for col in df_compact.columns:
        if df_compact[col].dtype == 'object':
            df_compact[col] = df_compact[col].astype(str).str.replace('\x00', '', regex=False)
            df_compact[col] = df_compact[col].str.replace('\r\n', ' ', regex=False)
            df_compact[col] = df_compact[col].str.replace('\r', ' ', regex=False)
            df_compact[col] = df_compact[col].str.replace('\n', ' ', regex=False)
            df_compact[col] = df_compact[col].str.replace('\t', ' ', regex=False)
            df_compact[col] = df_compact[col].str.replace(r'\s+', ' ', regex=True)
    
    # Export with proper escaping
    df_compact.to_csv(
        output_csv,
        index=False,
        quoting=2,  # QUOTE_NONNUMERIC
        encoding='utf-8-sig',
        lineterminator='\n'
    )
    
    print(f"✅ Compact CSV saved: {output_csv}")
    
    # Verify
    print(f"\n🔍 Verifying...")
    df_verify = pd.read_csv(output_csv, low_memory=False)
    
    if len(df_verify) == len(df_compact):
        print(f"✅ Verification passed: {len(df_verify):,} rows")
    else:
        print(f"❌ Verification failed: {len(df_verify):,} rows (expected {len(df_compact):,})")
    
    # Show what's kept
    print(f"\n📋 Columns kept in compact export:")
    essential_cols = ['item_id', 'title', 'year', 'authors', 'journal', 
                      'engine1_decision', 'engine2_decision', 'consensus_decision',
                      'agreement', 'needs_human_review']
    for col in essential_cols:
        if col in df_compact.columns:
            print(f"   ✓ {col}")
    
    print(f"\n💡 TIP: For full details, refer back to JSON results file")
    
    return output_csv

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python export_csv_compact.py <input_csv> [output_csv]")
        print("\nRemoves large text fields (abstract, reasoning) to create stable CSV")
        print("Example: python export_csv_compact.py results.csv")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else None
    
    export_csv_compact(input_csv, output_csv)

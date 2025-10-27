#!/usr/bin/env python3
"""
Quick analysis of input data files to understand structure.
"""

import pandas as pd
import os

print("=" * 60)
print("DATA INVENTORY - Input Files Analysis")
print("=" * 60)

# Excel files to analyze
excel_files = [
    's3above.xlsx',
    's14above.xlsx', 
    's20above.xlsx',
    'program_tags_included.xlsx',
    'program_tags_excluded.xlsx',
    'full_text_marl_constanza_included.xlsx',
    'full_text_marl_constanza_excluded.xlsx',
    'full_text_marl_constanza_maybe.xlsx'
]

print("\n1. EXCEL FILES:")
print("-" * 60)

total_records = 0
for filename in excel_files:
    if os.path.exists(filename):
        df = pd.read_excel(filename)
        print(f"\n📄 {filename}")
        print(f"   Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"   Columns: {', '.join(df.columns.tolist()[:5])}")
        if len(df.columns) > 5:
            print(f"            ... and {len(df.columns) - 5} more")
        
        # Check for include column
        include_cols = [col for col in df.columns if 'include' in col.lower()]
        if include_cols:
            print(f"   ✅ Include column: {include_cols}")
            if len(df) > 0:
                print(f"      Value counts: {df[include_cols[0]].value_counts().to_dict()}")
        
        # Check for program tags
        program_cols = [col for col in df.columns if 'program' in col.lower() or 'tag' in col.lower()]
        if program_cols:
            print(f"   🏷️  Program columns: {program_cols}")
        
        total_records += df.shape[0]
    else:
        print(f"\n❌ {filename} - NOT FOUND")

# Text files
print("\n\n2. TEXT FILES (RIS format):")
print("-" * 60)

text_files = [
    'Not excluded by DEP classifier (n=12,394).txt',
    'Excluded by DEP classifier (n=54,924).txt'
]

for filename in text_files:
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.strip().split('\n')
            
            # Count TY tags (type markers in RIS format)
            ty_count = content.count('\nTY  -')
            
            print(f"\n📄 {filename}")
            print(f"   Total lines: {len(lines):,}")
            print(f"   Estimated records (TY count): {ty_count:,}")
            print(f"   File size: {len(content):,} characters")
            
            total_records += ty_count
    else:
        print(f"\n❌ {filename} - NOT FOUND")

print("\n" + "=" * 60)
print(f"TOTAL RECORDS ACROSS ALL FILES: ~{total_records:,}")
print("=" * 60)

# Sample from s3above
print("\n\n3. SAMPLE DATA (s3above.xlsx - first 2 rows):")
print("-" * 60)
if os.path.exists('s3above.xlsx'):
    df = pd.read_excel('s3above.xlsx')
    print(df.head(2).to_string())

print("\n\n4. DATA SUMMARY BY CATEGORY:")
print("-" * 60)

categories = {
    "Title/Abstract Screened (Human)": ['s3above.xlsx', 's14above.xlsx', 's20above.xlsx'],
    "Program Tags": ['program_tags_included.xlsx', 'program_tags_excluded.xlsx'],
    "Full Text Screened (Human)": [
        'full_text_marl_constanza_included.xlsx',
        'full_text_marl_constanza_excluded.xlsx', 
        'full_text_marl_constanza_maybe.xlsx'
    ],
    "DEP Classifier Output": [
        'Not excluded by DEP classifier (n=12,394).txt',
        'Excluded by DEP classifier (n=54,924).txt'
    ]
}

for category, files in categories.items():
    print(f"\n{category}:")
    cat_total = 0
    for f in files:
        if f.endswith('.xlsx') and os.path.exists(f):
            df = pd.read_excel(f)
            count = df.shape[0]
            print(f"  • {f}: {count:,} records")
            cat_total += count
        elif f.endswith('.txt') and os.path.exists(f):
            with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                count = file.read().count('\nTY  -')
                print(f"  • {f}: ~{count:,} records")
                cat_total += count
    print(f"  Subtotal: {cat_total:,}")

print("\n" + "=" * 60)

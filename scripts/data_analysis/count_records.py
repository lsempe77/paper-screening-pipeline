import pandas as pd

print("="*60)
print("CORRECTED DATA COUNTS")
print("="*60)

files = {
    's3above.xlsx': 'S3+ screened',
    's14above.xlsx': 'S14+ screened',
    's20above.xlsx': 'S20+ screened',
    'program_tags_included.xlsx': 'Program tags (included)',
    'program_tags_excluded.xlsx': 'Program tags (excluded)',
    'full_text_marl_constanza_included.xlsx': 'Full text included',
    'full_text_marl_constanza_excluded.xlsx': 'Full text excluded',
    'full_text_marl_constanza_maybe.xlsx': 'Full text maybe',
}

total = 0
for filename, label in files.items():
    df = pd.read_excel(filename)
    count = len(df)
    print(f"{label:30s}: {count:4d} records")
    total += count

print(f"\n{'Total Excel records':30s}: {total:4d}")

# Check text files
import os
txt_files = [
    'Not excluded by DEP classifier (n=12,394).txt',
    'Excluded by DEP classifier (n=54,924).txt'
]

print("\nText files (RIS format):")
for filename in txt_files:
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            count = content.count('\nTY  -')
            print(f"{filename}: {count:,} records")
            total += count

print(f"\nGRAND TOTAL: {total:,} records")

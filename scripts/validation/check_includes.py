"""Check which papers are labeled as INCLUDE in validation file"""
import pandas as pd

df = pd.read_excel('data/input/s3above.xlsx')
print('Total papers:', len(df))
print('\nUnique label values:')
print(df['include'].value_counts())

print('\n' + '='*80)
print('Papers with "Include" in label:')
includes = df[df['include'].str.contains('Include', na=False)]
print('Count:', len(includes))

print('\n' + '='*80)
print('First 2 INCLUDE papers from validation:')
for idx, row in includes.head(2).iterrows():
    print(f'\n[{idx+1}] ID: {row["ID"]}')
    print(f'    Title: {row["Title"][:100]}...')
    print(f'    Year: {row.get("Year", "N/A")}')
    print(f'    Label: {row["include"]}')

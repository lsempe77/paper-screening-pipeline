import pandas as pd

df = pd.read_csv('scripts/validation/s14_comprehensive_results.csv')

# False positives: LLM=INCLUDE but Human=Excluded
false_positives = df[(df['llm_decision'] == 'INCLUDE') & (df['human_label'] == 'Excluded')]

print('='*80)
print('FALSE POSITIVES (LLM=INCLUDE, Human=Excluded)')
print('='*80)
print(f'\nCount: {len(false_positives)} out of 187 Excluded papers')
print(f'False positive rate: {len(false_positives)/187*100:.1f}%\n')

print('Paper IDs and Titles:')
print('-'*80)
for idx, row in false_positives.iterrows():
    print(f'\n{row["paper_id"]}: {row["title"]}')

# False negatives: LLM=EXCLUDE but Human=Included
false_negatives = df[(df['llm_decision'] == 'EXCLUDE') & (df['human_label'] == 'Included (TA)')]

print('\n' + '='*80)
print('FALSE NEGATIVES (LLM=EXCLUDE, Human=Included)')
print('='*80)
print(f'\nCount: {len(false_negatives)} out of 8 Included papers')
print(f'False negative rate: {len(false_negatives)/8*100:.1f}%\n')

print('Paper IDs and Titles:')
print('-'*80)
for idx, row in false_negatives.iterrows():
    print(f'\n{row["paper_id"]}: {row["title"]}')

# Save false positives IDs
print(f'\n\nFalse positive IDs: {false_positives["paper_id"].tolist()}')
print(f'False negative IDs: {false_negatives["paper_id"].tolist()}')

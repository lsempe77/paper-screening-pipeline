import pandas as pd

df = pd.read_csv('scripts/validation/s14_comprehensive_results.csv')

print('=' * 80)
print('S14 COMPREHENSIVE ANALYSIS SUMMARY')
print('=' * 80)

total = len(df)
print(f'\nTotal papers: {total}')

# False positives and negatives
fp = df[(df['human_label']=='Excluded') & (df['llm_decision'].isin(['INCLUDE','MAYBE']))]
fn = df[(df['human_label'].isin(['Included (TA)','Maybe (TA)'])) & (df['llm_decision']=='EXCLUDE')]

print(f'\nFalse Positives (Human=Excluded, LLM=INCLUDE/MAYBE): {len(fp)} ({len(fp)/total*100:.1f}%)')
print(f'False Negatives (Human=Include/Maybe, LLM=EXCLUDE): {len(fn)}')

print(f'\nFalse Positives breakdown:')
print(f'  LLM=INCLUDE (hard errors): {len(fp[fp["llm_decision"]=="INCLUDE"])}')
print(f'  LLM=MAYBE (uncertain): {len(fp[fp["llm_decision"]=="MAYBE"])}')

# Show the hard false positives (LLM=INCLUDE)
fp_include = fp[fp['llm_decision']=='INCLUDE']
if len(fp_include) > 0:
    print(f'\n{"-" * 80}')
    print('FALSE POSITIVES - LLM INCORRECTLY INCLUDED (LLM=INCLUDE):')
    print('-' * 80)
    for idx, row in fp_include.iterrows():
        print(f'\n{row["paper_id"]}: {row["title"][:70]}')

print(f'\n{"=" * 80}')
print('KEY METRICS:')
print('=' * 80)
print(f'Hard False Positive Rate: {len(fp_include)/total*100:.1f}% ({len(fp_include)}/{total})')
print(f'False Negative Rate: {len(fn)/total*100:.1f}% ({len(fn)}/{total})')
print(f'MAYBE Rate: {len(df[df["llm_decision"]=="MAYBE"])/total*100:.1f}%')

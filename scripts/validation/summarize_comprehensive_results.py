"""
Quick summary of comprehensive s14 analysis results
"""
import pandas as pd
from pathlib import Path

project_dir = Path(__file__).parent.parent.parent
results_file = project_dir / "data" / "output" / "s14_comprehensive_results.csv"

if not results_file.exists():
    print(f"Results file not found: {results_file}")
    exit(1)

df = pd.read_csv(results_file)

print("=" * 80)
print("COMPREHENSIVE S14 ANALYSIS SUMMARY")
print("=" * 80)

# Overall stats
total = len(df)
print(f"\nTotal papers analyzed: {total}")

# Agreement
correct = df[df['correct'] == True]
incorrect = df[df['correct'] == False]

print(f"\nAgreement with human labels:")
print(f"  Correct: {len(correct)} ({len(correct)/total*100:.1f}%)")
print(f"  Incorrect: {len(incorrect)} ({len(incorrect)/total*100:.1f}%)")

# False positives and negatives
fp = df[(df['human_label'] == 'Excluded') & (df['llm_decision'] == 'INCLUDE')]
fn = df[(df['human_label'].isin(['Included (TA)', 'Maybe (TA)'])) & (df['llm_decision'] == 'EXCLUDE')]

print(f"\nError breakdown:")
print(f"  False Positives (LLM=INCLUDE, Human=Excluded): {len(fp)}")
print(f"  False Negatives (LLM=EXCLUDE, Human=Include/Maybe): {len(fn)}")

if len(fp) > 0:
    print(f"\n{'=' * 80}")
    print("FALSE POSITIVES (LLM incorrectly included):")
    print("=" * 80)
    for idx, row in fp.iterrows():
        print(f"\n{row['paper_id']} - {row['short_title']}")
        print(f"  LLM: {row['llm_decision']}")
        print(f"  Human: {row['human_label']}")
        print(f"  Reasoning: {row['decision_reasoning'][:150]}...")

if len(fn) > 0:
    print(f"\n{'=' * 80}")
    print("FALSE NEGATIVES (LLM incorrectly excluded):")
    print("=" * 80)
    for idx, row in fn.iterrows():
        print(f"\n{row['paper_id']} - {row['short_title']}")
        print(f"  LLM: {row['llm_decision']}")
        print(f"  Human: {row['human_label']}")
        print(f"  Reasoning: {row['decision_reasoning'][:150]}...")

print(f"\n{'=' * 80}")
print("Full results saved to:")
print(f"  {results_file}")
print("=" * 80)

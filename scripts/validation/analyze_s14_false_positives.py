"""
Analyze false positives in s14above.xlsx
False positives = LLM says INCLUDE but human says Excluded

This will help us understand if:
1. LLM is being too permissive (false positives - bad)
2. Human labels are incorrect (LLM is actually right)
"""

import sys
from pathlib import Path
import pandas as pd
import yaml

# Add parent directory to path
script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from integrated_screener import IntegratedStructuredScreener
from src.models import Paper, ModelConfig
from src.parsers import RISParser

# Load config
with open(project_dir / 'config' / 'config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Load s14above
print("Loading s14above.xlsx...")
s14_df = pd.read_excel(project_dir / 'data' / 'input' / 's14above.xlsx')
print(f"Total papers: {len(s14_df)}")
print(f"\nLabel distribution:")
print(s14_df['include'].value_counts())

# Find papers where human says "Excluded" but we need to check LLM
excluded_papers = s14_df[s14_df['include'] == 'Excluded']
print(f"\n{len(excluded_papers)} papers labeled 'Excluded' by humans")

# Load corpus to get abstracts
print("\nLoading corpus...")
parser = RISParser()
ris_file = project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
papers = parser.parse_file(str(ris_file))

papers_dict = {}
for p in papers:
    if hasattr(p, 'ris_fields') and 'U1' in p.ris_fields:
        u1 = p.ris_fields['U1']
        paper_id = u1[0] if isinstance(u1, list) else u1
        papers_dict[str(paper_id).strip()] = p

print(f"Loaded {len(papers_dict)} papers from corpus")

# Initialize screener
print("\nInitializing screener...")
model_config = ModelConfig(
    provider="openrouter",
    model_name="anthropic/claude-3-haiku",
    temperature=0.1,
    max_tokens=1000,
    api_key=config['openrouter']['api_key']
)
screener = IntegratedStructuredScreener(model_config)

# Sample some excluded papers to check for false positives
# We'll just take a random sample since there's no DEP score column
import random
random.seed(42)

sample_size = 10
sample_indices = random.sample(range(len(excluded_papers)), min(sample_size, len(excluded_papers)))
sample_papers = excluded_papers.iloc[sample_indices][['ID', 'Title', 'Year']].values

print("\n" + "="*80)
print(f"ANALYZING {len(sample_papers)} RANDOM EXCLUDED PAPERS (checking for false positives)")
print("="*80)

results = []

for paper_id, title, year in sample_papers:
    paper_id_str = str(int(paper_id))
    print(f"\n{'='*80}")
    print(f"Paper ID: {paper_id_str}")
    print(f"Year: {year}")
    print(f"Title: {title[:100]}...")
    
    if paper_id_str not in papers_dict:
        print("⚠️  Paper not found in corpus!")
        continue
    
    paper = papers_dict[paper_id_str]
    abstract_preview = paper.abstract[:200] if paper.abstract else "NO ABSTRACT"
    print(f"Abstract: {abstract_preview}...")
    
    # Screen the paper
    print("\n🤖 Screening with LLM...")
    result = screener.screen_paper(paper)
    
    print(f"\n📊 LLM Decision: {result.final_decision.value.upper()}")
    print(f"Reasoning: {result.decision_reasoning[:200]}...")
    
    # Show criteria breakdown
    criteria_summary = result.get_criteria_summary()
    counts = result.count_criteria_by_status()
    
    print(f"\nCriteria Assessment:")
    print(f"  YES: {counts['YES']}, NO: {counts['NO']}, UNCLEAR: {counts['UNCLEAR']}")
    
    # Show NO criteria specifically
    if counts['NO'] > 0:
        print("\n  Criteria marked NO:")
        if criteria_summary['program_recognition'] == 'NO':
            print(f"    - program_recognition: {result.program_recognition.reasoning[:150]}...")
        if criteria_summary['participants_lmic'] == 'NO':
            print(f"    - participants_lmic: {result.participants_lmic.reasoning[:150]}...")
        if criteria_summary['component_a_cash'] == 'NO':
            print(f"    - cash_support: {result.component_a_cash_support.reasoning[:150]}...")
        if criteria_summary['component_b_assets'] == 'NO':
            print(f"    - productive_assets: {result.component_b_productive_assets.reasoning[:150]}...")
        if criteria_summary['outcomes'] == 'NO':
            print(f"    - relevant_outcomes: {result.relevant_outcomes.reasoning[:150]}...")
        if criteria_summary['study_design'] == 'NO':
            print(f"    - study_design: {result.appropriate_study_design.reasoning[:150]}...")
        if criteria_summary['year_2004_plus'] == 'NO':
            print(f"    - publication_year: {result.publication_year_2004_plus.reasoning[:150]}...")
        if criteria_summary['completed'] == 'NO':
            print(f"    - completed_study: {result.completed_study.reasoning[:150]}...")
    
    # Check if this is a false positive
    is_false_positive = result.final_decision.value == 'include'
    
    results.append({
        'paper_id': paper_id_str,
        'title': title[:100],
        'year': year,
        'human_label': 'Excluded',
        'llm_decision': result.final_decision.value,
        'is_false_positive': is_false_positive,
        'yes_count': counts['YES'],
        'no_count': counts['NO'],
        'unclear_count': counts['UNCLEAR']
    })
    
    if is_false_positive:
        print("\n🚨 FALSE POSITIVE DETECTED!")
        print("   LLM says INCLUDE but human says Excluded")
    else:
        print(f"\n✅ Agreement: Both say {result.final_decision.value.upper()}")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

results_df = pd.DataFrame(results)
print(f"\nTotal papers analyzed: {len(results_df)}")
print(f"False positives (LLM=INCLUDE, Human=Excluded): {results_df['is_false_positive'].sum()}")
print(f"Agreements (both Excluded): {len(results_df) - results_df['is_false_positive'].sum()}")

if results_df['is_false_positive'].sum() > 0:
    print("\n🚨 FALSE POSITIVE PAPERS:")
    fp_df = results_df[results_df['is_false_positive']]
    for idx, row in fp_df.iterrows():
        print(f"\n  Paper {row['paper_id']}:")
        print(f"    Title: {row['title']}")
        print(f"    Year: {row['year']}")
        print(f"    Criteria: {row['yes_count']} YES, {row['no_count']} NO, {row['unclear_count']} UNCLEAR")

# Save results
output_path = project_dir / 'data' / 'output' / 's14_false_positives_analysis.csv'
results_df.to_csv(output_path, index=False)
print(f"\n💾 Results saved to: {output_path}")

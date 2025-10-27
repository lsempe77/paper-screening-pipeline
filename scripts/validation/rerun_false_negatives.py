"""
Re-run comprehensive analysis on just the 4 false negatives from s14above.xlsx
with the updated prompts (outcomes fix + missing abstract handling + Python year assessment).
"""

import sys
from pathlib import Path
import pandas as pd
import yaml
import time

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

# Initialize screener
print("Initializing screener with updated prompts...\n")
model_config = ModelConfig(
    provider="openrouter",
    model_name="anthropic/claude-3-haiku",
    temperature=0.1,
    max_tokens=1000,
    api_key=config['openrouter']['api_key']
)
screener = IntegratedStructuredScreener(model_config)

# Load validation data
s14_path = project_dir / "data" / "input" / "s14above.xlsx"
labels_df = pd.read_excel(s14_path)

# The 4 false negatives
false_negative_ids = [121300172, 121340461, 121360003, 121337938]

# Load corpus
print("Loading corpus...")
parser = RISParser()
ris_file = project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
papers = parser.parse_file(str(ris_file))

papers_dict = {}
for p in papers:
    if hasattr(p, 'ris_fields') and 'U1' in p.ris_fields:
        u1 = p.ris_fields['U1']
        paper_id = u1[0] if isinstance(u1, list) else u1
        papers_dict[str(paper_id).strip()] = p

print(f"Loaded {len(papers_dict)} papers from corpus\n")

# Read updated prompt
with open(project_dir / "prompts" / "structured_screening_with_program_filter.txt", 'r', encoding='utf-8') as f:
    prompt_template = f.read()

# Results storage
results = []

print("=" * 100)
print("COMPREHENSIVE ANALYSIS OF 4 FALSE NEGATIVES")
print("=" * 100)
print()

for i, paper_id in enumerate(false_negative_ids, 1):
    paper_row = labels_df[labels_df['ID'] == paper_id].iloc[0]
    human_label = paper_row.get('include', 'N/A')
    
    print(f"\n{'='*100}")
    print(f"FALSE NEGATIVE #{i}: Paper {paper_id}")
    print(f"{'='*100}")
    print(f"Human Label: {human_label}")
    print(f"Title: {paper_row['Title']}")
    
    # Get paper from corpus
    paper_obj = papers_dict.get(str(paper_id))
    if not paper_obj:
        paper_obj = Paper(
            title=paper_row['Title'],
            abstract="",
            paper_id=str(paper_id)
        )
    
    abstract_length = len(paper_obj.abstract) if paper_obj.abstract else 0
    print(f"Abstract: {'YES (' + str(abstract_length) + ' chars)' if abstract_length > 100 else 'NO or very short'}")
    
    # Screen the paper
    start = time.time()
    result = screener.screen_paper(paper_obj, prompt_template=prompt_template)
    elapsed = time.time() - start
    
    # Extract criteria assessments
    criteria = {
        'program_recognition': result.program_recognition.assessment,
        'participants_lmic': result.participants_lmic.assessment,
        'component_a_cash': result.component_a_cash_support.assessment,
        'component_b_assets': result.component_b_productive_assets.assessment,
        'relevant_outcomes': result.relevant_outcomes.assessment,
        'study_design': result.appropriate_study_design.assessment,
        'year_2004_plus': result.publication_year_2004_plus.assessment,
        'completed_study': result.completed_study.assessment
    }
    
    counts = result.count_criteria_by_status()
    
    print(f"\nCriteria Assessment:")
    for name, assessment in criteria.items():
        print(f"  {name}: {assessment}")
    
    print(f"\nCounts: YES={counts['YES']}, NO={counts['NO']}, UNCLEAR={counts['UNCLEAR']}")
    print(f"Final Decision: {result.final_decision}")
    print(f"Time: {elapsed:.1f}s")
    
    # Store result
    results.append({
        'paper_id': paper_id,
        'human_label': human_label,
        'title': paper_row['Title'][:80],
        'abstract_length': abstract_length,
        'llm_decision': str(result.final_decision).split('.')[-1],
        'yes_count': counts['YES'],
        'no_count': counts['NO'],
        'unclear_count': counts['UNCLEAR'],
        **criteria
    })

print(f"\n{'='*100}")
print("SUMMARY")
print(f"{'='*100}\n")

results_df = pd.DataFrame(results)

# Group by decision
print("Results by LLM Decision:")
decision_summary = results_df.groupby('llm_decision').size()
for decision, count in decision_summary.items():
    print(f"  {decision}: {count}")

print("\n" + "="*100)
print("DETAILED COMPARISON")
print("="*100)

for idx, row in results_df.iterrows():
    print(f"\nPaper {row['paper_id']}:")
    print(f"  Human: {row['human_label']}")
    print(f"  LLM: {row['llm_decision']}")
    print(f"  Counts: YES={row['yes_count']}, NO={row['no_count']}, UNCLEAR={row['unclear_count']}")
    print(f"  Key criteria:")
    print(f"    - Cash: {row['component_a_cash']}")
    print(f"    - Assets: {row['component_b_assets']}")
    print(f"    - Year: {row['year_2004_plus']}")

print("\n" + "="*100)
print("ANALYSIS")
print("="*100)
print("\n1. Papers with NO criteria (should be EXCLUDE):")
for idx, row in results_df[results_df['no_count'] > 0].iterrows():
    print(f"   Paper {row['paper_id']}: {row['no_count']} NO criteria → {row['llm_decision']}")

print("\n2. Papers with 0 NO criteria (should be MAYBE or INCLUDE):")
for idx, row in results_df[results_df['no_count'] == 0].iterrows():
    print(f"   Paper {row['paper_id']}: 0 NO criteria → {row['llm_decision']}")
    if row['abstract_length'] < 100:
        print(f"      (Missing abstract - should be MAYBE)")

print("\n3. Year Assessment (all should be YES with Python):")
for idx, row in results_df.iterrows():
    print(f"   Paper {row['paper_id']}: {row['year_2004_plus']}")

# Save results
output_file = project_dir / "scripts" / "validation" / "false_negatives_reanalysis.csv"
results_df.to_csv(output_file, index=False)
print(f"\n✓ Results saved to: {output_file}")

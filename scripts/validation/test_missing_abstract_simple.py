"""
Simple test: Check how the updated prompt handles Paper 121340461 with missing abstract.
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

# Initialize components
print("Initializing screener...")
model_config = ModelConfig(
    provider="openrouter",
    model_name="anthropic/claude-3-haiku",
    temperature=0.1,
    max_tokens=1000,
    api_key=config['openrouter']['api_key']
)
screener = IntegratedStructuredScreener(model_config)

# Load validation data
print("\nLoading Paper 121340461 from s14above.xlsx...")
s14_path = project_dir / "data" / "input" / "s14above.xlsx"
labels_df = pd.read_excel(s14_path)
paper_row = labels_df[labels_df['ID'] == 121340461].iloc[0]

print(f"\n{'='*80}")
print(f"Paper ID: {paper_row['ID']}")
print(f"Title: {paper_row['Title']}")
print(f"Human Label: {paper_row.get('include', 'N/A')}")
print(f"{'='*80}\n")

# Load corpus to get abstract
print("Loading corpus to check for abstract...")
parser = RISParser()
ris_files = [
    project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
]

all_papers = []
for ris_file in ris_files:
    papers = parser.parse_file(str(ris_file))
    all_papers.extend(papers)

# Find the paper
paper_obj = None
for p in all_papers:
    if p.paper_id == str(121340461):
        paper_obj = p
        break

if paper_obj and paper_obj.abstract:
    print(f"Abstract found: {len(paper_obj.abstract)} chars")
    print(f"Abstract preview: {paper_obj.abstract[:200]}...")
else:
    print("NO ABSTRACT FOUND - Will evaluate from title only")
    if not paper_obj:
        # Create a paper object with empty abstract
        paper_obj = Paper(
            title=paper_row['Title'],
            abstract="",
            paper_id=str(paper_row['ID'])
        )

# Read the updated prompt with missing abstract handling
print(f"\n{'='*80}")
print("Testing with UPDATED PROMPT (includes missing abstract instructions)")
print(f"{'='*80}\n")

with open(project_dir / "prompts" / "structured_screening_with_program_filter.txt", 'r', encoding='utf-8') as f:
    prompt_template = f.read()

# Screen the paper
result = screener.screen_paper(paper_obj, prompt_template=prompt_template)

print("\nCRITERIA ASSESSMENT:")
print(f"0. Program Recognition: {result.program_recognition.assessment}")
print(f"   Reasoning: {result.program_recognition.reasoning}\n")

print(f"1. LMIC: {result.participants_lmic.assessment}")
print(f"   Reasoning: {result.participants_lmic.reasoning}\n")

print(f"2. Cash Support: {result.component_a_cash_support.assessment}")
print(f"   Reasoning: {result.component_a_cash_support.reasoning}\n")

print(f"3. Productive Assets: {result.component_b_productive_assets.assessment}")
print(f"   Reasoning: {result.component_b_productive_assets.reasoning}\n")

print(f"4. Outcomes: {result.relevant_outcomes.assessment}")
print(f"   Reasoning: {result.relevant_outcomes.reasoning}\n")

print(f"5. Study Design: {result.appropriate_study_design.assessment}")
print(f"   Reasoning: {result.appropriate_study_design.reasoning}\n")

print(f"6. Year 2004+: {result.publication_year_2004_plus.assessment}")
print(f"   Reasoning: {result.publication_year_2004_plus.reasoning}\n")

print(f"7. Completed: {result.completed_study.assessment}")
print(f"   Reasoning: {result.completed_study.reasoning}\n")

print(f"{'='*80}")
print(f"FINAL DECISION: {result.final_decision}")
print(f"Decision Reasoning: {result.decision_reasoning}")
print(f"{'='*80}\n")

counts = result.count_criteria_by_status()
print(f"Summary:")
print(f"  YES: {counts['YES']}/8")
print(f"  NO: {counts['NO']}/8")
print(f"  UNCLEAR: {counts['UNCLEAR']}/8")

print(f"\n✓ EXPECTED: With missing abstract and poverty-related title:")
print(f"  - Should use UNCLEAR (not NO) for criteria that can't be assessed from title")
print(f"  - Should result in MAYBE decision (pass to full-text screening)")
print(f"  - Title mentions 'poverty' + 'Nigeria' so should be generous with inclusion")

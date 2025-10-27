"""
Test the updated year extraction logic.
Paper 121340461 should now correctly identify year 2007 >= 2004.
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
print("Testing updated year extraction logic\n")
model_config = ModelConfig(
    provider="openrouter",
    model_name="anthropic/claude-3-haiku",
    temperature=0.1,
    max_tokens=1000,
    api_key=config['openrouter']['api_key']
)
screener = IntegratedStructuredScreener(model_config)

# Load Paper 121340461
s14_path = project_dir / "data" / "input" / "s14above.xlsx"
labels_df = pd.read_excel(s14_path)
paper_row = labels_df[labels_df['ID'] == 121340461].iloc[0]

# Load from corpus
parser = RISParser()
ris_file = project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
papers = parser.parse_file(str(ris_file))

papers_dict = {}
for p in papers:
    if hasattr(p, 'ris_fields') and 'U1' in p.ris_fields:
        u1 = p.ris_fields['U1']
        paper_id = u1[0] if isinstance(u1, list) else u1
        papers_dict[str(paper_id).strip()] = p

paper_obj = papers_dict.get(str(121340461))

if not paper_obj:
    paper_obj = Paper(
        title=paper_row['Title'],
        abstract="",
        paper_id=str(121340461),
        year=2007  # Known year
    )

print(f"Paper ID: {paper_obj.paper_id}")
print(f"Title: {paper_obj.title}")
print(f"Year in Paper object: {paper_obj.year if hasattr(paper_obj, 'year') else 'N/A'}")
print(f"Abstract: {'YES' if paper_obj.abstract else 'NO (title only)'}\n")

# Read updated prompt
with open(project_dir / "prompts" / "structured_screening_with_program_filter.txt", 'r', encoding='utf-8') as f:
    prompt_template = f.read()

print("=" * 80)
print("LLM EVALUATION WITH UPDATED YEAR LOGIC")
print("=" * 80)
print()

result = screener.screen_paper(paper_obj, prompt_template=prompt_template)

print(f"6. Publication Year: {result.publication_year_2004_plus.assessment}")
print(f"   Reasoning: {result.publication_year_2004_plus.reasoning}\n")

print(f"Final Decision: {result.final_decision}")
print(f"Decision Reasoning: {result.decision_reasoning}\n")

counts = result.count_criteria_by_status()
print(f"Summary: YES={counts['YES']}, NO={counts['NO']}, UNCLEAR={counts['UNCLEAR']}")

print("\n" + "=" * 80)
if result.publication_year_2004_plus.assessment == 'YES':
    print("✅ SUCCESS: Year correctly identified as >= 2004")
elif result.publication_year_2004_plus.assessment == 'NO':
    print("❌ FAILED: Year incorrectly marked as < 2004")
else:
    print("⚠️  UNCLEAR: Year not found/extracted")
print("=" * 80)

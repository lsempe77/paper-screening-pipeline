"""
Review all 4 false negatives from s14above with full details:
- Abstract
- Human evaluation
- LLM criterion-by-criterion assessment
- Final decision
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
print("Initializing screener...\n")
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

# False negatives identified earlier
false_negative_ids = [121300172, 121340461, 121360003, 121337938]

# Load corpus
print("Loading corpus...")
parser = RISParser()
ris_files = [
    project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
]

all_papers = {}
for ris_file in ris_files:
    papers = parser.parse_file(str(ris_file))
    for p in papers:
        if hasattr(p, 'ris_fields') and 'U1' in p.ris_fields:
            u1 = p.ris_fields['U1']
            paper_id = u1[0] if isinstance(u1, list) else u1
            all_papers[str(paper_id).strip()] = p

print(f"Loaded {len(all_papers)} papers from corpus\n")

# Read the updated prompt
with open(project_dir / "prompts" / "structured_screening_with_program_filter.txt", 'r', encoding='utf-8') as f:
    prompt_template = f.read()

# Process each false negative
for i, paper_id in enumerate(false_negative_ids, 1):
    print("=" * 100)
    print(f"FALSE NEGATIVE #{i}: Paper {paper_id}")
    print("=" * 100)
    
    # Get human label
    paper_row = labels_df[labels_df['ID'] == paper_id].iloc[0]
    human_label = paper_row.get('include', 'N/A')
    
    print(f"\n📋 TITLE:")
    print(f"   {paper_row['Title']}")
    
    print(f"\n👤 HUMAN EVALUATION: {human_label}")
    
    # Get paper from corpus
    paper_obj = all_papers.get(str(paper_id))
    
    if not paper_obj:
        # Create paper with empty abstract if not found
        paper_obj = Paper(
            title=paper_row['Title'],
            abstract="",
            paper_id=str(paper_id)
        )
    
    # Print abstract
    print(f"\n📄 ABSTRACT:")
    if paper_obj.abstract:
        print(f"   Length: {len(paper_obj.abstract)} characters")
        print(f"   {paper_obj.abstract}")
    else:
        print("   [NO ABSTRACT AVAILABLE]")
    
    # Screen the paper with LLM
    print(f"\n🤖 LLM EVALUATION:")
    print(f"   (Using updated prompt with outcomes fix + missing abstract handling)\n")
    
    result = screener.screen_paper(paper_obj, prompt_template=prompt_template)
    
    # Print criterion by criterion
    print(f"   0. Program Recognition: {result.program_recognition.assessment}")
    print(f"      └─ {result.program_recognition.reasoning}\n")
    
    print(f"   1. LMIC Participants: {result.participants_lmic.assessment}")
    print(f"      └─ {result.participants_lmic.reasoning}\n")
    
    print(f"   2. Cash/Consumption Support: {result.component_a_cash_support.assessment}")
    print(f"      └─ {result.component_a_cash_support.reasoning}\n")
    
    print(f"   3. Productive Assets: {result.component_b_productive_assets.assessment}")
    print(f"      └─ {result.component_b_productive_assets.reasoning}\n")
    
    print(f"   4. Relevant Outcomes: {result.relevant_outcomes.assessment}")
    print(f"      └─ {result.relevant_outcomes.reasoning}\n")
    
    print(f"   5. Study Design: {result.appropriate_study_design.assessment}")
    print(f"      └─ {result.appropriate_study_design.reasoning}\n")
    
    print(f"   6. Publication Year 2004+: {result.publication_year_2004_plus.assessment}")
    print(f"      └─ {result.publication_year_2004_plus.reasoning}\n")
    
    print(f"   7. Completed Study: {result.completed_study.assessment}")
    print(f"      └─ {result.completed_study.reasoning}\n")
    
    # Summary counts
    counts = result.count_criteria_by_status()
    print(f"   SUMMARY: YES={counts['YES']}, NO={counts['NO']}, UNCLEAR={counts['UNCLEAR']}")
    
    # Final decision
    print(f"\n✅ FINAL DECISION: {result.final_decision}")
    print(f"   Reasoning: {result.decision_reasoning}")
    
    print(f"\n{'=' * 100}\n")

print("\n" + "=" * 100)
print("REVIEW COMPLETE")
print("=" * 100)
print("\nKey Question: Do the updated prompt changes (outcomes + missing abstract handling)")
print("affect the LLM's decisions on these false negatives?")
print("\nExpected:")
print("  - Paper 121340461 (no abstract) → Should now be MAYBE instead of EXCLUDE")
print("  - Others → May remain EXCLUDE if they still fail strict criteria")

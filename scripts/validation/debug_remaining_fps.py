"""
Debug the 2 remaining false positives (SCTP and LEAP)
Show what's in abstracts and what LLM is assessing
"""
import sys
from pathlib import Path

script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

import pandas as pd
from integrated_screener import IntegratedStructuredScreener
from src.models import ModelConfig
from src.parsers import RISParser
import yaml
import json

# Load config
with open(project_dir / 'config' / 'config.yaml', 'r') as f:
    config_dict = yaml.safe_load(f)
config = ModelConfig.from_dict(config_dict)

# Load prompt
with open(project_dir / 'prompts' / 'structured_screening_criteria_optimized.txt', 'r') as f:
    prompt_template = f.read()

# Load corpus
parser = RISParser()
ris_files = [
    project_dir / "data" / "input" / "Excluded by DEP classifier (n=54,924).txt",
    project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
]

corpus_lookup = {}
for ris_file in ris_files:
    if ris_file.exists():
        papers = parser.parse_file(str(ris_file))
        for paper in papers:
            if hasattr(paper, 'ris_fields') and 'U1' in paper.ris_fields:
                paper_ids = paper.ris_fields['U1']
                if isinstance(paper_ids, list):
                    paper_id = paper_ids[0] if paper_ids else None
                else:
                    paper_id = paper_ids
                
                if paper_id:
                    corpus_lookup[str(paper_id)] = paper

# Test papers
test_papers = {
    '121296063': 'Malawi SCTP',
    '121328933': 'Ghana LEAP'
}

screener = IntegratedStructuredScreener(config)

for paper_id, name in test_papers.items():
    print("=" * 80)
    print(f"PAPER: {name} ({paper_id})")
    print("=" * 80)
    
    paper = corpus_lookup.get(paper_id)
    if not paper:
        print("Paper not found!")
        continue
    
    print(f"\nTitle: {paper.title}")
    print(f"\nAbstract (first 500 chars):")
    print(paper.abstract[:500] + "...")
    
    # Screen paper
    result = screener.screen_paper(paper, prompt_template=prompt_template)
    
    # Extract criteria assessments
    print("\n" + "-" * 80)
    print("LLM ASSESSMENTS:")
    print("-" * 80)
    
    # The result object has attributes we can access
    if hasattr(result, 'raw_criteria'):
        criteria = result.raw_criteria
        
        # Show key criteria
        prog_recog = criteria.get('program_recognition', {})
        comp_a = criteria.get('component_a_cash_support', {})
        comp_b = criteria.get('component_b_productive_assets', {})
        study_design = criteria.get('appropriate_study_design', {})
        
        print(f"\nProgram Recognition: {prog_recog.get('assessment', 'N/A')}")
        print(f"  Reasoning: {prog_recog.get('reasoning', 'N/A')[:200]}")
        
        print(f"\nComponent A (Cash): {comp_a.get('assessment', 'N/A')}")
        print(f"  Reasoning: {comp_a.get('reasoning', 'N/A')[:200]}")
        
        print(f"\nComponent B (Assets): {comp_b.get('assessment', 'N/A')}")
        print(f"  Reasoning: {comp_b.get('reasoning', 'N/A')[:300]}")
        
        print(f"\nStudy Design: {study_design.get('assessment', 'N/A')}")
        print(f"  Reasoning: {study_design.get('reasoning', 'N/A')[:300]}")
        
        # Count YES
        yes_count = sum(1 for c in criteria.values() if isinstance(c, dict) and c.get('assessment') == 'YES')
        print(f"\nTotal YES criteria: {yes_count}/7")
    
    # Show final decision
    decision_str = str(result.final_decision.value) if hasattr(result.final_decision, 'value') else str(result.final_decision)
    print(f"\n" + "-" * 80)
    print(f"FINAL DECISION: {decision_str}")
    print(f"Reasoning: {result.decision_reasoning[:300]}")
    print("\n")

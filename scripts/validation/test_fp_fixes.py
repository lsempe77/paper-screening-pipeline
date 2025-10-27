"""
Test the updated prompt on the 5 false positives
"""
import sys
from pathlib import Path

script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from integrated_screener import IntegratedStructuredScreener
from src.models import ModelConfig
from src.parsers import RISParser
import yaml

# The 5 false positives
test_cases = {
    121296063: {
        "name": "Malawi SCTP",
        "expected": "EXCLUDE",
        "reason": "Measures asset outcomes, doesn't provide assets"
    },
    121308863: {
        "name": "Tribal Sub-Plan Review",
        "expected": "EXCLUDE",
        "reason": "Review paper: 'This paper review on...'"
    },
    121328933: {
        "name": "Ghana LEAP comparison",
        "expected": "MAYBE or EXCLUDE",
        "reason": "Comparative analysis, argues skills > cash"
    },
    121328658: {
        "name": "PES Burkina Faso",
        "expected": "EXCLUDE",
        "reason": "Cash only (environmental payments), no assets"
    },
    121337599: {
        "name": "Nigeria NEEDS",
        "expected": "EXCLUDE",
        "reason": "Policy analysis/critique, not impact evaluation"
    }
}

# Load config
config_path = project_dir / "config" / "config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

model_config = ModelConfig(
    provider="openrouter",
    model_name=config['models']['primary']['model_name'],
    api_url=config['openrouter']['api_url'],
    api_key=config['openrouter']['api_key'],
    temperature=0.0,
    max_tokens=4000
)

screener = IntegratedStructuredScreener(
    model_config=model_config,
    use_program_filter=True
)

# Load prompt
prompt_path = project_dir / 'prompts' / 'structured_screening_with_program_filter.txt'
with open(prompt_path, 'r', encoding='utf-8') as f:
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

print("=" * 80)
print("TESTING UPDATED PROMPT ON 5 FALSE POSITIVES")
print("=" * 80)

for paper_id, test_info in test_cases.items():
    print(f"\n{'=' * 80}")
    print(f"Testing: {test_info['name']} ({paper_id})")
    print(f"Expected: {test_info['expected']}")
    print(f"Reason: {test_info['reason']}")
    print("=" * 80)
    
    paper = corpus_lookup.get(str(paper_id))
    if not paper:
        print(f"Paper not found in corpus!")
        continue
    
    # Screen paper
    result = screener.screen_paper(paper, prompt_template=prompt_template)
    
    decision_str = str(result.final_decision.value) if hasattr(result.final_decision, 'value') else str(result.final_decision)
    decision_str = decision_str.upper()
    
    print(f"\nDecision: {decision_str}", end="")
    if decision_str == test_info['expected'] or (test_info['expected'] == "MAYBE or EXCLUDE" and decision_str in ["MAYBE", "EXCLUDE"]):
        print(" [CORRECT]")
    else:
        print(f" [WRONG]")
    
    print(f"Reasoning: {result.decision_reasoning[:300]}...")

print(f"\n{'=' * 80}")
print("TEST COMPLETE")
print("=" * 80)

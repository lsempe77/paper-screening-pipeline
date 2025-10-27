"""
Test if strict list matching fixes the false Program Recognition YES
for Malawi SCTP and Pakistan BISP
"""

import sys
from pathlib import Path

script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from integrated_screener import IntegratedStructuredScreener
from src.models import ModelConfig
from src.parsers import RISParser

def test_program_recognition():
    # Load config
    import yaml
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
                    u1_value = paper.ris_fields['U1']
                    pid = u1_value[0] if isinstance(u1_value, list) else u1_value
                    corpus_lookup[str(pid).strip()] = paper
    
    print("Testing strict list matching for Program Recognition\n")
    print("="*80)
    
    test_cases = [
        {'id': '121296063', 'name': 'Malawi SCTP', 'expected_prog': 'UNCLEAR'},
        {'id': '121299285', 'name': 'Pakistan BISP', 'expected_prog': 'UNCLEAR'},
    ]
    
    for case in test_cases:
        paper = corpus_lookup.get(case['id'])
        if not paper:
            print(f"❌ Paper {case['id']} not found!")
            continue
        
        print(f"\n{'='*80}")
        print(f"Testing: {case['name']} ({case['id']})")
        print(f"Expected Program Recognition: {case['expected_prog']}")
        print(f"{'='*80}")
        
        result = screener.screen_paper(paper)
        
        prog_recog = result.program_recognition.assessment
        prog_reason = result.program_recognition.reasoning
        final_decision = str(result.final_decision).split('.')[-1]
        
        correct = (prog_recog == case['expected_prog'])
        status = "✅ CORRECT" if correct else "❌ WRONG"
        
        print(f"\nProgram Recognition: {prog_recog} {status}")
        print(f"Reasoning: {prog_reason}")
        print(f"\nFinal Decision: {final_decision}")
        print(f"Decision Reasoning: {result.decision_reasoning[:200]}...")
        
        # Check assets
        print(f"\nProductive Assets: {result.component_b_productive_assets.assessment}")
        print(f"Assets Reasoning: {result.component_b_productive_assets.reasoning[:200]}...")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_program_recognition()

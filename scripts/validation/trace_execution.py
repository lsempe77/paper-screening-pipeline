"""
Trace execution flow for one false positive to see exactly what's happening
"""
import sys
from pathlib import Path

script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

import pandas as pd
from integrated_screener import IntegratedStructuredScreener
from src.models import ModelConfig
import yaml

def trace_sctp():
    """Trace SCTP screening - the one where Python matching works but assets confused"""
    
    # Load paper
    corpus = pd.read_excel('data/input/corpus.xlsx')
    paper_data = corpus[corpus['id'] == 121296063].iloc[0]
    
    paper_dict = {
        'id': int(paper_data['id']),
        'title': str(paper_data['title']),
        'abstract': str(paper_data['abstract'])
    }
    
    print("="*80)
    print(f"TRACING: {paper_dict['title'][:80]}")
    print("="*80)
    print(f"\nAbstract (first 300 chars):\n{paper_dict['abstract'][:300]}...")
    
    # Screen the paper with config
    with open('config/config.yaml', 'r') as f:
        config_dict = yaml.safe_load(f)
    config = ModelConfig.from_dict(config_dict)
    
    screener = IntegratedStructuredScreener(config)
    result = screener.screen_paper(paper_dict)
    
    print("\n" + "="*80)
    print("LLM RESPONSE STRUCTURE")
    print("="*80)
    print(f"Response type: {type(result)}")
    print(f"Top-level keys: {list(result.keys())}")
    
    # Check if followup structure
    if 'first_pass' in result:
        print("\nThis is a FOLLOWUP response")
        print(f"First pass length: {len(result['first_pass'])} chars")
        print(f"Followup keys: {list(result.get('followup', {}).keys())}")
    else:
        print("\nThis is a SIMPLE response")
    
    # Check program recognition
    criteria = result.get('criteria_evaluation', {})
    prog_recog = criteria.get('program_recognition', {})
    
    print("\n" + "="*80)
    print("PROGRAM RECOGNITION")
    print("="*80)
    print(f"Assessment: {prog_recog.get('assessment', 'NOT FOUND')}")
    print(f"Reasoning: {prog_recog.get('reasoning', 'NOT FOUND')[:200]}")
    
    # Check Component B
    comp_b = criteria.get('component_b_productive_assets', {})
    
    print("\n" + "="*80)
    print("COMPONENT B - PRODUCTIVE ASSETS")
    print("="*80)
    print(f"Assessment: {comp_b.get('assessment', 'NOT FOUND')}")
    print(f"Reasoning: {comp_b.get('reasoning', 'NOT FOUND')[:300]}")
    
    # Count YES criteria
    yes_count = sum(1 for c in criteria.values() if isinstance(c, dict) and c.get('assessment') == 'YES')
    print(f"\nTotal YES criteria: {yes_count}/7")
    
    # Show decision
    print("\n" + "="*80)
    print("FINAL DECISION")
    print("="*80)
    print(f"Decision: {result.get('decision', 'NOT FOUND')}")
    print(f"Reasoning: {result.get('reasoning', 'NOT FOUND')[:300]}")

if __name__ == "__main__":
    trace_sctp()

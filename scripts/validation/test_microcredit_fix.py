"""
Test the microcredit fix on the 8 false positives from s14 comprehensive analysis
This should correctly identify 6 papers as EXCLUDE and 2 as INCLUDE
"""

import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from integrated_screener import IntegratedStructuredScreener
from src.models import Paper, ModelConfig
from src.parsers import RISParser

def load_corpus():
    """Load corpus to get abstracts"""
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
                    paper_id = u1_value[0] if isinstance(u1_value, list) else u1_value
                    corpus_lookup[str(paper_id).strip()] = paper
    
    return corpus_lookup

def test_microcredit_fix():
    """Test the microcredit fix on 8 false positive papers"""
    
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
        temperature=config['models']['primary'].get('temperature', 0.0),
        max_tokens=config['models']['primary'].get('max_tokens', 4000)
    )
    
    screener = IntegratedStructuredScreener(
        model_config=model_config,
        use_program_filter=True
    )
    print("✓ Screener initialized with UPDATED prompt (microcredit fix)\n")
    
    # Load corpus
    print("Loading corpus...")
    corpus_lookup = load_corpus()
    print(f"✓ Loaded {len(corpus_lookup)} papers\n")
    
    # The 8 false positive paper IDs with their expected outcomes after fix
    test_cases = [
        # Should remain INCLUDE (legitimate cash transfer programs)
        {'id': '121296063', 'name': 'Malawi SCTP', 'expected': 'INCLUDE'},
        {'id': '121299285', 'name': 'Pakistan BISP', 'expected': 'INCLUDE'},
        
        # Should become EXCLUDE (microfinance only)
        {'id': '121323669', 'name': 'PRSP microcredit (2004)', 'expected': 'EXCLUDE'},
        {'id': '121323321', 'name': 'PRSP microcredit (2005)', 'expected': 'EXCLUDE'},
        {'id': '121308119', 'name': 'Egyptian SFD (2009)', 'expected': 'EXCLUDE'},
        {'id': '121295210', 'name': 'Egyptian SFD duplicate', 'expected': 'EXCLUDE'},
        {'id': '121304324', 'name': 'Fadama Nigeria', 'expected': 'EXCLUDE'},
        
        # Should become EXCLUDE (review paper)
        {'id': '121295197', 'name': 'CCT Latin America review', 'expected': 'EXCLUDE'},
    ]
    
    print("="*80)
    print("TESTING MICROCREDIT FIX ON 8 FALSE POSITIVES")
    print("="*80)
    
    results = []
    correct = 0
    
    for idx, test_case in enumerate(test_cases, 1):
        paper_id = test_case['id']
        paper = corpus_lookup.get(paper_id)
        
        if not paper:
            print(f"\n❌ Paper {paper_id} not found in corpus!")
            continue
        
        print(f"\n{idx}. Testing {paper_id}: {test_case['name']}")
        print(f"   Abstract length: {len(paper.abstract)} chars")
        print(f"   Expected: {test_case['expected']}")
        
        # Screen the paper
        result = screener.screen_paper(paper)
        llm_decision = str(result.final_decision).split('.')[-1]
        
        # Check if correct
        is_correct = (llm_decision == test_case['expected'])
        correct += is_correct
        
        status = "✅ CORRECT" if is_correct else "❌ WRONG"
        print(f"   LLM Decision: {llm_decision} {status}")
        
        # Show relevant criteria
        if hasattr(result, 'component_a_cash_support'):
            print(f"   Cash support: {result.component_a_cash_support.assessment}")
            if result.component_a_cash_support.reasoning:
                # Show first 150 chars of reasoning
                reasoning = result.component_a_cash_support.reasoning[:150]
                print(f"   Reasoning: {reasoning}...")
        
        results.append({
            'paper_id': paper_id,
            'name': test_case['name'],
            'expected': test_case['expected'],
            'llm_decision': llm_decision,
            'correct': is_correct,
            'cash_assessment': result.component_a_cash_support.assessment if hasattr(result, 'component_a_cash_support') else 'N/A',
            'cash_reasoning': result.component_a_cash_support.reasoning if hasattr(result, 'component_a_cash_support') else 'N/A'
        })
    
    # Summary
    print("\n" + "="*80)
    print(f"SUMMARY: {correct}/{len(test_cases)} correct ({100*correct/len(test_cases):.1f}%)")
    print("="*80)
    
    # Show which ones are still wrong
    wrong = [r for r in results if not r['correct']]
    if wrong:
        print(f"\n❌ Still incorrect ({len(wrong)} papers):")
        for r in wrong:
            print(f"   - {r['paper_id']}: {r['name']}")
            print(f"     Expected {r['expected']}, got {r['llm_decision']}")
            print(f"     Cash: {r['cash_assessment']}")
            print(f"     Reasoning: {r['cash_reasoning'][:100]}...")
            print()
    else:
        print("\n✅ All papers correctly classified!")
    
    # Save results
    results_df = pd.DataFrame(results)
    output_file = script_dir / "microcredit_fix_test_results.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\n✓ Results saved to: {output_file}")

if __name__ == "__main__":
    test_microcredit_fix()

"""
Test that synthesis/review papers are now correctly excluded
"""
import sys
import os
from pathlib import Path

script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

import pandas as pd
from integrated_screener import IntegratedStructuredScreener
from src.models import Paper, ModelConfig
from src.parsers import RISParser
import yaml

# Paper IDs to test
test_papers = {
    121295197: {
        "name": "CCT Latin America Review",
        "expected_design": "NO",
        "expected_decision": "EXCLUDE",
        "reason": "Synthesis paper reviewing multiple CCT programs"
    }
}

def test_synthesis_exclusion():
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
    
    # Load s14above data
    df = pd.read_excel(project_dir / 'data' / 'input' / 's14above.xlsx')
    
    # Initialize screener
    screener = IntegratedStructuredScreener(
        model_config=model_config,
        use_program_filter=True
    )
    
    # Load prompt
    prompt_path = project_dir / 'prompts' / 'structured_screening_with_program_filter.txt'
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    # Load corpus from RIS files
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
                    # U1 field can be a list, take first ID
                    if isinstance(paper_ids, list):
                        paper_id = paper_ids[0] if paper_ids else None
                    else:
                        paper_id = paper_ids
                    
                    if paper_id:
                        corpus_lookup[str(paper_id)] = paper
    
    print("Testing Synthesis Paper Exclusion")
    print("=" * 80)
    
    for paper_id, test_info in test_papers.items():
        print(f"\n{'=' * 80}")
        print(f"Testing: {test_info['name']} ({paper_id})")
        print(f"Expected Study Design: {test_info['expected_design']}")
        print(f"Reason: {test_info['reason']}")
        print("=" * 80)
        
        # Get paper from corpus
        paper = corpus_lookup.get(str(paper_id))
        if not paper:
            print(f"❌ Paper {paper_id} not found in corpus!")
            continue
        
        # Screen paper
        result = screener.screen_paper(paper, prompt_template=prompt_template)
        
        # Print raw response for debugging
        print(f"\n=== RAW LLM RESPONSE ===")
        print(result.raw_response[:1000])
        print("=== END RAW RESPONSE ===\n")
        
        # Extract study design assessment
        import json
        try:
            response_data = json.loads(result.raw_response)
            criteria_eval = response_data.get('criteria_evaluation', {})
            study_design = criteria_eval.get('study_design', {})
            
            design_assessment = study_design.get('assessment', 'NOT FOUND')
            design_reasoning = study_design.get('reasoning', 'NOT FOUND')
            
            print(f"\nStudy Design Assessment: {design_assessment}", end="")
            if design_assessment == test_info['expected_design']:
                print(" [CORRECT]")
            else:
                print(f" [WRONG - expected {test_info['expected_design']}]")
            
            print(f"Design Reasoning: {design_reasoning[:200]}...")
            
        except Exception as e:
            print(f"Error parsing response: {e}")
            design_assessment = "ERROR"
        
        # Check final decision
        decision_str = str(result.final_decision.value) if hasattr(result.final_decision, 'value') else str(result.final_decision)
        decision_str = decision_str.upper()  # Normalize to uppercase
        expected_decision = test_info['expected_decision'].upper()
        
        print(f"\nFinal Decision: {decision_str}", end="")
        if decision_str == expected_decision:
            print(" [CORRECT]")
        else:
            print(f" [WRONG - expected {expected_decision}]")
        
        reasoning_clean = result.decision_reasoning.encode('ascii', 'ignore').decode('ascii')
        print(f"Decision Reasoning: {reasoning_clean[:200]}...")
        
        # Check if study design was marked NO
        if 'appropriate_study_design' in reasoning_clean or 'Study design' in reasoning_clean:
            print("\n[SUCCESS] Study design criterion was used in decision logic!")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    test_synthesis_exclusion()

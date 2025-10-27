"""
Debug why papers with NO cash support still get INCLUDE
Check what other criteria are triggering inclusion
"""

import sys
from pathlib import Path

# Add parent directory to path
script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from integrated_screener import IntegratedStructuredScreener
from src.models import Paper, ModelConfig
from src.parsers import RISParser

def debug_paper(paper_id, name):
    """Debug a single paper's screening"""
    
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
    
    paper = corpus_lookup.get(paper_id)
    if not paper:
        print(f"Paper {paper_id} not found!")
        return
    
    print(f"\n{'='*80}")
    print(f"DEBUGGING: {paper_id} - {name}")
    print(f"{'='*80}")
    print(f"\nTitle: {paper.title}")
    print(f"Abstract length: {len(paper.abstract)} chars")
    print(f"\nAbstract preview:")
    print(paper.abstract[:500])
    print("...\n")
    
    # Screen the paper
    result = screener.screen_paper(paper)
    
    print(f"FINAL DECISION: {result.final_decision}")
    print(f"\nDecision Reasoning: {result.decision_reasoning}")
    
    print(f"\n{'='*80}")
    print("ALL CRITERIA:")
    print(f"{'='*80}")
    print(f"0. Program Recognition: {result.program_recognition.assessment}")
    print(f"   → {result.program_recognition.reasoning[:150]}...")
    print(f"\n1. LMIC: {result.participants_lmic.assessment}")
    print(f"   → {result.participants_lmic.reasoning[:150]}...")
    print(f"\n2. Cash Support: {result.component_a_cash_support.assessment}")
    print(f"   → {result.component_a_cash_support.reasoning[:200]}...")
    print(f"\n3. Productive Assets: {result.component_b_productive_assets.assessment}")
    print(f"   → {result.component_b_productive_assets.reasoning[:150]}...")
    print(f"\n4. Outcomes: {result.relevant_outcomes.assessment}")
    print(f"   → {result.relevant_outcomes.reasoning[:150]}...")
    print(f"\n5. Study Design: {result.appropriate_study_design.assessment}")
    print(f"   → {result.appropriate_study_design.reasoning[:150]}...")
    print(f"\n6. Year: {result.publication_year_2004_plus.assessment}")
    print(f"   → {result.publication_year_2004_plus.reasoning[:150]}...")
    print(f"\n7. Completed: {result.completed_study.assessment}")
    print(f"   → {result.completed_study.reasoning[:150]}...")

if __name__ == "__main__":
    # Debug the problematic papers
    print("\n" + "="*80)
    print("DEBUGGING PAPERS WITH NO CASH SUPPORT BUT STILL INCLUDED")
    print("="*80)
    
    debug_paper('121323321', 'PRSP microcredit (2005)')
    debug_paper('121295210', 'Egyptian SFD duplicate')
    debug_paper('121304324', 'Fadama Nigeria')

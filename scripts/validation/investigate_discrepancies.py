"""
Investigate the 5 false positives and 1 false negative from s14 comprehensive analysis
Retrieve full abstracts and detailed LLM reasoning for each paper
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
                    pid = u1_value[0] if isinstance(u1_value, list) else u1_value
                    corpus_lookup[str(pid).strip()] = paper
    
    return corpus_lookup

def investigate_paper(paper_id, name, corpus_lookup, screener):
    """Investigate a single paper in detail"""
    
    paper = corpus_lookup.get(paper_id)
    if not paper:
        print(f"\n❌ Paper {paper_id} not found in corpus!")
        return
    
    print(f"\n{'='*100}")
    print(f"PAPER {paper_id}: {name}")
    print(f"{'='*100}")
    print(f"\n📄 Title: {paper.title}")
    print(f"📏 Abstract length: {len(paper.abstract)} chars")
    print(f"\n📝 ABSTRACT:")
    print("-" * 100)
    print(paper.abstract)
    print("-" * 100)
    
    # Screen the paper
    print(f"\n🤖 LLM SCREENING RESULT:")
    print("-" * 100)
    result = screener.screen_paper(paper)
    
    print(f"\n✅ FINAL DECISION: {result.final_decision}")
    print(f"📋 Decision Reasoning: {result.decision_reasoning}")
    
    print(f"\n📊 ALL CRITERIA ASSESSMENTS:")
    print("-" * 100)
    
    criteria = [
        ('program_recognition', 'Program Recognition'),
        ('participants_lmic', 'LMIC Participants'),
        ('component_a_cash_support', 'Cash Support'),
        ('component_b_productive_assets', 'Productive Assets'),
        ('relevant_outcomes', 'Relevant Outcomes'),
        ('appropriate_study_design', 'Study Design'),
        ('publication_year_2004_plus', 'Year 2004+'),
        ('completed_study', 'Completed Study')
    ]
    
    for attr_name, display_name in criteria:
        if hasattr(result, attr_name):
            criterion = getattr(result, attr_name)
            print(f"\n{display_name}: {criterion.assessment}")
            print(f"  → {criterion.reasoning}")

def main():
    """Investigate all 6 discrepancy papers"""
    
    # Initialize screener
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
    print("✓ Screener initialized\n")
    
    # Load corpus
    print("Loading corpus...")
    corpus_lookup = load_corpus()
    print(f"✓ Loaded {len(corpus_lookup)} papers\n")
    
    # Papers to investigate
    false_positives = [
        {'id': '121296063', 'name': 'Malawi SCTP'},
        {'id': '121299285', 'name': 'Pakistan BISP'},
        {'id': '121310791', 'name': 'Gaza CCT'},
        {'id': '121295197', 'name': 'CCT Latin America Review'},
        {'id': '121328933', 'name': 'Ghana Cash Transfers'},
    ]
    
    false_negatives = [
        {'id': '121354173', 'name': 'Ethiopia Livelihood Study'},
    ]
    
    print("\n" + "="*100)
    print("INVESTIGATING 5 FALSE POSITIVES (LLM=INCLUDE, Human=Excluded)")
    print("="*100)
    
    for paper_info in false_positives:
        investigate_paper(paper_info['id'], paper_info['name'], corpus_lookup, screener)
    
    print("\n\n" + "="*100)
    print("INVESTIGATING 1 FALSE NEGATIVE (LLM=EXCLUDE, Human=Included)")
    print("="*100)
    
    for paper_info in false_negatives:
        investigate_paper(paper_info['id'], paper_info['name'], corpus_lookup, screener)
    
    print("\n\n" + "="*100)
    print("INVESTIGATION COMPLETE")
    print("="*100)

if __name__ == "__main__":
    main()

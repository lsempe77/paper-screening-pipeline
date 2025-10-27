"""
Detailed analysis of false positive cases from s14above.xlsx
Cases where Human: Excluded but LLM: INCLUDE/MAYBE
Total: 28 false positives identified in comprehensive analysis
"""

import sys
from pathlib import Path
import pandas as pd
import time

# Add parent directory to path
script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from integrated_screener import IntegratedStructuredScreener
from src.models import Paper, ModelConfig
from src.parsers import RISParser

def analyze_false_positives():
    """Analyze false positive cases in detail"""
    
    print("="*80)
    print("ANALYZING FALSE POSITIVE CASES")
    print("="*80)
    
    # Load the validation data
    s14_path = project_dir / "data" / "input" / "s14above.xlsx"
    labels_df = pd.read_excel(s14_path)
    
    # Load corpus to get abstracts
    print(f"Loading corpus for abstracts...")
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
    
    # Initialize screener
    print(f"Initializing LLM screener...")
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
    
    # Find excluded papers that might be false positives
    excluded_papers = labels_df[labels_df['include'] == 'Excluded']
    print(f"Found {len(excluded_papers)} papers labeled as 'Excluded' by humans")
    
    false_positives = []
    
    print(f"\nScreening first 10 excluded papers to find false positives...")
    
    for idx, (_, row) in enumerate(excluded_papers.head(10).iterrows()):
        paper_id = str(row['ID'])
        print(f"\n--- Paper {idx+1}/10: ID {paper_id} ---")
        print(f"Title: {row['Title'][:80]}...")
        
        # Get paper with abstract if available
        corpus_paper = corpus_lookup.get(paper_id)
        if corpus_paper:
            test_paper = corpus_paper
            print(f"Abstract: {len(corpus_paper.abstract)} chars")
        else:
            test_paper = Paper(
                paper_id=paper_id,
                title=str(row['Title']),
                abstract="No abstract available",
                authors=[],
                year=row.get('Year', 2020),
                journal="",
                doi="",
                source_file="s14above.xlsx"
            )
            print(f"Abstract: Not available")
        
        try:
            result = screener.screen_paper(test_paper)
            llm_decision = result.final_decision
            
            print(f"Human: Excluded | LLM: {llm_decision}")
            
            # Check if this is a false positive
            if llm_decision.name in ['INCLUDE', 'MAYBE']:
                print(f"⚠️  FALSE POSITIVE DETECTED!")
                
                false_positive_info = {
                    'paper_id': paper_id,
                    'title': row['Title'],
                    'human_label': 'Excluded',
                    'llm_decision': llm_decision.name,
                    'program_recognition': result.program_recognition.assessment,
                    'program_reasoning': result.program_recognition.reasoning,
                    'decision_reasoning': result.decision_reasoning,
                    'abstract_length': len(test_paper.abstract),
                    'criteria_summary': {
                        'participants_lmic': result.participants_lmic.assessment,
                        'cash_support': result.component_a_cash_support.assessment,
                        'productive_assets': result.component_b_productive_assets.assessment,
                        'relevant_outcomes': result.relevant_outcomes.assessment,
                        'study_design': result.appropriate_study_design.assessment,
                        'publication_year': result.publication_year_2004_plus.assessment,
                        'completed_study': result.completed_study.assessment
                    }
                }
                false_positives.append(false_positive_info)
                
                # Show detailed breakdown for first few false positives
                if len(false_positives) <= 3:
                    print(f"\n   📊 DETAILED BREAKDOWN:")
                    print(f"   Program: {result.program_recognition.assessment} - {result.program_recognition.reasoning[:60]}...")
                    print(f"   Cash Support: {result.component_a_cash_support.assessment}")
                    print(f"   Assets: {result.component_b_productive_assets.assessment}")
                    print(f"   Reasoning: {result.decision_reasoning}")
            else:
                print(f"✅ Correctly classified as {llm_decision}")
                
        except Exception as e:
            print(f"❌ Error screening paper: {e}")
    
    # Analyze patterns in false positives
    print(f"\n" + "="*80)
    print(f"FALSE POSITIVE ANALYSIS")
    print(f"="*80)
    
    if false_positives:
        print(f"\nFound {len(false_positives)} false positives in sample:")
        
        # Analyze by LLM decision type
        include_fps = [fp for fp in false_positives if fp['llm_decision'] == 'INCLUDE']
        maybe_fps = [fp for fp in false_positives if fp['llm_decision'] == 'MAYBE']
        
        print(f"  - INCLUDE false positives: {len(include_fps)}")
        print(f"  - MAYBE false positives: {len(maybe_fps)}")
        
        # Analyze by program recognition
        program_yes = [fp for fp in false_positives if fp['program_recognition'] == 'YES']
        program_unclear = [fp for fp in false_positives if fp['program_recognition'] == 'UNCLEAR']
        program_no = [fp for fp in false_positives if fp['program_recognition'] == 'NO']
        
        print(f"\nProgram Recognition Distribution:")
        print(f"  - YES: {len(program_yes)} (known relevant programs)")
        print(f"  - UNCLEAR: {len(program_unclear)} (unknown programs)")  
        print(f"  - NO: {len(program_no)} (known irrelevant programs)")
        
        # Show program recognition details for INCLUDE false positives
        if include_fps:
            print(f"\n🔍 INCLUDE False Positives (most concerning):")
            for fp in include_fps:
                print(f"  ID: {fp['paper_id']}")
                print(f"    Title: {fp['title'][:60]}...")
                print(f"    Program: {fp['program_recognition']} - {fp['program_reasoning'][:60]}...")
                print(f"    Decision: {fp['decision_reasoning'][:60]}...")
                print()
        
        # Analyze criteria patterns
        print(f"\n📈 CRITERIA PATTERNS IN FALSE POSITIVES:")
        criteria_counts = {}
        for criterion in ['participants_lmic', 'cash_support', 'productive_assets', 'relevant_outcomes', 'study_design', 'publication_year', 'completed_study']:
            yes_count = sum(1 for fp in false_positives if fp['criteria_summary'][criterion] == 'YES')
            no_count = sum(1 for fp in false_positives if fp['criteria_summary'][criterion] == 'NO')
            unclear_count = sum(1 for fp in false_positives if fp['criteria_summary'][criterion] == 'UNCLEAR')
            print(f"  {criterion:20}: YES={yes_count:2d} | NO={no_count:2d} | UNCLEAR={unclear_count:2d}")
        
        print(f"\n💡 POTENTIAL ISSUES:")
        if len(program_yes) > 0:
            print(f"  1. {len(program_yes)} false positives are about 'known relevant programs' - may need to review program lists")
        if len(maybe_fps) > len(include_fps):
            print(f"  2. More MAYBE than INCLUDE false positives - conservative uncertainty might be appropriate")
        if len(include_fps) > 0:
            print(f"  3. {len(include_fps)} INCLUDE false positives need investigation - these are confident wrong decisions")
            
    else:
        print(f"\n✅ No false positives found in sample of 10 papers!")
        print(f"   This suggests the comprehensive analysis false positives might be from:")
        print(f"   - Different papers in the full dataset")
        print(f"   - Edge cases or papers with specific characteristics")
    
    return false_positives

def analyze_specific_false_positive_ids():
    """Analyze the specific false positive IDs mentioned in the comprehensive analysis"""
    
    print(f"\n" + "="*80)
    print(f"ANALYZING SPECIFIC FALSE POSITIVES FROM COMPREHENSIVE ANALYSIS")
    print(f"="*80)
    
    # These are the IDs mentioned in the comprehensive analysis output
    known_fp_ids = [
        "121295867",  # Rural Finance And Agricultural Technology Adoption In Ethiopia
        "121315839",  # Rwanda's potential to achieve the Millennium Development Goals
        "121303690",  # An empirical study on the influence of Islamic values in poverty alleviation
        "121296063",  # Evaluating The Effectiveness Of An Unconditional Social Cash Transfer Programme (INCLUDE)
        "121298980",  # Does conservation agriculture technology reduce farm household poverty
    ]
    
    # Load the validation data
    s14_path = project_dir / "data" / "input" / "s14above.xlsx"
    labels_df = pd.read_excel(s14_path)
    
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
                    paper_id = u1_value[0] if isinstance(u1_value, list) else u1_value
                    corpus_lookup[str(paper_id).strip()] = paper
    
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
    
    print(f"Analyzing {len(known_fp_ids)} specific false positive cases...")
    
    for idx, fp_id in enumerate(known_fp_ids):
        print(f"\n--- FALSE POSITIVE {idx+1}/{len(known_fp_ids)}: ID {fp_id} ---")
        
        # Find in validation data
        target_row = labels_df[labels_df['ID'].astype(str) == fp_id]
        if target_row.empty:
            print(f"❌ ID {fp_id} not found in validation data")
            continue
            
        row = target_row.iloc[0]
        print(f"Title: {row['Title']}")
        print(f"Human Label: {row['include']}")
        
        # Get paper with abstract
        corpus_paper = corpus_lookup.get(fp_id)
        if corpus_paper:
            test_paper = corpus_paper
            print(f"Abstract: {len(corpus_paper.abstract)} chars")
        else:
            test_paper = Paper(
                paper_id=fp_id,
                title=str(row['Title']),
                abstract="",
                authors=[],
                year=row.get('Year', 2020),
                journal="",
                doi="",
                source_file="s14above.xlsx"
            )
            print(f"Abstract: Not available")
        
        try:
            result = screener.screen_paper(test_paper)
            
            print(f"\nLLM Decision: {result.final_decision}")
            print(f"Program Recognition: {result.program_recognition.assessment}")
            print(f"Program Reasoning: {result.program_recognition.reasoning}")
            print(f"Decision Reasoning: {result.decision_reasoning}")
            
            # Show criteria that led to INCLUDE/MAYBE
            criteria = [
                ("Participants LMIC", result.participants_lmic),
                ("Cash Support", result.component_a_cash_support),
                ("Productive Assets", result.component_b_productive_assets),
                ("Outcomes", result.relevant_outcomes),
                ("Study Design", result.appropriate_study_design),
                ("Year", result.publication_year_2004_plus),
                ("Completed", result.completed_study)
            ]
            
            print(f"\nCriteria Breakdown:")
            yes_criteria = []
            for name, assessment in criteria:
                status = "✅" if assessment.assessment == "YES" else "❌" if assessment.assessment == "NO" else "❓"
                print(f"  {name}: {status} {assessment.assessment}")
                if assessment.assessment == "YES":
                    yes_criteria.append(name)
            
            print(f"\nWhy this might be a false positive:")
            if result.final_decision.name == "INCLUDE":
                if result.program_recognition.assessment == "YES":
                    print(f"  - Program recognized as relevant, triggered automatic INCLUDE")
                else:
                    print(f"  - Met sufficient criteria for INCLUDE: {', '.join(yes_criteria)}")
            elif result.final_decision.name == "MAYBE":
                print(f"  - Conservative MAYBE decision due to uncertainty")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    # First analyze a sample to understand patterns
    sample_fps = analyze_false_positives()
    
    # Then analyze specific known false positives
    analyze_specific_false_positive_ids()
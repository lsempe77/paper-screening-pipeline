"""
Investigate the 3 false negative cases from s20above.xlsx analysis
Cases where Human: Included but LLM: EXCLUDE

False Negatives identified:
1. ID: 121378353 - Social assistance and adaptation to flooding in Bangladesh
2. ID: 121326700 - Sustainable Poverty Reduction through Social Assistance: Modality, Context, and ...  
3. ID: 121295397 - The effects of poverty reduction policy on health services utilization among the...
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

def investigate_false_negatives():
    """Analyze the 3 false negative cases in detail"""
    
    print("="*80)
    print("INVESTIGATING 3 FALSE NEGATIVE CASES FROM s20above.xlsx")
    print("="*80)
    
    # IDs of the false negative papers
    false_negative_ids = [
        '121378353',  # Social assistance and adaptation to flooding in Bangladesh
        '121326700',  # Sustainable Poverty Reduction through Social Assistance
        '121295397'   # The effects of poverty reduction policy on health services utilization
    ]
    
    # Load the validation data
    s20_path = project_dir / "data" / "input" / "s20above.xlsx"
    labels_df = pd.read_excel(s20_path)
    
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
            print(f"  Loading {ris_file.name}...")
            papers = parser.parse_file(str(ris_file))
            for paper in papers:
                # U1 field contains the numeric ID
                if hasattr(paper, 'ris_fields') and 'U1' in paper.ris_fields:
                    u1_value = paper.ris_fields['U1']
                    paper_id = u1_value[0] if isinstance(u1_value, list) else u1_value
                    corpus_lookup[str(paper_id).strip()] = paper
    
    print(f"\nAnalyzing {len(false_negative_ids)} false negative cases:")
    print("-" * 80)
    
    # Initialize screener
    config_path = project_dir / "config" / "config.yaml"
    import yaml
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
    
    for i, paper_id in enumerate(false_negative_ids, 1):
        print(f"\n" + "="*80)
        print(f"FALSE NEGATIVE CASE {i}: Paper ID {paper_id}")
        print("="*80)
        
        # Get paper info from validation set
        paper_row = labels_df[labels_df['ID'] == int(paper_id)]
        if paper_row.empty:
            print(f"❌ Paper {paper_id} not found in validation set")
            continue
        
        paper_info = paper_row.iloc[0]
        
        print(f"📋 VALIDATION DATA:")
        print(f"   Title: {paper_info['Title']}")
        print(f"   Human Label: {paper_info['include']}")
        print(f"   Year: {paper_info.get('Year', 'N/A')}")
        
        # Get abstract from corpus
        corpus_paper = corpus_lookup.get(paper_id)
        if corpus_paper:
            print(f"\n📄 ABSTRACT ({len(corpus_paper.abstract)} chars):")
            print(f"   {corpus_paper.abstract[:500]}...")
            if len(corpus_paper.abstract) > 500:
                print(f"   [...{len(corpus_paper.abstract)-500} more characters...]")
            
            # Screen the paper again for detailed analysis
            print(f"\n🤖 LLM SCREENING ANALYSIS:")
            result = screener.screen_paper(corpus_paper)
            
            print(f"   Final Decision: {result.final_decision}")
            print(f"   Program Recognition: {result.program_recognition if hasattr(result, 'program_recognition') else 'N/A'}")
            
            if hasattr(result, 'decision_reasoning'):
                print(f"\n📝 DETAILED REASONING:")
                print(f"   {result.decision_reasoning}")
            
            if hasattr(result, 'criteria_assessment'):
                print(f"\n⚖️ CRITERIA ASSESSMENT:")
                criteria = result.criteria_assessment
                if hasattr(criteria, '__dict__'):
                    for key, value in criteria.__dict__.items():
                        if not key.startswith('_'):
                            print(f"   {key}: {value}")
            
        else:
            print(f"❌ Abstract not found in corpus for paper {paper_id}")
        
        print(f"\n🔍 ANALYSIS:")
        print(f"   This paper was labeled as '{paper_info['include']}' by humans")
        print(f"   but the LLM classified it as 'EXCLUDE'")
        print(f"   Key question: Should this paper actually be included in a systematic review")
        print(f"   of cash + productive assets interventions?")
        
        # Manual analysis prompts
        print(f"\n❓ INVESTIGATION QUESTIONS:")
        print(f"   1. Does the intervention provide both cash transfers AND productive assets?")
        print(f"   2. Is this an impact evaluation (not just descriptive/analytical)?")
        print(f"   3. Are participants from LMIC countries?")
        print(f"   4. Does it measure relevant outcomes?")
        print(f"   5. Could this be a human labeling error?")

def main():
    investigate_false_negatives()
    
    print(f"\n" + "="*80)
    print("INVESTIGATION COMPLETE")
    print("="*80)
    print("\nRecommendations:")
    print("1. Review each abstract against screening criteria")
    print("2. Check if papers truly meet 'cash + assets' requirement") 
    print("3. Verify these are impact evaluations, not descriptive studies")
    print("4. Consider if human labels should be corrected")
    print("5. If corrections needed, create correction script like s3above/s14above")

if __name__ == "__main__":
    main()
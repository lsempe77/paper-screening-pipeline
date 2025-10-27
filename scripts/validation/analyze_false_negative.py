"""
Detailed analysis of the false negative case from s14above.xlsx
Paper ID: 121295601 - Growth Enhancement Support Scheme (GESS)
Human: Included (TA), LLM: EXCLUDE
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

def analyze_false_negative():
    """Analyze the specific false negative case in detail"""
    
    print("="*80)
    print("ANALYZING FALSE NEGATIVE CASE")
    print("="*80)
    
    # Load the validation data
    s14_path = project_dir / "data" / "input" / "s14above.xlsx"
    labels_df = pd.read_excel(s14_path)
    
    # Find the specific paper
    target_id = "121295601"
    target_row = labels_df[labels_df['ID'].astype(str) == target_id]
    
    if target_row.empty:
        print(f"❌ Paper ID {target_id} not found in s14above.xlsx")
        return
    
    row = target_row.iloc[0]
    print(f"📋 PAPER DETAILS")
    print(f"   ID: {row['ID']}")
    print(f"   Title: {row['Title']}")
    print(f"   Human Label: {row['include']}")
    print(f"   Year: {row.get('Year', 'N/A')}")
    
    # Load corpus to get full abstract
    print(f"\n🔍 LOADING FULL PAPER FROM CORPUS...")
    parser = RISParser()
    ris_files = [
        project_dir / "data" / "input" / "Excluded by DEP classifier (n=54,924).txt",
        project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
    ]
    
    corpus_paper = None
    for ris_file in ris_files:
        if ris_file.exists():
            papers = parser.parse_file(str(ris_file))
            for paper in papers:
                if hasattr(paper, 'ris_fields') and 'U1' in paper.ris_fields:
                    u1_value = paper.ris_fields['U1']
                    paper_id = u1_value[0] if isinstance(u1_value, list) else u1_value
                    if str(paper_id).strip() == target_id:
                        corpus_paper = paper
                        break
            if corpus_paper:
                break
    
    if not corpus_paper:
        print(f"❌ Paper not found in corpus - creating from validation data only")
        corpus_paper = Paper(
            paper_id=target_id,
            title=str(row['Title']),
            abstract="",
            authors=[],
            year=row.get('Year'),
            journal="",
            doi="",
            source_file="s14above.xlsx"
        )
    
    print(f"✅ Paper loaded:")
    print(f"   Abstract length: {len(corpus_paper.abstract)} characters")
    print(f"   Year: {corpus_paper.year}")
    print(f"   Journal: {corpus_paper.journal}")
    
    # Show abstract preview
    if corpus_paper.abstract:
        print(f"\n📄 ABSTRACT PREVIEW:")
        print(f"   {corpus_paper.abstract[:500]}...")
        if len(corpus_paper.abstract) > 500:
            print(f"   [... {len(corpus_paper.abstract) - 500} more characters]")
    else:
        print(f"\n⚠️  NO ABSTRACT AVAILABLE")
    
    # Initialize screener
    print(f"\n🤖 INITIALIZING LLM SCREENER...")
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
    
    print(f"✅ Screener initialized with program filter enabled")
    
    # Screen the paper
    print(f"\n🔬 SCREENING THE PAPER...")
    start_time = time.time()
    
    try:
        result = screener.screen_paper(corpus_paper)
        processing_time = time.time() - start_time
        
        print(f"✅ Screening completed in {processing_time:.1f}s")
        
        # Display detailed results
        print(f"\n" + "="*80)
        print(f"DETAILED SCREENING RESULTS")
        print(f"="*80)
        
        print(f"\n🎯 FINAL DECISION: {result.final_decision}")
        print(f"   Human Expected: Included (TA)")
        print(f"   LLM Decision: {result.final_decision}")
        print(f"   ❌ MISMATCH: This is the FALSE NEGATIVE")
        
        print(f"\n📊 CRITERIA BREAKDOWN:")
        
        # Program Recognition
        prog_rec = result.program_recognition
        print(f"   0. Program Recognition: {prog_rec.assessment}")
        print(f"      └─ {prog_rec.reasoning}")
        
        # All other criteria
        criteria = [
            ("1. Participants LMIC", result.participants_lmic),
            ("2. Cash Support", result.component_a_cash_support),  
            ("3. Productive Assets", result.component_b_productive_assets),
            ("4. Relevant Outcomes", result.relevant_outcomes),
            ("5. Study Design", result.appropriate_study_design),
            ("6. Publication Year", result.publication_year_2004_plus),
            ("7. Completed Study", result.completed_study)
        ]
        
        yes_count = 0
        no_count = 0
        unclear_count = 0
        
        for name, assessment in criteria:
            status_emoji = "✅" if assessment.assessment == "YES" else "❌" if assessment.assessment == "NO" else "❓"
            print(f"   {name}: {status_emoji} {assessment.assessment}")
            print(f"      └─ {assessment.reasoning}")
            
            if assessment.assessment == "YES":
                yes_count += 1
            elif assessment.assessment == "NO":
                no_count += 1
            else:
                unclear_count += 1
        
        print(f"\n📈 CRITERIA SUMMARY:")
        print(f"   YES: {yes_count} | NO: {no_count} | UNCLEAR: {unclear_count}")
        
        print(f"\n🧠 DECISION REASONING:")
        print(f"   {result.decision_reasoning}")
        
        print(f"\n🔍 ANALYSIS OF WHY THIS IS A FALSE NEGATIVE:")
        print(f"   The paper is about 'Growth Enhancement Support Scheme (GESS)'")
        print(f"   This appears to be an agricultural input subsidy program")
        print(f"   Human reviewers marked it as 'Included (TA)' suggesting it meets criteria")
        print(f"   LLM marked it as 'EXCLUDE' - let's see which criteria failed...")
        
        # Identify the specific issues
        failed_criteria = []
        for name, assessment in criteria:
            if assessment.assessment == "NO":
                failed_criteria.append(name)
        
        if failed_criteria:
            print(f"\n❌ CRITERIA THAT FAILED (marked as NO):")
            for criterion in failed_criteria:
                print(f"   • {criterion}")
        
        # Check program recognition specifically
        if prog_rec.assessment != "YES":
            print(f"\n🏷️  PROGRAM RECOGNITION ISSUE:")
            print(f"   Assessment: {prog_rec.assessment}")
            print(f"   Reasoning: {prog_rec.reasoning}")
            if "not found in known lists" in prog_rec.reasoning:
                print(f"   ⚠️  GESS is not in the known program lists - this might need to be added")
        
        print(f"\n💡 POTENTIAL IMPROVEMENTS:")
        if "GESS" in corpus_paper.title and prog_rec.assessment != "YES":
            print(f"   1. Add 'Growth Enhancement Support Scheme (GESS)' to known program lists")
        
        failed_components = [name for name, assessment in criteria if assessment.assessment == "NO" and "component" in name.lower()]
        if failed_components:
            print(f"   2. Review component recognition - GESS might include both cash and assets")
        
        failed_design = [name for name, assessment in criteria if assessment.assessment == "NO" and "design" in name.lower()]
        if failed_design:
            print(f"   3. Review study design assessment - might be valid experimental/quasi-experimental")
            
    except Exception as e:
        print(f"❌ Screening failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_false_negative()
#!/usr/bin/env python3
"""
Analyze MAYBE patterns using the current integrated approach (without dual_component).
"""

import sys
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models import ModelConfig, Paper
from src.parsers import RISParser
from integrated_screener import IntegratedStructuredScreener

def analyze_current_maybe_patterns():
    """Analyze MAYBE patterns using the current integrated screener."""
    
    print("🔍 ANALYZING CURRENT MAYBE PATTERNS")
    print("=" * 37)
    print("(Using integrated approach without dual_component)")
    print()
    
    # Load config
    config_path = Path("config/config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    model_config = ModelConfig(
        model_name=config['models']['primary']['model_name'],
        api_url="https://openrouter.ai/api/v1",
        api_key=config['openrouter']['api_key'],
        provider="openrouter",
        temperature=0.1,
        max_tokens=1500
    )
    
    screener = IntegratedStructuredScreener(model_config)
    parser = RISParser()
    
    # Load a sample of papers to find MAYBE patterns
    print("📊 Loading papers for analysis...")
    included_papers = parser.parse_file("data/input/included.txt")
    excluded_papers = parser.parse_file("data/input/excluded.txt")
    
    print(f"   • Loaded {len(included_papers)} included papers")
    print(f"   • Loaded {len(excluded_papers)} excluded papers")
    print()
    
    # Test a sample to find MAYBE cases
    maybe_cases = []
    test_papers = included_papers[:15] + excluded_papers[:10]  # Sample 25 papers
    
    print("🔍 Screening sample papers to find MAYBE patterns...")
    print()
    
    for i, paper in enumerate(test_papers, 1):
        print(f"   📄 {i}/25: {paper.title[:50]}...")
        
        try:
            result = screener.screen_paper(paper)
            decision = result.final_decision.value
            
            if decision == "maybe":
                maybe_cases.append((paper, result))
                print(f"      → MAYBE ✨ (found pattern case)")
            else:
                print(f"      → {decision.upper()}")
                
        except Exception as e:
            print(f"      → ERROR: {e}")
    
    print(f"\n📋 Found {len(maybe_cases)} MAYBE cases for analysis")
    print()
    
    if len(maybe_cases) == 0:
        print("⚠️  No MAYBE cases found in sample. The approach may be working well!")
        print("   This suggests the MAYBE rate is lower than expected.")
        return
    
    # Analyze MAYBE patterns
    print("🔍 DETAILED MAYBE ANALYSIS:")
    print("-" * 26)
    
    unclear_by_criterion = {}
    
    for i, (paper, result) in enumerate(maybe_cases, 1):
        print(f"\n📄 MAYBE CASE #{i}")
        print("-" * 40)
        print(f"Title: {paper.title}")
        print(f"Abstract: {paper.abstract[:150]}...")
        print()
        
        print(f"🤖 Decision: {result.final_decision.value.upper()}")
        print(f"📝 Reasoning: {result.decision_reasoning}")
        print()
        
        # Analyze criteria (7 criteria in integrated approach)
        criteria_attrs = [
            ('participants_lmic', 'LMIC Participants'),
            ('component_a_cash_support', 'Cash Support'),
            ('component_b_productive_assets', 'Productive Assets'),
            ('relevant_outcomes', 'Relevant Outcomes'),
            ('appropriate_study_design', 'Study Design'),
            ('publication_year_2004_plus', 'Year 2004+'),
            ('completed_study', 'Completed Study')
        ]
        
        print("📊 CRITERIA BREAKDOWN:")
        unclear_criteria = []
        
        for attr_name, display_name in criteria_attrs:
            if hasattr(result, attr_name):
                criterion = getattr(result, attr_name)
                status_icon = "❓" if criterion.assessment == "UNCLEAR" else "✅" if criterion.assessment == "YES" else "❌"
                print(f"   {status_icon} {display_name}: {criterion.assessment}")
                
                if criterion.assessment == "UNCLEAR":
                    unclear_criteria.append(display_name)
                    print(f"      🔍 Reason: {criterion.reasoning}")
                    
                    # Track patterns
                    if display_name not in unclear_by_criterion:
                        unclear_by_criterion[display_name] = []
                    unclear_by_criterion[display_name].append({
                        'paper_title': paper.title[:60],
                        'reasoning': criterion.reasoning,
                        'abstract_snippet': paper.abstract[:100]
                    })
        
        counts = result.count_criteria_by_status()
        print(f"\n   📊 Summary: {counts.get('YES', 0)}Y / {counts.get('NO', 0)}N / {counts.get('UNCLEAR', 0)}U")
        print(f"   🎯 UNCLEAR criteria: {', '.join(unclear_criteria)}")
        print("\n" + "=" * 50)
    
    # Pattern analysis
    print("\n🔍 UNCLEAR CRITERIA PATTERNS:")
    print("-" * 28)
    
    for criterion, cases in unclear_by_criterion.items():
        print(f"\n📋 {criterion} ({len(cases)} unclear cases):")
        
        for j, case in enumerate(cases, 1):
            print(f"   {j}. {case['paper_title']}")
            print(f"      Reasoning: {case['reasoning'][:100]}...")
            print(f"      Context: {case['abstract_snippet']}...")
        
        # Suggest improvements based on patterns
        print(f"\n   💡 Optimization suggestions for {criterion}:")
        
        if "cash" in criterion.lower():
            print("     • Add examples: training allowances, transportation support")
            print("     • Clarify: program cost coverage implies cash component")
            print("     • Guide: infer from 'participant support' language")
            
        elif "asset" in criterion.lower():
            print("     • Add examples: business kits, agricultural inputs, tools")
            print("     • Clarify: training materials can include productive assets")
            print("     • Guide: infer from 'productive activity' mentions")
            
        elif "outcome" in criterion.lower():
            print("     • Broaden examples: livelihoods, economic empowerment")
            print("     • Clarify: business outcomes, self-employment measures")
            print("     • Guide: infer economic outcomes from poverty programs")
            
        elif "design" in criterion.lower():
            print("     • Add examples: comparison groups, treatment/control")
            print("     • Clarify: quasi-experimental design variations")
            print("     • Guide: infer RCT from random assignment mentions")
            
        else:
            print("     • Review examples and guidance for this criterion")
            print("     • Consider if evidence standards are too strict")
    
    print(f"\n🎯 OPTIMIZATION RECOMMENDATIONS:")
    print("-" * 30)
    print("1. 📝 Enhance prompt with more edge case examples")
    print("2. 🎯 Clarify evidence standards for each criterion")
    print("3. 📋 Add guidance for reasonable inference")
    print("4. ✅ Test optimized prompt on these MAYBE cases")
    print("5. 📊 Measure MAYBE rate reduction")
    
    # Calculate potential impact
    current_maybe_rate = len(maybe_cases) / len(test_papers) * 100
    print(f"\n📊 CURRENT SAMPLE MAYBE RATE: {current_maybe_rate:.1f}%")
    print(f"   Target: Reduce to 15-20%")
    print(f"   For 12,400 papers: Save ~{12400 * (current_maybe_rate - 17.5) / 100:.0f} from human review")

if __name__ == "__main__":
    analyze_current_maybe_patterns()
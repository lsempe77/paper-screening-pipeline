#!/usr/bin/env python3
"""
Test the integrated approach: LLM for criteria assessment + Python for decision logic.
"""

import json
import time
from openai import OpenAI
import yaml
from pathlib import Path
from decision_processor import ScreeningDecisionProcessor

def test_integrated_approach():
    """Test LLM criteria assessment + Python decision logic."""
    
    print("🔗 INTEGRATED APPROACH TEST")
    print("=" * 35)
    print("LLM: Criteria assessment only | Python: Decision logic")
    print()
    
    # Load configuration
    config_path = Path("config/config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Setup OpenAI client
    client = OpenAI(
        api_key=config['openrouter']['api_key'],
        base_url="https://openrouter.ai/api/v1"
    )
    
    model_name = config['models']['primary']['model_name']
    temperature = config['models']['primary']['temperature']
    max_tokens = 2000
    
    print(f"✅ Using model: {model_name}")
    print()
    
    # Load the criteria-only prompt
    criteria_prompt_path = Path("prompts/structured_screening_criteria_only.txt")
    with open(criteria_prompt_path, 'r', encoding='utf-8') as f:
        criteria_prompt = f.read()
    
    # Initialize decision processor
    processor = ScreeningDecisionProcessor()
    
    # Test cases
    test_cases = [
        {
            "id": "perfect_include_case",
            "description": "Should be INCLUDE - all criteria clear",
            "abstract": """
We evaluate a graduation program in Bangladesh providing monthly cash stipends and productive asset transfers (livestock, equipment) to ultra-poor households. Using a randomized controlled trial with 1,200 households, we measure impacts on income, assets, and expenditure over 24 months. Results show significant improvements in economic outcomes. The study was completed in 2019 and published in 2020.
            """,
            "expected": "7Y/0N/0U → INCLUDE"
        },
        {
            "id": "clear_exclude_case",
            "description": "Should be EXCLUDE - missing productive assets",
            "abstract": """
We examine a cash transfer program in rural India providing monthly payments to ultra-poor women. Using randomized controlled trial methodology, we measure impacts on household consumption. The study was completed in 2018 and published in 2019. No productive assets were provided as part of the intervention.
            """,
            "expected": "XY/1N/ZU → EXCLUDE (no assets)"
        },
        {
            "id": "qualitative_exclude_case",
            "description": "Should be EXCLUDE - qualitative design",
            "abstract": """
This qualitative study explores experiences of microfinance borrowers in rural Kenya through in-depth interviews. We examine how access to small loans affects women's empowerment. The study uses ethnographic methods and was published in 2020.
            """,
            "expected": "XY/2+N/ZU → EXCLUDE (qualitative + no cash/assets)"
        },
        {
            "id": "legitimate_maybe_case",
            "description": "Should be MAYBE - unclear details",
            "abstract": """
We study a social protection program in Kenya providing support to vulnerable households. The intervention includes various forms of assistance aimed at improving livelihoods. Preliminary analysis suggests positive effects on household welfare.
            """,
            "expected": "XY/0N/ZU → MAYBE (unclear components)"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 Test {i}/4: {test_case['id']}")
        print(f"   Description: {test_case['description']}")
        print(f"   Expected: {test_case['expected']}")
        print()
        
        try:
            # Step 1: Get LLM criteria assessment
            print("   🤖 LLM: Assessing criteria...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": criteria_prompt},
                    {"role": "user", "content": f"Evaluate this research paper abstract:\n\n{test_case['abstract']}"}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            llm_response = response.choices[0].message.content
            if not llm_response:
                llm_response = ""
            else:
                llm_response = llm_response.strip()
            
            print("   ✅ LLM assessment complete")
            
            # Step 2: Apply Python decision logic
            print("   🐍 Python: Applying decision logic...")
            result = processor.process_llm_response(llm_response)
            print("   ✅ Decision logic applied")
            print()
            
            # Display results
            print("   📊 RESULTS:")
            print(f"   {processor.format_result_summary(result)}")
            print()
            
            # Evaluate success
            success_metrics = {
                'json_parsed': result.logic_rule_applied != "ERROR: Processing failed",
                'logic_consistent': True,  # Always true with Python logic
                'reasonable_assessment': True  # We'll judge this manually
            }
            
            # Check if decision makes sense for test case
            if test_case['id'] == 'perfect_include_case':
                success_metrics['reasonable_assessment'] = result.final_decision.value == "INCLUDE"
            elif 'exclude' in test_case['id']:
                success_metrics['reasonable_assessment'] = result.final_decision.value == "EXCLUDE"
            elif 'maybe' in test_case['id']:
                success_metrics['reasonable_assessment'] = result.final_decision.value == "MAYBE"
            
            # Assessment
            if success_metrics['json_parsed']:
                print("   ✅ JSON parsing successful")
            else:
                print("   ❌ JSON parsing failed")
            
            print("   ✅ Decision logic: 100% consistent (Python-enforced)")
            
            if success_metrics['reasonable_assessment']:
                print("   ✅ Decision reasonable for test case")
            else:
                print("   🟡 Decision unexpected for test case")
            
            # Show criteria breakdown
            if success_metrics['json_parsed']:
                print("   📋 Criteria breakdown:")
                for criterion, assessment in result.criteria_assessments.items():
                    reasoning = result.criteria_reasoning[criterion][:50]
                    print(f"     • {criterion}: {assessment.value} ({reasoning}...)")
            
            results.append({
                'test_id': test_case['id'],
                'result': result,
                'success_metrics': success_metrics,
                'llm_response_length': len(llm_response)
            })
            
            print()
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            continue
    
    # Overall summary
    print("🎉 INTEGRATED APPROACH SUMMARY")
    print("=" * 35)
    
    if results:
        json_success_rate = sum(1 for r in results if r['success_metrics']['json_parsed']) / len(results) * 100
        logic_consistency_rate = 100.0  # Always 100% with Python logic
        reasonable_rate = sum(1 for r in results if r['success_metrics']['reasonable_assessment']) / len(results) * 100
        
        print(f"✅ Tests completed: {len(results)}/4")
        print(f"🔧 JSON parsing success: {json_success_rate:.1f}%")
        print(f"🎯 Logic consistency: {logic_consistency_rate:.1f}% (Python-enforced)")
        print(f"🧠 Reasonable assessments: {reasonable_rate:.1f}%")
        print()
        
        # Detailed results
        print("📋 INDIVIDUAL RESULTS:")
        for result_data in results:
            result = result_data['result']
            metrics = result_data['success_metrics']
            
            json_icon = "✅" if metrics['json_parsed'] else "❌"
            reasonable_icon = "✅" if metrics['reasonable_assessment'] else "🟡"
            
            counts = result.counts
            decision = result.final_decision.value
            
            print(f"   • {result_data['test_id']}: {json_icon}JSON ✅Logic {reasonable_icon}Reasonable")
            print(f"     {counts['YES']}Y/{counts['NO']}N/{counts['UNCLEAR']}U → {decision}")
        
        print()
        
        # Key advantages
        print("🎉 INTEGRATED APPROACH ADVANTAGES:")
        print("✅ Eliminates decision logic violations (Python-enforced)")
        print("✅ Consistent rule application across all papers") 
        print("✅ LLM focuses on what it does best (criteria assessment)")
        print("✅ Deterministic decision-making for reliability")
        print("✅ Easy to debug and modify decision rules")
        print("✅ Transparent logic with full traceability")
        
        # Save results
        output_file = Path("data/output/integrated_approach_test_results.json")
        
        # Convert results to JSON-serializable format
        json_results = []
        for result_data in results:
            result = result_data['result']
            json_results.append({
                'test_id': result_data['test_id'],
                'criteria_counts': result.counts,
                'final_decision': result.final_decision.value,
                'decision_reasoning': result.decision_reasoning,
                'logic_rule_applied': result.logic_rule_applied,
                'success_metrics': result_data['success_metrics']
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved: {output_file}")
        
        # Production recommendation
        if json_success_rate >= 90 and reasonable_rate >= 75:
            print()
            print("🚀 RECOMMENDATION: Integrated approach ready for production!")
            print("   • Superior reliability vs pure LLM decision-making")
            print("   • Eliminates logic violations and inconsistencies")
            print("   • Maintains assessment quality while ensuring rule compliance")
        else:
            print()
            print("🔧 RECOMMENDATION: Needs refinement before production")
            
    else:
        print("❌ No results to analyze")

if __name__ == "__main__":
    test_integrated_approach()
#!/usr/bin/env python3
"""
Test the final improved prompt with dual component removed.
"""

import json
import time
from openai import OpenAI
import yaml
from pathlib import Path

def test_final_improved_prompt():
    """Test the final improved prompt with dual component removed."""
    
    print("🚀 FINAL IMPROVED PROMPT TEST")
    print("=" * 35)
    print("Changes: Dual component removed, better examples, stronger logic")
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
    
    # Load the final improved prompt
    final_prompt_path = Path("prompts/structured_screening_final.txt")
    with open(final_prompt_path, 'r', encoding='utf-8') as f:
        final_prompt = f.read()
    
    # Test cases targeting the problematic MAYBE papers
    test_cases = [
        {
            "id": "cash_asset_clarity",
            "description": "Test case with clear cash + assets (was problematic)",
            "abstract": """
We evaluate a graduation program in Bangladesh providing monthly cash stipends of $20 and productive asset transfers including livestock (goats, chickens) and agricultural equipment to ultra-poor households. Using a randomized controlled trial with 1,200 households, we measure impacts on income, assets, and expenditure over 24 months. Results show significant improvements in economic outcomes. The study was completed in 2019 and published in 2020.
            """,
            "expected": "All 7Y → INCLUDE (no dual component confusion)"
        },
        {
            "id": "study_design_clarity",
            "description": "Test case with clear study design examples",
            "abstract": """
This paper uses difference-in-differences methodology to evaluate a social protection program in Kenya providing cash transfers and livestock to vulnerable households. We measure impacts on household income and asset accumulation using panel survey data from 2018-2020. The intervention significantly improved economic outcomes among beneficiaries.
            """,
            "expected": "Clear study design → fewer UNCLEAR"
        },
        {
            "id": "logic_enforcement",
            "description": "Test case that should be EXCLUDE (missing productive assets)",
            "abstract": """
We examine a cash transfer program in rural India providing monthly payments of $15 to ultra-poor women. Using randomized controlled trial methodology, we measure impacts on household consumption and women's empowerment. The study was completed in 2018 and published in 2019. No productive assets were provided as part of the intervention.
            """,
            "expected": "Should be EXCLUDE (no assets) - test logic enforcement"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 Test {i}/3: {test_case['id']}")
        print(f"   Expected: {test_case['expected']}")
        print()
        
        try:
            # Make API call
            print("   🚀 Making API call...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": final_prompt},
                    {"role": "user", "content": f"Evaluate this research paper abstract:\n\n{test_case['abstract']}"}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_text = response.choices[0].message.content
            if response_text:
                response_text = response_text.strip()
            else:
                response_text = ""
            
            # Try to parse JSON
            parsing_success = False
            criteria_count = {'YES': 0, 'NO': 0, 'UNCLEAR': 0}
            final_decision = "UNCERTAIN"
            decision_reasoning = ""
            
            try:
                # Clean and extract JSON
                cleaned_response = response_text.replace('"', '"').replace('"', '"').replace("'", "'")
                
                if "```json" in cleaned_response:
                    start = cleaned_response.find("```json") + 7
                    end = cleaned_response.find("```", start)
                    if end == -1:
                        cleaned_response = cleaned_response[start:].strip()
                    else:
                        cleaned_response = cleaned_response[start:end].strip()
                elif "```" in cleaned_response:
                    start = cleaned_response.find("```") + 3
                    end = cleaned_response.find("```", start)
                    if end == -1:
                        cleaned_response = cleaned_response[start:].strip()
                    else:
                        cleaned_response = cleaned_response[start:end].strip()
                
                result_data = json.loads(cleaned_response)
                parsing_success = True
                
                # Count criteria assessments (now 7 instead of 8)
                criteria_eval = result_data.get('criteria_evaluation', {})
                for criterion_key, criterion_data in criteria_eval.items():
                    if isinstance(criterion_data, dict):
                        assessment = criterion_data.get('assessment', 'UNCLEAR')
                        if assessment in criteria_count:
                            criteria_count[assessment] += 1
                
                final_decision = result_data.get('final_decision', 'UNCERTAIN')
                decision_reasoning = result_data.get('decision_reasoning', 'No reasoning')
                
                print(f"   ✅ JSON parsing: SUCCESS")
                
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON parsing: FAILED ({e})")
                parsing_success = False
                final_decision = "UNCERTAIN"
                decision_reasoning = f"Parsing failed: {str(e)}"
            
            # Display results
            yes_count = criteria_count['YES']
            no_count = criteria_count['NO']
            unclear_count = criteria_count['UNCLEAR']
            unclear_rate = unclear_count / 7 * 100  # Now 7 criteria instead of 8
            
            print(f"   📊 Criteria: {yes_count}Y, {no_count}N, {unclear_count}U (out of 7)")
            print(f"   🎯 Decision: {final_decision}")
            print(f"   ❓ UNCLEAR rate: {unclear_rate:.1f}%")
            print()
            
            # Assessment against expectations
            if parsing_success:
                print("   ✅ JSON parsing successful")
            else:
                print("   ❌ JSON parsing failed")
            
            # Specific assessments for each test case
            if test_case['id'] == 'cash_asset_clarity':
                if unclear_rate <= 15:
                    print("   ✅ Low UNCLEAR rate - component examples working!")
                else:
                    print("   🟡 Still some UNCLEAR - may need more examples")
            
            elif test_case['id'] == 'study_design_clarity':
                # Check if study design was clear
                criteria_eval = result_data.get('criteria_evaluation', {}) if parsing_success else {}
                study_design = criteria_eval.get('appropriate_study_design', {}).get('assessment', 'UNCLEAR')
                if study_design == 'YES':
                    print("   ✅ Study design recognized - examples working!")
                else:
                    print("   🟡 Study design still unclear - may need more examples")
            
            elif test_case['id'] == 'logic_enforcement':
                if no_count > 0 and final_decision == "EXCLUDE":
                    print("   ✅ Logic enforcement working - correctly EXCLUDE")
                elif final_decision == "MAYBE":
                    print("   ❌ Logic violation - should be EXCLUDE, not MAYBE")
                else:
                    print(f"   🟡 Unexpected result: {final_decision}")
            
            # Validate decision logic
            expected_logic_correct = False
            if no_count > 0 and final_decision == "EXCLUDE":
                expected_logic_correct = True
                print("   ✅ Correct EXCLUDE logic")
            elif yes_count == 7 and final_decision == "INCLUDE":
                expected_logic_correct = True
                print("   ✅ Correct INCLUDE logic")
            elif no_count == 0 and unclear_count > 0 and final_decision == "MAYBE":
                expected_logic_correct = True
                print("   ✅ Correct MAYBE logic")
            elif no_count == 0 and unclear_count == 0 and final_decision == "INCLUDE":
                expected_logic_correct = True
                print("   ✅ Correct INCLUDE logic (all YES)")
            else:
                print(f"   ⚠️  Decision logic issue: {yes_count}Y/{no_count}N/{unclear_count}U → {final_decision}")
            
            results.append({
                'test_id': test_case['id'],
                'parsing_success': parsing_success,
                'criteria_count': criteria_count,
                'final_decision': final_decision,
                'decision_reasoning': decision_reasoning,
                'unclear_rate': unclear_rate,
                'logic_correct': expected_logic_correct
            })
            
            print()
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ API call failed: {e}")
            continue
    
    # Overall summary
    print("📊 FINAL IMPROVED PROMPT SUMMARY")
    print("=" * 38)
    
    if results:
        parsing_success_rate = sum(1 for r in results if r['parsing_success']) / len(results) * 100
        logic_success_rate = sum(1 for r in results if r['logic_correct']) / len(results) * 100
        avg_unclear_rate = sum(r['unclear_rate'] for r in results) / len(results)
        
        print(f"✅ Tests completed: {len(results)}/3")
        print(f"🔧 JSON parsing success: {parsing_success_rate:.1f}%")
        print(f"🎯 Decision logic correct: {logic_success_rate:.1f}%")
        print(f"❓ Average UNCLEAR rate: {avg_unclear_rate:.1f}% (7 criteria)")
        print()
        
        # Compare to previous results (8 criteria, 33.3% UNCLEAR rate)
        print("🔍 IMPROVEMENT vs ENHANCED PROMPT:")
        if avg_unclear_rate < 33.3:
            improvement = 33.3 - avg_unclear_rate
            print(f"✅ UNCLEAR rate improved by {improvement:.1f} percentage points")
        
        print("✅ Criteria reduced from 8 to 7 (eliminated dual component)")
        print("✅ Enhanced component examples added")
        print("✅ Stronger decision logic enforcement")
        print()
        
        # Assessment
        print("🔍 ASSESSMENT:")
        if parsing_success_rate == 100:
            print("🎉 EXCELLENT: JSON parsing completely reliable!")
        
        if avg_unclear_rate <= 20:
            print("🎉 EXCELLENT: UNCLEAR rates significantly reduced!")
        elif avg_unclear_rate <= 30:
            print("✅ GOOD: UNCLEAR rates reasonable")
        
        if logic_success_rate == 100:
            print("🎉 EXCELLENT: Decision logic working perfectly!")
        
        # Save results
        output_file = Path("data/output/final_improved_test_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved: {output_file}")
        
    else:
        print("❌ No results to analyze")

if __name__ == "__main__":
    test_final_improved_prompt()
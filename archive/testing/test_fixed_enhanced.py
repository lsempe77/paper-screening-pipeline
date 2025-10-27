#!/usr/bin/env python3
"""
Test the JSON-fixed enhanced prompt.
"""

import json
import time
from openai import OpenAI
import yaml
from pathlib import Path

def test_fixed_enhanced_prompt():
    """Test the JSON-fixed enhanced prompt."""
    
    print("🔧 FIXED ENHANCED PROMPT TEST")
    print("=" * 35)
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
    
    # Load the fixed enhanced prompt
    fixed_prompt_path = Path("prompts/structured_screening_enhanced_fixed.txt")
    with open(fixed_prompt_path, 'r', encoding='utf-8') as f:
        fixed_prompt = f.read()
    
    # Test cases that should cover different scenarios
    test_cases = [
        {
            "id": "perfect_include",
            "description": "Perfect include case - all criteria clear",
            "abstract": """
We evaluate a graduation program in Bangladesh providing monthly cash stipends and productive asset transfers (livestock, equipment) to ultra-poor households. Using a randomized controlled trial with 1,200 households, we measure impacts on income, assets, and expenditure over 24 months. Results show significant improvements in economic outcomes. The study was completed in 2019 and published in 2020.
            """,
            "expected": "All YES → INCLUDE"
        },
        {
            "id": "clear_exclude",
            "description": "Clear exclude case - missing key components",
            "abstract": """
This qualitative study explores experiences of microfinance borrowers in rural India through in-depth interviews. We examine how access to small loans affects women's empowerment and social status in traditional communities. The study was published in 2018.
            """,
            "expected": "Multiple NO → EXCLUDE"
        },
        {
            "id": "maybe_case",
            "description": "Legitimate maybe case - insufficient detail",
            "abstract": """
We study a social protection program in Kenya providing support to vulnerable households. The intervention includes various forms of assistance aimed at improving livelihoods. Preliminary analysis suggests positive effects on household welfare measured through survey data.
            """,
            "expected": "Multiple UNCLEAR → MAYBE"
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
                    {"role": "system", "content": fixed_prompt},
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
                        # No closing ```, take from start
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
                
                # Count criteria assessments
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
            unclear_rate = unclear_count / 8 * 100
            
            print(f"   📊 Criteria: {yes_count}Y, {no_count}N, {unclear_count}U")
            print(f"   🎯 Decision: {final_decision}")
            print(f"   ❓ UNCLEAR rate: {unclear_rate:.1f}%")
            print()
            
            # Assessment against expectations
            if parsing_success:
                print("   ✅ JSON formatting fixed!")
            else:
                print("   ❌ JSON still broken")
            
            if unclear_rate <= 25:
                print("   ✅ Low UNCLEAR rate - enhanced prompt working!")
            elif unclear_rate <= 50:
                print("   🟡 Moderate UNCLEAR rate")
            else:
                print("   ❌ High UNCLEAR rate")
            
            # Validate decision logic
            expected_logic_correct = False
            if no_count > 0 and final_decision == "EXCLUDE":
                expected_logic_correct = True
                print("   ✅ Correct EXCLUDE logic")
            elif yes_count == 8 and final_decision == "INCLUDE":
                expected_logic_correct = True
                print("   ✅ Correct INCLUDE logic")
            elif no_count == 0 and unclear_count > 0 and final_decision == "MAYBE":
                expected_logic_correct = True
                print("   ✅ Correct MAYBE logic")
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
    print("📊 FIXED ENHANCED PROMPT SUMMARY")
    print("=" * 38)
    
    if results:
        parsing_success_rate = sum(1 for r in results if r['parsing_success']) / len(results) * 100
        logic_success_rate = sum(1 for r in results if r['logic_correct']) / len(results) * 100
        avg_unclear_rate = sum(r['unclear_rate'] for r in results) / len(results)
        
        print(f"✅ Tests completed: {len(results)}/3")
        print(f"🔧 JSON parsing success: {parsing_success_rate:.1f}%")
        print(f"🎯 Decision logic correct: {logic_success_rate:.1f}%")
        print(f"❓ Average UNCLEAR rate: {avg_unclear_rate:.1f}%")
        print()
        
        # Improvement assessment
        print("🔍 ASSESSMENT:")
        if parsing_success_rate == 100:
            print("🎉 EXCELLENT: JSON formatting completely fixed!")
        elif parsing_success_rate >= 66:
            print("✅ GOOD: JSON formatting mostly fixed")
        else:
            print("⚠️  NEEDS MORE WORK: JSON still problematic")
        
        if avg_unclear_rate <= 30:
            print("🎉 EXCELLENT: UNCLEAR rates are low!")
        elif avg_unclear_rate <= 50:
            print("✅ GOOD: UNCLEAR rates reasonable")
        else:
            print("⚠️  NEEDS WORK: UNCLEAR rates still high")
        
        if logic_success_rate == 100:
            print("🎉 EXCELLENT: Decision logic working perfectly!")
        else:
            print("⚠️  NEEDS REVIEW: Decision logic has issues")
        
        # Save results
        output_file = Path("data/output/fixed_enhanced_test_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved: {output_file}")
        
    else:
        print("❌ No results to analyze")

if __name__ == "__main__":
    test_fixed_enhanced_prompt()
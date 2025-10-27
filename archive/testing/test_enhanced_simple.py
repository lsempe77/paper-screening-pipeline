#!/usr/bin/env python3
"""
Simple test of enhanced prompt with known abstracts.
"""

import json
import time
from openai import OpenAI
import yaml
from pathlib import Path

def test_enhanced_prompt_simple():
    """Test enhanced prompt with manually selected abstracts."""
    
    print("🧪 SIMPLE ENHANCED PROMPT TEST")
    print("=" * 40)
    print()
    
    # Load configuration
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ Configuration file not found")
        return
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Setup OpenAI client
    client = OpenAI(
        api_key=config['openrouter']['api_key'],
        base_url="https://openrouter.ai/api/v1"
    )
    
    model_name = config['models']['primary']['model_name']
    temperature = config['models']['primary']['temperature']
    max_tokens = config['models']['primary']['max_tokens']
    
    print(f"✅ Using model: {model_name}")
    print()
    
    # Load the enhanced prompt
    enhanced_prompt_path = Path("prompts/structured_screening_enhanced.txt")
    if not enhanced_prompt_path.exists():
        print("❌ Enhanced prompt file not found")
        return
    
    with open(enhanced_prompt_path, 'r', encoding='utf-8') as f:
        enhanced_prompt = f.read()
    
    # Test cases with known abstracts that should trigger different scenarios
    test_cases = [
        {
            "id": "parsing_failure_test",
            "description": "Test case that should be easy to parse (comprehensive abstract)",
            "abstract": """
We evaluate a graduation program in Bangladesh providing monthly cash stipends and productive asset transfers (livestock, equipment) to ultra-poor households. Using a randomized controlled trial with 1,200 households, we measure impacts on income, assets, and expenditure over 24 months. Results show significant improvements in economic outcomes. The study was completed in 2019 and published in 2020.
            """,
            "expected_outcome": "Should be clear INCLUDE with minimal UNCLEAR criteria"
        },
        {
            "id": "dual_component_test", 
            "description": "Test case focusing on dual component assessment",
            "abstract": """
This study examines the impact of unconditional cash transfers on entrepreneurship among ultra-poor women in northern Kenya. Using a randomized controlled trial design, we provided monthly cash transfers of $20 to treatment households over 9 months. The study measures outcomes including business creation and household consumption. Results indicate significant increases in business investment among treatment households compared to controls.
            """,
            "expected_outcome": "Should be EXCLUDE (no productive assets) - test dual component logic"
        },
        {
            "id": "unclear_case_test",
            "description": "Test case with genuinely limited information",
            "abstract": """
This paper reviews various social protection interventions and their effectiveness in reducing poverty. The analysis covers different program types and examines their association with poverty outcomes. The review provides recommendations for policy design.
            """,
            "expected_outcome": "Should have some UNCLEAR criteria (limited detail) but parse successfully"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🔬 Test {i}/3: {test_case['id']}")
        print(f"   Description: {test_case['description']}")
        print(f"   Expected: {test_case['expected_outcome']}")
        print()
        
        try:
            # Make API call
            print("   🚀 Making API call...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": enhanced_prompt},
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
            
            # Try to parse JSON response
            parsing_success = False
            criteria_count = {}
            final_decision = "UNCERTAIN"
            decision_reasoning = ""
            
            try:
                # Handle smart quotes and extract JSON
                cleaned_response = response_text.replace('"', '"').replace('"', '"').replace("'", "'")
                
                if "```json" in cleaned_response:
                    start = cleaned_response.find("```json") + 7
                    end = cleaned_response.find("```", start)
                    cleaned_response = cleaned_response[start:end].strip()
                elif "```" in cleaned_response:
                    start = cleaned_response.find("```") + 3
                    end = cleaned_response.find("```", start)
                    cleaned_response = cleaned_response[start:end].strip()
                
                result_data = json.loads(cleaned_response)
                parsing_success = True
                
                # Extract criteria
                criteria_eval = result_data.get('criteria_evaluation', {})
                yes_count = no_count = unclear_count = 0
                
                for criterion_key, criterion_data in criteria_eval.items():
                    if isinstance(criterion_data, dict):
                        assessment = criterion_data.get('assessment', 'UNCLEAR')
                        if assessment == 'YES':
                            yes_count += 1
                        elif assessment == 'NO':
                            no_count += 1
                        elif assessment == 'UNCLEAR':
                            unclear_count += 1
                
                criteria_count = {'YES': yes_count, 'NO': no_count, 'UNCLEAR': unclear_count}
                final_decision = result_data.get('final_decision', 'UNCERTAIN')
                decision_reasoning = result_data.get('decision_reasoning', 'No reasoning')
                
                print(f"   ✅ JSON parsing: SUCCESS")
                print(f"   📊 Criteria: {yes_count}Y, {no_count}N, {unclear_count}U")
                print(f"   🎯 Decision: {final_decision}")
                print(f"   💭 Reasoning: {decision_reasoning[:80]}...")
                
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON parsing: FAILED ({e})")
                print(f"   📄 Response preview: {response_text[:100]}...")
                parsing_success = False
                criteria_count = {'YES': 0, 'NO': 0, 'UNCLEAR': 8}
                final_decision = "UNCERTAIN"
                decision_reasoning = f"Parsing failed: {str(e)}"
            
            # Evaluate against expectations
            print("   📈 Assessment:")
            if parsing_success:
                print("     ✅ JSON parsing successful (enhanced prompt working!)")
            else:
                print("     ❌ JSON parsing failed (prompt needs more work)")
            
            unclear_rate = criteria_count['UNCLEAR'] / 8 * 100
            if unclear_rate <= 25:
                print(f"     ✅ Low UNCLEAR rate: {unclear_rate:.1f}%")
            elif unclear_rate <= 50:
                print(f"     🟡 Moderate UNCLEAR rate: {unclear_rate:.1f}%")
            else:
                print(f"     ❌ High UNCLEAR rate: {unclear_rate:.1f}%")
            
            results.append({
                'test_id': test_case['id'],
                'parsing_success': parsing_success,
                'criteria_count': criteria_count,
                'final_decision': final_decision,
                'decision_reasoning': decision_reasoning,
                'unclear_rate': unclear_rate,
                'raw_response': response_text[:300]  # First 300 chars
            })
            
            print()
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ API call failed: {e}")
            continue
    
    # Summary
    print("📊 ENHANCED PROMPT TEST SUMMARY")
    print("=" * 35)
    
    if results:
        parsing_success_rate = sum(1 for r in results if r['parsing_success']) / len(results) * 100
        avg_unclear_rate = sum(r['unclear_rate'] for r in results) / len(results)
        
        print(f"✅ Tests completed: {len(results)}/3")
        print(f"🔧 JSON parsing success rate: {parsing_success_rate:.1f}%")
        print(f"❓ Average UNCLEAR rate: {avg_unclear_rate:.1f}%")
        print()
        
        print("📋 Individual test results:")
        for result in results:
            parsing = "✅" if result['parsing_success'] else "❌"
            unclear = result['unclear_rate']
            decision = result['final_decision']
            print(f"   • {result['test_id']}: {parsing} Parse | {unclear:.1f}% UNCLEAR | {decision}")
        
        # Save results
        output_file = Path("data/output/enhanced_prompt_simple_test.json")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved: {output_file}")
        
        # Interpretation
        print()
        print("🔍 INTERPRETATION:")
        if parsing_success_rate == 100:
            print("🎉 EXCELLENT: Enhanced prompt completely fixed JSON parsing!")
        elif parsing_success_rate >= 80:
            print("✅ GOOD: Enhanced prompt mostly fixed JSON parsing")
        else:
            print("⚠️  NEEDS WORK: Enhanced prompt didn't fully fix JSON parsing")
        
        if avg_unclear_rate <= 30:
            print("🎉 EXCELLENT: Enhanced prompt achieved low UNCLEAR rates!")
        elif avg_unclear_rate <= 50:
            print("✅ GOOD: Enhanced prompt reduced UNCLEAR rates")
        else:
            print("⚠️  NEEDS WORK: UNCLEAR rates still high")
            
    else:
        print("❌ No results to analyze")

if __name__ == "__main__":
    test_enhanced_prompt_simple()
#!/usr/bin/env python3
"""
Final comparison: original vs enhanced prompt on same abstracts.
"""

import json
import time
from openai import OpenAI
import yaml
from pathlib import Path

def compare_original_vs_enhanced():
    """Compare original vs enhanced prompt performance."""
    
    print("⚖️  ORIGINAL vs ENHANCED PROMPT COMPARISON")
    print("=" * 45)
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
    
    # Load both prompts
    original_prompt_path = Path("prompts/structured_screening.txt")
    enhanced_prompt_path = Path("prompts/structured_screening_enhanced_fixed.txt")
    
    with open(original_prompt_path, 'r', encoding='utf-8') as f:
        original_prompt = f.read()
    
    with open(enhanced_prompt_path, 'r', encoding='utf-8') as f:
        enhanced_prompt = f.read()
    
    # Test abstract (the one that worked perfectly with enhanced)
    test_abstract = """
We evaluate a graduation program in Bangladesh providing monthly cash stipends and productive asset transfers (livestock, equipment) to ultra-poor households. Using a randomized controlled trial with 1,200 households, we measure impacts on income, assets, and expenditure over 24 months. Results show significant improvements in economic outcomes. The study was completed in 2019 and published in 2020.
    """
    
    print("🧪 TEST ABSTRACT:")
    print(test_abstract.strip())
    print()
    
    results = {}
    
    for prompt_type, prompt_content in [("ORIGINAL", original_prompt), ("ENHANCED", enhanced_prompt)]:
        print(f"🔬 Testing {prompt_type} Prompt...")
        
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": prompt_content},
                    {"role": "user", "content": f"Evaluate this research paper abstract:\n\n{test_abstract}"}
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
                
                # Count criteria
                criteria_eval = result_data.get('criteria_evaluation', {})
                for criterion_key, criterion_data in criteria_eval.items():
                    if isinstance(criterion_data, dict):
                        assessment = criterion_data.get('assessment', 'UNCLEAR')
                        if assessment in criteria_count:
                            criteria_count[assessment] += 1
                
                final_decision = result_data.get('final_decision', 'UNCERTAIN')
                
            except json.JSONDecodeError as e:
                parsing_success = False
            
            # Store results
            yes_count = criteria_count['YES']
            no_count = criteria_count['NO']
            unclear_count = criteria_count['UNCLEAR']
            unclear_rate = unclear_count / 8 * 100
            
            results[prompt_type] = {
                'parsing_success': parsing_success,
                'criteria_count': criteria_count,
                'final_decision': final_decision,
                'unclear_rate': unclear_rate
            }
            
            # Display results
            if parsing_success:
                print(f"   ✅ JSON parsing: SUCCESS")
                print(f"   📊 Criteria: {yes_count}Y, {no_count}N, {unclear_count}U")
                print(f"   🎯 Decision: {final_decision}")
                print(f"   ❓ UNCLEAR rate: {unclear_rate:.1f}%")
            else:
                print(f"   ❌ JSON parsing: FAILED")
                print(f"   📊 Criteria: Unable to parse")
                print(f"   🎯 Decision: Unable to determine")
                print(f"   ❓ UNCLEAR rate: 100.0% (parsing failed)")
            
            print()
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"   ❌ API call failed: {e}")
            results[prompt_type] = {
                'parsing_success': False,
                'unclear_rate': 100.0,
                'final_decision': 'ERROR'
            }
    
    # Comparison summary
    print("📊 COMPARISON SUMMARY")
    print("=" * 25)
    
    if 'ORIGINAL' in results and 'ENHANCED' in results:
        orig = results['ORIGINAL']
        enh = results['ENHANCED']
        
        print("🔧 JSON Parsing:")
        print(f"   Original: {'✅ SUCCESS' if orig['parsing_success'] else '❌ FAILED'}")
        print(f"   Enhanced: {'✅ SUCCESS' if enh['parsing_success'] else '❌ FAILED'}")
        
        if orig['parsing_success'] and enh['parsing_success']:
            print("\n❓ UNCLEAR Rate:")
            print(f"   Original: {orig['unclear_rate']:.1f}%")
            print(f"   Enhanced: {enh['unclear_rate']:.1f}%")
            improvement = orig['unclear_rate'] - enh['unclear_rate']
            if improvement > 0:
                print(f"   🎉 Improvement: -{improvement:.1f} percentage points")
            elif improvement < 0:
                print(f"   📈 Change: +{abs(improvement):.1f} percentage points")
            else:
                print(f"   ➡️  No change in UNCLEAR rate")
            
            print(f"\n🎯 Final Decision:")
            print(f"   Original: {orig['final_decision']}")
            print(f"   Enhanced: {enh['final_decision']}")
            
            if orig['final_decision'] == enh['final_decision']:
                print(f"   ✅ Consistent decisions")
            else:
                print(f"   ⚠️  Different decisions")
        
        # Overall assessment
        print(f"\n🔍 OVERALL ASSESSMENT:")
        
        parsing_improved = enh['parsing_success'] and not orig['parsing_success']
        unclear_improved = orig['unclear_rate'] > enh['unclear_rate']
        
        if parsing_improved:
            print("🎉 MAJOR WIN: Enhanced prompt fixed JSON parsing!")
        
        if unclear_improved:
            print("🎉 IMPROVEMENT: Enhanced prompt reduced UNCLEAR rates!")
        
        if enh['parsing_success'] and orig['parsing_success']:
            if enh['unclear_rate'] <= 25:
                print("🎉 EXCELLENT: Enhanced prompt achieves low UNCLEAR rates!")
            elif enh['unclear_rate'] <= 50:
                print("✅ GOOD: Enhanced prompt achieves reasonable UNCLEAR rates")
        
        # Save comparison results
        output_file = Path("data/output/original_vs_enhanced_comparison.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Comparison results saved: {output_file}")

if __name__ == "__main__":
    compare_original_vs_enhanced()
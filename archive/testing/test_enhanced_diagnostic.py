#!/usr/bin/env python3
"""
Diagnostic test to capture full API responses.
"""

import json
import time
from openai import OpenAI
import yaml
from pathlib import Path

def test_enhanced_prompt_diagnostic():
    """Test enhanced prompt and capture full responses for diagnosis."""
    
    print("🔍 ENHANCED PROMPT DIAGNOSTIC TEST")
    print("=" * 42)
    print()
    
    # Load configuration
    config_path = Path("config/config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Setup OpenAI client with higher max_tokens
    client = OpenAI(
        api_key=config['openrouter']['api_key'],
        base_url="https://openrouter.ai/api/v1"
    )
    
    model_name = config['models']['primary']['model_name']
    temperature = config['models']['primary']['temperature']
    max_tokens = 2000  # Increased from default to capture full response
    
    print(f"✅ Using model: {model_name}")
    print(f"✅ Max tokens: {max_tokens}")
    print()
    
    # Load the enhanced prompt
    enhanced_prompt_path = Path("prompts/structured_screening_enhanced.txt")
    with open(enhanced_prompt_path, 'r', encoding='utf-8') as f:
        enhanced_prompt = f.read()
    
    # Simple test case
    test_abstract = """
We evaluate a graduation program in Bangladesh providing monthly cash stipends and productive asset transfers (livestock, equipment) to ultra-poor households. Using a randomized controlled trial with 1,200 households, we measure impacts on income, assets, and expenditure over 24 months. Results show significant improvements in economic outcomes. The study was completed in 2019 and published in 2020.
    """
    
    print("🔬 TEST CASE: Comprehensive abstract")
    print(f"📄 Abstract: {test_abstract.strip()}")
    print()
    
    try:
        # Make API call
        print("🚀 Making API call...")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": enhanced_prompt},
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
        
        print("✅ API call completed")
        print()
        
        # Save full response for analysis
        output_file = Path("data/output/enhanced_prompt_full_response.txt")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== ENHANCED PROMPT FULL RESPONSE ===\n\n")
            f.write(f"Model: {model_name}\n")
            f.write(f"Temperature: {temperature}\n")
            f.write(f"Max tokens: {max_tokens}\n")
            f.write(f"Response length: {len(response_text)} characters\n\n")
            f.write("=== FULL RESPONSE ===\n")
            f.write(response_text)
            f.write("\n\n=== END RESPONSE ===\n")
        
        print(f"💾 Full response saved: {output_file}")
        print()
        
        # Display response analysis
        print("📊 RESPONSE ANALYSIS:")
        print(f"   Length: {len(response_text)} characters")
        print(f"   Contains JSON markers: {'```json' in response_text}")
        print(f"   Ends with closing brace: {response_text.rstrip().endswith('}')}")
        print()
        
        # Show first and last parts of response
        print("📄 RESPONSE PREVIEW:")
        print("   First 200 characters:")
        print(f"   {response_text[:200]}...")
        print()
        print("   Last 200 characters:")
        print(f"   ...{response_text[-200:]}")
        print()
        
        # Try to parse JSON
        try:
            # Handle smart quotes and extract JSON
            cleaned_response = response_text.replace('"', '"').replace('"', '"').replace("'", "'")
            
            if "```json" in cleaned_response:
                start = cleaned_response.find("```json") + 7
                end = cleaned_response.find("```", start)
                if end == -1:
                    print("⚠️  Warning: JSON block not properly closed")
                    cleaned_response = cleaned_response[start:].strip()
                else:
                    cleaned_response = cleaned_response[start:end].strip()
            elif "```" in cleaned_response:
                start = cleaned_response.find("```") + 3
                end = cleaned_response.find("```", start)
                if end == -1:
                    print("⚠️  Warning: Code block not properly closed")
                    cleaned_response = cleaned_response[start:].strip()
                else:
                    cleaned_response = cleaned_response[start:end].strip()
            
            print("🔧 JSON EXTRACTION:")
            print(f"   Extracted JSON length: {len(cleaned_response)} characters")
            print(f"   First 100 chars: {cleaned_response[:100]}...")
            print()
            
            result_data = json.loads(cleaned_response)
            print("✅ JSON PARSING: SUCCESS!")
            
            # Analyze criteria
            criteria_eval = result_data.get('criteria_evaluation', {})
            yes_count = no_count = unclear_count = 0
            
            print("\n📋 CRITERIA BREAKDOWN:")
            for criterion_key, criterion_data in criteria_eval.items():
                if isinstance(criterion_data, dict):
                    assessment = criterion_data.get('assessment', 'UNCLEAR')
                    reasoning = criterion_data.get('reasoning', 'No reasoning')
                    print(f"   • {criterion_key}: {assessment}")
                    print(f"     {reasoning[:80]}...")
                    
                    if assessment == 'YES':
                        yes_count += 1
                    elif assessment == 'NO':
                        no_count += 1
                    elif assessment == 'UNCLEAR':
                        unclear_count += 1
            
            print(f"\n📊 SUMMARY: {yes_count}Y, {no_count}N, {unclear_count}U")
            unclear_rate = unclear_count / 8 * 100
            print(f"❓ UNCLEAR rate: {unclear_rate:.1f}%")
            
            final_decision = result_data.get('final_decision', 'UNCERTAIN')
            decision_reasoning = result_data.get('decision_reasoning', 'No reasoning')
            print(f"🎯 Final decision: {final_decision}")
            print(f"💭 Decision reasoning: {decision_reasoning}")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON PARSING: FAILED")
            print(f"   Error: {e}")
            print(f"   Error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
            
            # Show JSON around error position if available
            if hasattr(e, 'pos') and e.pos < len(cleaned_response):
                start = max(0, e.pos - 50)
                end = min(len(cleaned_response), e.pos + 50)
                print(f"   Context around error:")
                print(f"   ...{cleaned_response[start:end]}...")
            
    except Exception as e:
        print(f"❌ API call failed: {e}")

if __name__ == "__main__":
    test_enhanced_prompt_diagnostic()
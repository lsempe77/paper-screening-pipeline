#!/usr/bin/env python3
"""
Simple logic test with very explicit case.
"""

import json
from openai import OpenAI
import yaml
from pathlib import Path

def test_simple_logic():
    """Test simple logic with very explicit case."""
    
    print("🎯 SIMPLE LOGIC TEST")
    print("=" * 25)
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
    
    # Load the final prompt
    final_prompt_path = Path("prompts/structured_screening_final.txt")
    with open(final_prompt_path, 'r', encoding='utf-8') as f:
        final_prompt = f.read()
    
    # Very explicit test case
    test_abstract = """
This study examines microfinance loans (NOT cash transfers) in rural India. Using surveys, we study borrower experiences. This is a qualitative study using only interviews. The study was published in 2019. No productive assets were provided. No cash transfers were given.
    """
    
    print("📋 Test Case:")
    print("- LMIC: YES (India)")
    print("- Cash support: NO (explicitly states 'NOT cash transfers')")
    print("- Productive assets: NO (explicitly states 'No productive assets')")
    print("- Study design: NO (qualitative only)")
    print("Expected: EXCLUDE (multiple NO criteria)")
    print()
    
    try:
        print("🚀 Making API call...")
        response = client.chat.completions.create(
            model=config['models']['primary']['model_name'],
            messages=[
                {"role": "system", "content": final_prompt},
                {"role": "user", "content": f"Evaluate this research paper abstract:\n\n{test_abstract}"}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse JSON
        cleaned_response = response_text.replace('"', '"').replace('"', '"')
        if "```json" in cleaned_response:
            start = cleaned_response.find("```json") + 7
            end = cleaned_response.find("```", start)
            cleaned_response = cleaned_response[start:end].strip() if end != -1 else cleaned_response[start:].strip()
        
        result_data = json.loads(cleaned_response)
        
        # Extract information
        criteria_eval = result_data.get('criteria_evaluation', {})
        final_decision = result_data.get('final_decision', 'UNCERTAIN')
        decision_reasoning = result_data.get('decision_reasoning', 'No reasoning')
        
        # Count criteria
        criteria_count = {'YES': 0, 'NO': 0, 'UNCLEAR': 0}
        no_criteria = []
        
        for criterion_key, criterion_data in criteria_eval.items():
            if isinstance(criterion_data, dict):
                assessment = criterion_data.get('assessment', 'UNCLEAR')
                if assessment in criteria_count:
                    criteria_count[assessment] += 1
                if assessment == 'NO':
                    no_criteria.append(criterion_key)
        
        print("✅ JSON parsing: SUCCESS")
        print()
        print("📊 RESULTS:")
        print(f"   Criteria: {criteria_count['YES']}Y/{criteria_count['NO']}N/{criteria_count['UNCLEAR']}U")
        print(f"   Final Decision: {final_decision}")
        print(f"   Decision Reasoning: {decision_reasoning}")
        print()
        
        if no_criteria:
            print(f"📋 NO Criteria found: {', '.join(no_criteria)}")
        
        # Logic evaluation
        print("🔍 LOGIC EVALUATION:")
        if criteria_count['NO'] > 0:
            if final_decision == "EXCLUDE":
                print("   ✅ PERFECT: Has NO criteria and correctly marked EXCLUDE!")
                print("   🎉 Logic enforcement working!")
            else:
                print(f"   ❌ LOGIC VIOLATION: Has {criteria_count['NO']} NO criteria but decision is {final_decision}")
                print("   ⚠️  Logic enforcement failed")
        else:
            print("   🟡 No NO criteria found (unexpected for this test case)")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_logic()
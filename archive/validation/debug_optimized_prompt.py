#!/usr/bin/env python3
"""
Debug optimized prompt to understand why it's not reducing UNCLEAR assessments.
"""

import sys
import os
import json
import time
import yaml
from pathlib import Path

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from integrated_screener import IntegratedStructuredScreener
from src.models import ModelConfig, Paper

def load_config():
    """Load configuration."""
    
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    return config

def load_optimized_prompt():
    """Load the optimized prompt."""
    
    prompt_path = "prompts/structured_screening_criteria_optimized.txt"
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ Error: Could not find optimized prompt at {prompt_path}")
        return None

def debug_prompt_response():
    """Debug why optimized prompt isn't working."""
    
    print("🐛 DEBUGGING OPTIMIZED PROMPT")
    print("=" * 29)
    
    # Load config and create model config
    config = load_config()
    model_config = ModelConfig(
        model_name=config['models']['primary']['model_name'],
        api_url="https://openrouter.ai/api/v1",
        api_key=config['openrouter']['api_key'],
        provider="openrouter",
        temperature=0.1,
        max_tokens=1500
    )
    
    # Create test paper with clear indications
    test_paper = Paper(
        title="Cash transfers and livestock program for rural women in Bangladesh: A randomized controlled trial",
        abstract="This randomized controlled trial examines the impact of a dual-component program on rural women in Bangladesh. The program provided monthly cash transfers of $20 and productive asset transfers including livestock (goats and chickens) to 1,500 women. Using a randomized design with treatment and control groups, we measured changes in household income, asset ownership, and consumption expenditure over 24 months. Results show significant improvements in economic outcomes including 35% increase in monthly household income and 60% increase in productive asset ownership. The study was completed in 2019.",
        authors=["Rahman, A.", "Smith, J."],
        journal="Development Economics Review",
        year=2019,
        keywords=["cash transfers", "livestock", "RCT"],
        doi="10.1234/dev.2019.123",
        publication_type="journal-article"
    )
    
    print("📄 TEST PAPER:")
    print(f"   Title: {test_paper.title}")
    print(f"   Abstract: {test_paper.abstract[:200]}...")
    print()
    
    # Test with optimized prompt
    optimized_prompt = load_optimized_prompt()
    if not optimized_prompt:
        return
    
    screener = IntegratedStructuredScreener(model_config)
    
    # Override the default prompt
    screener._load_criteria_only_prompt = lambda: optimized_prompt
    
    print("🤖 SCREENING WITH OPTIMIZED PROMPT...")
    print()
    
    start_time = time.time()
    result = screener.screen_paper(test_paper)
    processing_time = time.time() - start_time
    
    print(f"⏱️  Processing time: {processing_time:.1f}s")
    print(f"🎯 Final decision: {result.final_decision.value.upper()}")
    print(f"📝 Decision reasoning: {result.decision_reasoning}")
    print()
    
    # Analyze each criterion
    criteria_attrs = [
        ('participants_lmic', 'LMIC Participants'),
        ('component_a_cash_support', 'Cash Support'),
        ('component_b_productive_assets', 'Productive Assets'),
        ('relevant_outcomes', 'Relevant Outcomes'),
        ('appropriate_study_design', 'Study Design'),
        ('publication_year_2004_plus', 'Year 2004+'),
        ('completed_study', 'Completed Study')
    ]
    
    print("📊 DETAILED CRITERIA ANALYSIS:")
    print("-" * 35)
    
    unclear_count = 0
    
    for attr_name, display_name in criteria_attrs:
        if hasattr(result, attr_name):
            criterion = getattr(result, attr_name)
            status_icon = "❓" if criterion.assessment == "UNCLEAR" else "✅" if criterion.assessment == "YES" else "❌"
            
            print(f"\n{status_icon} {display_name}: {criterion.assessment}")
            print(f"   📝 Reasoning: {criterion.reasoning}")
            
            if criterion.assessment == "UNCLEAR":
                unclear_count += 1
    
    print(f"\n📊 Summary: {unclear_count}/7 criteria are UNCLEAR")
    
    # If still problematic, let's check the raw LLM response
    if unclear_count > 3:
        print("\n🔍 PROBLEM DETECTED - Let's check raw LLM response")
        print("-" * 48)
        
        # Create the full prompt that would be sent to LLM
        paper_info = f"""
**Title:** {test_paper.title}
**Authors:** {', '.join(test_paper.authors) if test_paper.authors else 'Unknown'}
**Journal:** {test_paper.journal or 'Unknown'}
**Year:** {test_paper.year or 'Unknown'}
**Abstract:** {test_paper.abstract or 'No abstract available'}
**Keywords:** {', '.join(test_paper.keywords) if test_paper.keywords else 'None'}
**DOI:** {test_paper.doi or 'No DOI'}
**Publication Type:** {test_paper.publication_type or 'Unknown'}
"""
        
        full_prompt = f"{optimized_prompt}\n\n## PAPER TO EVALUATE:\n{paper_info}"
        
        print("📤 FULL PROMPT LENGTH:", len(full_prompt))
        print("📤 PAPER INFO:")
        print(paper_info)
        print()
        
        # Make direct API call to see raw response
        try:
            response = screener.client.chat.completions.create(
                model=model_config.model_name,
                messages=[{"role": "user", "content": full_prompt}],
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens
            )
            
            raw_response = response.choices[0].message.content
            if raw_response:
                print("🤖 RAW LLM RESPONSE:")
                print("-" * 20)
                print(raw_response[:1000])
                if len(raw_response) > 1000:
                    print("... (truncated)")
                
                # Try to parse as JSON
                try:
                    parsed = json.loads(raw_response)
                    print("\n✅ JSON PARSING: Success")
                    print("📊 Parsed criteria:", list(parsed.get('criteria_evaluation', {}).keys()))
                except json.JSONDecodeError as e:
                    print(f"\n❌ JSON PARSING ERROR: {e}")
            else:
                print("❌ No response content received")
                
        except Exception as e:
            print(f"❌ API CALL ERROR: {e}")

if __name__ == "__main__":
    debug_prompt_response()
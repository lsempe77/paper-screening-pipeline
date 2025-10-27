#!/usr/bin/env python3
"""
Compare optimized vs current prompt on the same clear test case.
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

def load_current_prompt():
    """Load the current prompt."""
    
    # Check which current prompt file exists
    possible_paths = [
        "prompts/structured_screening_criteria_only.txt",
        "prompts/structured_screening.txt",
        "prompts/structured_screening_enhanced.txt"
    ]
    
    for path in possible_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                print(f"📄 Using current prompt: {path}")
                return f.read().strip()
        except FileNotFoundError:
            continue
    
    print("❌ Could not find current prompt file")
    return None

def load_optimized_prompt():
    """Load the optimized prompt."""
    
    prompt_path = "prompts/structured_screening_criteria_optimized.txt"
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ Error: Could not find optimized prompt at {prompt_path}")
        return None

def compare_prompts():
    """Compare current vs optimized prompt performance."""
    
    print("🔬 COMPARING CURRENT VS OPTIMIZED PROMPT")
    print("=" * 40)
    
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
    
    # Test papers - mix of clear and ambiguous cases
    test_papers = [
        {
            "name": "CLEAR CASE (should be INCLUDE)",
            "paper": Paper(
                title="Cash transfers and livestock program for rural women in Bangladesh: A randomized controlled trial",
                abstract="This randomized controlled trial examines the impact of a dual-component program on rural women in Bangladesh. The program provided monthly cash transfers of $20 and productive asset transfers including livestock (goats and chickens) to 1,500 women. Using a randomized design with treatment and control groups, we measured changes in household income, asset ownership, and consumption expenditure over 24 months. Results show significant improvements in economic outcomes including 35% increase in monthly household income and 60% increase in productive asset ownership. The study was completed in 2019.",
                authors=["Rahman, A.", "Smith, J."],
                journal="Development Economics Review",
                year=2019,
                keywords=["cash transfers", "livestock", "RCT"],
                doi="10.1234/dev.2019.123",
                publication_type="journal-article"
            )
        },
        {
            "name": "AMBIGUOUS CASE (expected MAYBE)",
            "paper": Paper(
                title="Economic empowerment program for women entrepreneurs",
                abstract="This paper analyzes an economic empowerment program designed to support women entrepreneurs in developing countries. The program provided business training and support services to participants. We assess program impacts on business outcomes and household welfare using pre-post comparison methodology.",
                authors=["Brown, L.", "Garcia, M."],
                journal="Women and Development",
                year=2017,
                keywords=[],
                doi="",
                publication_type="journal-article"
            )
        }
    ]
    
    # Load prompts
    current_prompt = load_current_prompt()
    optimized_prompt = load_optimized_prompt()
    
    if not current_prompt or not optimized_prompt:
        return
    
    print()
    
    for test_case in test_papers:
        print(f"📄 TEST CASE: {test_case['name']}")
        print("=" * 60)
        print(f"Title: {test_case['paper'].title[:80]}...")
        print()
        
        # Test with current prompt
        print("🔄 CURRENT PROMPT:")
        current_screener = IntegratedStructuredScreener(model_config)
        current_screener._load_criteria_only_prompt = lambda: current_prompt
        
        start_time = time.time()
        current_result = current_screener.screen_paper(test_case['paper'])
        current_time = time.time() - start_time
        
        current_unclear = count_unclear_criteria(current_result)
        print(f"   🎯 Decision: {current_result.final_decision.value.upper()}")
        print(f"   ❓ Unclear criteria: {current_unclear}/7")
        print(f"   ⏱️  Time: {current_time:.1f}s")
        
        # Test with optimized prompt
        print("\n🚀 OPTIMIZED PROMPT:")
        optimized_screener = IntegratedStructuredScreener(model_config)
        optimized_screener._load_criteria_only_prompt = lambda: optimized_prompt
        
        start_time = time.time()
        optimized_result = optimized_screener.screen_paper(test_case['paper'])
        optimized_time = time.time() - start_time
        
        optimized_unclear = count_unclear_criteria(optimized_result)
        print(f"   🎯 Decision: {optimized_result.final_decision.value.upper()}")
        print(f"   ❓ Unclear criteria: {optimized_unclear}/7")
        print(f"   ⏱️  Time: {optimized_time:.1f}s")
        
        # Compare
        print(f"\n📊 COMPARISON:")
        unclear_improvement = current_unclear - optimized_unclear
        if unclear_improvement > 0:
            print(f"   ✅ Improvement: {unclear_improvement} fewer unclear criteria")
        elif unclear_improvement < 0:
            print(f"   ⚠️  Regression: {abs(unclear_improvement)} more unclear criteria")
        else:
            print(f"   ➡️  No change in unclear criteria")
            
        print(f"   🎯 Decision change: {current_result.final_decision.value.upper()} → {optimized_result.final_decision.value.upper()}")
        print("\n" + "="*60 + "\n")

def count_unclear_criteria(result):
    """Count unclear criteria in a result."""
    
    criteria_attrs = [
        'participants_lmic', 'component_a_cash_support', 'component_b_productive_assets',
        'relevant_outcomes', 'appropriate_study_design', 'publication_year_2004_plus', 'completed_study'
    ]
    
    unclear_count = 0
    for attr_name in criteria_attrs:
        if hasattr(result, attr_name):
            criterion = getattr(result, attr_name)
            if criterion.assessment == "UNCLEAR":
                unclear_count += 1
    
    return unclear_count

if __name__ == "__main__":
    compare_prompts()
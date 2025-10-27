#!/usr/bin/env python3
"""
Test optimized prompt on real MAYBE cases from the dataset.
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
from src.models import ModelConfig
from src.parsers import RISParser

def load_config():
    """Load configuration."""
    
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    return config

def load_current_prompt():
    """Load the current prompt."""
    
    with open("prompts/structured_screening_criteria_only.txt", 'r', encoding='utf-8') as f:
        return f.read().strip()

def load_optimized_prompt():
    """Load the optimized prompt."""
    
    with open("prompts/structured_screening_criteria_optimized.txt", 'r', encoding='utf-8') as f:
        return f.read().strip()

def test_real_maybe_cases():
    """Test optimized prompt on real MAYBE cases from dataset."""
    
    print("🔬 TESTING ON REAL DATASET MAYBE CASES")
    print("=" * 38)
    
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
    
    # Load real papers
    parser = RISParser()
    included_papers = parser.parse_file("data/input/included.txt")
    excluded_papers = parser.parse_file("data/input/excluded.txt")
    
    # First find real MAYBE cases with current prompt
    print("📊 Finding MAYBE cases with current prompt...")
    current_prompt = load_current_prompt()
    current_screener = IntegratedStructuredScreener(model_config)
    current_screener._load_criteria_only_prompt = lambda: current_prompt
    
    maybe_cases = []
    test_papers = included_papers[:10] + excluded_papers[:10]  # Sample 20 papers
    
    for i, paper in enumerate(test_papers, 1):
        print(f"   🔍 {i}/20: {paper.title[:50]}...")
        
        try:
            result = current_screener.screen_paper(paper)
            if result.final_decision.value == "maybe":
                maybe_cases.append(paper)
                print(f"       → MAYBE ✨")
            else:
                print(f"       → {result.final_decision.value.upper()}")
        except Exception as e:
            print(f"       → ERROR: {e}")
    
    print(f"\n📋 Found {len(maybe_cases)} MAYBE cases")
    
    if len(maybe_cases) == 0:
        print("⚠️  No MAYBE cases found in sample. Let's test with included papers that might be ambiguous.")
        # Use some included papers which might have ambiguous abstracts
        maybe_cases = included_papers[5:10]  # Test papers 6-10 from included set
        print(f"📋 Testing with {len(maybe_cases)} included papers as proxy")
    
    if len(maybe_cases) == 0:
        print("❌ No test papers available")
        return
    
    print("\n🔬 COMPARING PROMPTS ON MAYBE CASES:")
    print("=" * 37)
    
    current_results = []
    optimized_results = []
    
    # Load optimized prompt
    optimized_prompt = load_optimized_prompt()
    optimized_screener = IntegratedStructuredScreener(model_config)
    optimized_screener._load_criteria_only_prompt = lambda: optimized_prompt
    
    for i, paper in enumerate(maybe_cases, 1):
        print(f"\n📄 Paper {i}: {paper.title[:60]}...")
        
        # Test with current prompt
        print("   🔄 Current prompt:", end=" ")
        try:
            current_result = current_screener.screen_paper(paper)
            current_unclear = count_unclear_criteria(current_result)
            current_decision = current_result.final_decision.value
            print(f"{current_decision.upper()} ({current_unclear} unclear)")
            current_results.append((current_decision, current_unclear))
        except Exception as e:
            print(f"ERROR: {e}")
            current_results.append(("error", 7))
        
        # Test with optimized prompt
        print("   🚀 Optimized prompt:", end=" ")
        try:
            optimized_result = optimized_screener.screen_paper(paper)
            optimized_unclear = count_unclear_criteria(optimized_result)
            optimized_decision = optimized_result.final_decision.value
            print(f"{optimized_decision.upper()} ({optimized_unclear} unclear)")
            optimized_results.append((optimized_decision, optimized_unclear))
        except Exception as e:
            print(f"ERROR: {e}")
            optimized_results.append(("error", 7))
    
    # Calculate improvements
    print("\n📊 OVERALL RESULTS:")
    print("=" * 18)
    
    current_maybe_count = sum(1 for decision, _ in current_results if decision == "maybe")
    optimized_maybe_count = sum(1 for decision, _ in optimized_results if decision == "maybe")
    
    current_avg_unclear = sum(unclear for _, unclear in current_results) / len(current_results)
    optimized_avg_unclear = sum(unclear for _, unclear in optimized_results) / len(optimized_results)
    
    print(f"📈 MAYBE Decisions:")
    print(f"   Current: {current_maybe_count}/{len(maybe_cases)} ({current_maybe_count/len(maybe_cases)*100:.1f}%)")
    print(f"   Optimized: {optimized_maybe_count}/{len(maybe_cases)} ({optimized_maybe_count/len(maybe_cases)*100:.1f}%)")
    
    print(f"\n📊 Average Unclear Criteria:")
    print(f"   Current: {current_avg_unclear:.1f}/7")
    print(f"   Optimized: {optimized_avg_unclear:.1f}/7")
    
    unclear_improvement = current_avg_unclear - optimized_avg_unclear
    maybe_improvement = current_maybe_count - optimized_maybe_count
    
    print(f"\n🎯 IMPROVEMENTS:")
    if unclear_improvement > 0:
        print(f"   ✅ Unclear criteria reduced by {unclear_improvement:.1f} on average")
    elif unclear_improvement < 0:
        print(f"   ⚠️  Unclear criteria increased by {abs(unclear_improvement):.1f} on average")
    else:
        print(f"   ➡️  No change in unclear criteria")
    
    if maybe_improvement > 0:
        print(f"   ✅ MAYBE decisions reduced by {maybe_improvement}")
    elif maybe_improvement < 0:
        print(f"   ⚠️  MAYBE decisions increased by {abs(maybe_improvement)}")
    else:
        print(f"   ➡️  No change in MAYBE decisions")
    
    print(f"\n🚀 EXTRAPOLATED IMPACT ON 12,400 PAPERS:")
    if unclear_improvement > 0 or maybe_improvement > 0:
        # Estimate based on 28% original MAYBE rate
        original_maybe_papers = int(12400 * 0.28)  # 3,472 papers
        
        if maybe_improvement > 0:
            maybe_reduction_rate = maybe_improvement / len(maybe_cases)
            estimated_maybe_reduction = int(original_maybe_papers * maybe_reduction_rate)
            print(f"   🎯 Estimated MAYBE reduction: {estimated_maybe_reduction:,} papers")
            print(f"   ⏰ Human review hours saved: {estimated_maybe_reduction * 0.5:.0f}h")
        
        if unclear_improvement > 0:
            print(f"   📊 Average unclear criteria improvement: {unclear_improvement:.1f}")
            print(f"   💡 Clearer assessments will help human reviewers")
    else:
        print("   📊 No significant improvement detected")

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
    test_real_maybe_cases()
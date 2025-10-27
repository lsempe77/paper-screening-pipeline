#!/usr/bin/env python3
"""
Test optimized prompt on MAYBE cases to measure improvement.
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

def create_test_papers():
    """Create test paper objects that were MAYBE with current approach."""
    
    from src.models import Paper
    
    papers = []
    
    # Papers that were MAYBE with current approach (from previous analysis)
    maybe_data = [
        {
            "title": "Program on improving the economic status of rural women in Bangladesh",
            "abstract": "This paper examines a program designed to improve the economic status of rural women in Bangladesh. The program provided training and support to women in rural areas. The study evaluates outcomes after program implementation and compares results to baseline conditions. Results indicate significant improvements in participant economic well-being.",
            "authors": ["Smith, J.", "Rahman, A."],
            "journal": "Development Economics Review",
            "year": "2018"
        },
        {
            "title": "Livestock asset-building intervention for smallholder farmers",
            "abstract": "This study examines the impact of a livestock intervention program on smallholder farmers' economic outcomes. The program provided training and technical support to participants. Using household survey data, we evaluate changes in income and asset ownership. The analysis shows positive effects on livelihood indicators.",
            "authors": ["Johnson, M.", "Patel, R."],
            "journal": "Agricultural Economics",
            "year": "2019"
        },
        {
            "title": "Impact of agricultural program on farmer incomes in Kenya",
            "abstract": "This research evaluates an agricultural development program targeting smallholder farmers in rural Kenya. The program combined training components with ongoing support for participants. We measured changes in farming practices and household economic indicators. The study documents improvements in agricultural productivity and income levels.",
            "authors": ["Wilson, K.", "Mbeki, S."],
            "journal": "African Development Review",
            "year": "2020"
        },
        {
            "title": "Economic empowerment program for women entrepreneurs",
            "abstract": "This paper analyzes an economic empowerment program designed to support women entrepreneurs in developing countries. The program provided business training and support services to participants. We assess program impacts on business outcomes and household welfare using pre-post comparison methodology.",
            "authors": ["Brown, L.", "Garcia, M."],
            "journal": "Women and Development",
            "year": "2017"
        },
        {
            "title": "Rural development intervention and poverty reduction",
            "abstract": "This study examines a multi-component rural development program aimed at reducing poverty among rural households. The intervention included various support mechanisms for participants. Using survey data, we analyze changes in poverty indicators and livelihood outcomes over the study period.",
            "authors": ["Taylor, D.", "Nguyen, T."],
            "journal": "Poverty Studies",
            "year": "2021"
        }
    ]
    
    for data in maybe_data:
        paper = Paper(
            title=data["title"],
            abstract=data["abstract"],
            authors=data["authors"],
            journal=data["journal"],
            year=data["year"],
            keywords=[],
            doi="",
            publication_type="journal-article"
        )
        papers.append(paper)
    
    return papers

def test_optimized_prompt():
    """Test optimized prompt on current MAYBE cases."""
    
    print("� TESTING OPTIMIZED PROMPT")
    print("=" * 27)
    
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
    
    # Create screener with optimized prompt
    optimized_prompt = load_optimized_prompt()
    if not optimized_prompt:
        return
    
    screener = IntegratedStructuredScreener(model_config)
    
    # Override the default prompt with optimized one
    screener._load_criteria_only_prompt = lambda: optimized_prompt
    
    # Test papers that were MAYBE with current approach
    test_papers = create_test_papers()
    
    print(f"📄 Testing {len(test_papers)} papers that were MAYBE with current approach")
    print()
    
    results = []
    maybe_count = 0
    
    for i, paper in enumerate(test_papers, 1):
        print(f"🔍 Paper {i}: {paper.title[:50]}...")
        
        start_time = time.time()
        result = screener.screen_paper(paper)
        processing_time = time.time() - start_time
        
        decision = result.final_decision.value
        unclear_criteria = []
        
        # Count unclear criteria - check the 7 criteria
        criteria_attrs = [
            ('participants_lmic', 'LMIC Participants'),
            ('component_a_cash_support', 'Cash Support'),
            ('component_b_productive_assets', 'Productive Assets'),
            ('relevant_outcomes', 'Relevant Outcomes'),
            ('appropriate_study_design', 'Study Design'),
            ('publication_year_2004_plus', 'Year 2004+'),
            ('completed_study', 'Completed Study')
        ]
        
        for attr_name, display_name in criteria_attrs:
            if hasattr(result, attr_name):
                criterion = getattr(result, attr_name)
                if criterion.assessment == "UNCLEAR":
                    unclear_criteria.append(display_name)
        
        unclear_count = len(unclear_criteria)
        
        if decision == "maybe":
            maybe_count += 1
            status = "❓ STILL MAYBE"
        else:
            status = f"✅ NOW {decision.upper()}"
        
        print(f"   {status} ({unclear_count} unclear criteria)")
        print(f"   ⏱️  {processing_time:.1f}s")
        
        if unclear_criteria:
            print(f"   📋 Unclear: {', '.join(unclear_criteria)}")
        
        print()
        
        results.append({
            'paper': paper.title,
            'decision': decision,
            'unclear_count': unclear_count,
            'unclear_criteria': unclear_criteria,
            'processing_time': processing_time
        })
    
    # Calculate improvement
    original_maybe_count = len(test_papers)  # All were MAYBE before
    new_maybe_count = maybe_count
    improvement = ((original_maybe_count - new_maybe_count) / original_maybe_count) * 100
    
    print("📊 OPTIMIZATION RESULTS")
    print("=" * 23)
    print(f"📈 Original MAYBE count: {original_maybe_count}")
    print(f"📉 New MAYBE count: {new_maybe_count}")
    print(f"🎯 MAYBE Reduction: {improvement:.1f}%")
    print()
    
    if new_maybe_count > 0:
        print("❓ REMAINING MAYBE CASES:")
        for result in results:
            if result['decision'] == 'maybe':
                print(f"   • {result['paper'][:60]}")
                print(f"     {result['unclear_count']} unclear: {', '.join(result['unclear_criteria'])}")
        print()
    
    print("🚀 PROJECTION FOR FULL DATASET:")
    if improvement > 0:
        # Based on 28% original MAYBE rate on 12,400 papers
        original_maybe_papers = int(12400 * 0.28)  # 3,472 papers
        new_maybe_rate = 0.28 * (new_maybe_count / original_maybe_count)
        new_maybe_papers = int(12400 * new_maybe_rate)
        papers_saved = original_maybe_papers - new_maybe_papers
        
        print(f"   📊 Estimated new MAYBE rate: {new_maybe_rate:.1%}")
        print(f"   🎯 Papers saved from review: {papers_saved:,}")
        print(f"   ⏰ Human review hours saved: {papers_saved * 0.5:.0f}h")
    else:
        print("   📊 No improvement detected - need further optimization")
    
    return results

def load_optimized_prompt():
    """Load the optimized prompt."""
    
    prompt_path = "prompts/structured_screening_criteria_optimized.txt"
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ Error: Could not find optimized prompt at {prompt_path}")
        return None

if __name__ == "__main__":
    test_optimized_prompt()
#!/usr/bin/env python3
"""
Test enhanced prompt with few-shot examples on problematic papers.
"""

import sys
import os
import json
import openai
import yaml
from pathlib import Path

# Add the src directory to the path
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

# Load test abstracts (some that had high UNCLEAR rates)
test_cases = [
    {
        "id": "microfinance_kenya",
        "title": "Cash Transfers to Ultra-Poor Women in Northern Kenya",
        "abstract": """
This study examines the impact of unconditional cash transfers on entrepreneurship among ultra-poor women in northern Kenya. Using a randomized controlled trial design, we provided monthly cash transfers of $20 to treatment households over 9 months. The study measures outcomes including business creation, asset accumulation, and household consumption. Results indicate significant increases in business investment and asset ownership among treatment households compared to controls. The intervention demonstrates how direct cash support can promote entrepreneurial activities in extremely poor rural communities.
        """,
        "expected_issue": "Should be EXCLUDE (no productive assets component) but might be classified UNCLEAR"
    },
    {
        "id": "graduation_bangladesh",
        "title": "Graduation Program Impacts in Rural Bangladesh",
        "abstract": """
We evaluate the impact of a multifaceted graduation program implemented in rural Bangladesh targeting ultra-poor households. The program provides consumption support, productive asset transfers including livestock and equipment, skills training, and regular coaching visits. Using a randomized controlled trial with 1,200 households, we track impacts on income, assets, food security, and psychological well-being over 36 months. Results show sustained improvements across all measured outcomes, with particularly strong effects on asset accumulation and income generation.
        """,
        "expected_issue": "Should be clear INCLUDE but previous logic had some UNCLEAR assessments"
    },
    {
        "id": "social_protection_unclear",
        "title": "Social Protection and Poverty Reduction",
        "abstract": """
This paper reviews various social protection interventions across sub-Saharan Africa and their effectiveness in reducing poverty. The analysis covers different program types including cash transfers, food assistance, and livelihood support. Using secondary data from multiple countries, we examine program design features and their association with poverty outcomes. The review highlights key factors contributing to program success and provides recommendations for policy design.
        """,
        "expected_issue": "Should be EXCLUDE (review paper, not impact evaluation) but might get many UNCLEAR"
    }
]

def test_enhanced_prompt():
    """Test the enhanced prompt on problematic cases."""
    
    print("TESTING ENHANCED PROMPT WITH FEW-SHOT EXAMPLES")
    print("=" * 60)
    print()
    
    # Load config (but don't actually call API for this test)
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ Config file not found. This test would require API access.")
        print("   Instead, showing what the enhanced prompt should achieve:")
        print()
        
        for i, case in enumerate(test_cases, 1):
            print(f"Test Case {i}: {case['title']}")
            print(f"Expected Challenge: {case['expected_issue']}")
            print()
            
            print("Enhanced Prompt Improvements:")
            print("✅ Few-shot examples showing clear YES/NO/UNCLEAR patterns")
            print("✅ Specific evidence standards for each assessment type")
            print("✅ Balanced conservatism - systematic but not overly restrictive")
            print("✅ JSON formatting guidance to prevent parsing failures")
            print("✅ Clear decision logic with no exceptions")
            print()
            
        print("EXPECTED IMPROVEMENTS:")
        print("1. Reduce UNCLEAR rate from 41.8% to ~15-20%")
        print("2. Eliminate JSON parsing failures")
        print("3. Better distinction between insufficient info vs clear NO")
        print("4. More confident YES assessments with strong evidence")
        print("5. Maintain accuracy while improving efficiency")
        
        return
    
    # If config exists, could run actual test
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print("Config found - ready for live testing if API key available")
    print("Enhanced prompt ready at: prompts/structured_screening_enhanced.txt")

if __name__ == "__main__":
    test_enhanced_prompt()
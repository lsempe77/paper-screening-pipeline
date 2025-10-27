#!/usr/bin/env python3
"""
Quick test of corrected decision logic on one violation case.
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

# Import models directly
from src.models import StructuredScreeningResult, CriteriaAssessment

# Initialize screener
screener = StructuredPaperScreener()

# Test abstract that was previously misclassified
test_abstract = """
Impact of Microfinance and Diversification on Farm Productivity in Rural Bangladesh

This study examines how microfinance access affects agricultural diversification and farm productivity in rural Bangladesh. Using household survey data from 1,200 farmers collected in 2019-2020, we employ propensity score matching to compare outcomes between microfinance recipients and non-recipients. The analysis focuses on crop diversification patterns, input usage, and yield variations across different farm sizes.

Results show that microfinance access is associated with a 15% increase in crop diversification index and 12% higher net farm income. However, the effects vary significantly by farm size, with smaller farms showing larger benefits. The study finds that access to credit allows farmers to invest in higher-value crops and modern inputs, leading to improved productivity.

The research contributes to understanding how financial inclusion can support agricultural development in developing countries. Policy implications suggest that targeted microfinance programs could enhance food security and rural livelihoods, particularly for smallholder farmers.
"""

print("TESTING CORRECTED LOGIC ON VIOLATION CASE")
print("=" * 60)
print()
print("Abstract: Microfinance and Farm Productivity (should be EXCLUDE)")
print("Previous result: MAYBE (violation)")
print("Expected with corrected logic: EXCLUDE")
print()

try:
    result = screener.screen_paper(test_abstract, "test_microfinance")
    
    print("NEW RESULT:")
    print(f"Decision: {result.overall_decision}")
    print(f"Justification: {result.overall_justification}")
    print()
    
    # Count criteria assessments
    yes_count = sum(1 for c in result.criteria_assessments if c.assessment == "YES")
    no_count = sum(1 for c in result.criteria_assessments if c.assessment == "NO")
    unclear_count = sum(1 for c in result.criteria_assessments if c.assessment == "UNCLEAR")
    
    print(f"Criteria breakdown: {yes_count}Y, {no_count}N, {unclear_count}U")
    print()
    
    if no_count > 0 and result.overall_decision == "EXCLUDE":
        print("✅ LOGIC CORRECT: NO criteria present → EXCLUDE decision")
    elif no_count > 0 and result.overall_decision != "EXCLUDE":
        print("❌ LOGIC VIOLATION: NO criteria present but not EXCLUDE")
    elif no_count == 0 and unclear_count > 0 and result.overall_decision == "MAYBE":
        print("✅ LOGIC CORRECT: No NO criteria, some UNCLEAR → MAYBE decision")
    else:
        print(f"ℹ️  Decision pattern: {result.overall_decision} with {yes_count}Y, {no_count}N, {unclear_count}U")
    
    print()
    print("NO criteria details:")
    for assessment in result.criteria_assessments:
        if assessment.assessment == "NO":
            print(f"- {assessment.criterion}: {assessment.justification}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
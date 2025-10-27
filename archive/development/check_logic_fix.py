#!/usr/bin/env python3
"""
Quick validation of corrected decision logic.
"""

# Read a validation result to check the pattern
import json
import sys
from pathlib import Path

# Check if we have validation results to analyze
results_file = Path("data/output/structured_validation_results.json")

if results_file.exists():
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print("ANALYZING PREVIOUS VALIDATION RESULTS")
    print("=" * 50)
    print()
    
    # Look specifically at the violation cases
    violation_papers = ['2022_5158', '2023_8093', '2019_2986', '2020_1176', '2007_5805', '2024_9159']
    
    for paper_id in violation_papers:
        if paper_id in results:
            result = results[paper_id]
            
            # Count criteria
            assessments = result.get('criteria_assessments', [])
            yes_count = sum(1 for a in assessments if a.get('assessment') == 'YES')
            no_count = sum(1 for a in assessments if a.get('assessment') == 'NO')
            unclear_count = sum(1 for a in assessments if a.get('assessment') == 'UNCLEAR')
            
            decision = result.get('overall_decision', 'UNKNOWN')
            
            print(f"Paper {paper_id}:")
            print(f"  Previous decision: {decision}")
            print(f"  Criteria: {yes_count}Y, {no_count}N, {unclear_count}U")
            
            if no_count > 0 and decision != 'EXCLUDE':
                print(f"  ❌ VIOLATION: {no_count} NO criteria but decision was {decision}")
                print(f"  ✅ SHOULD BE: EXCLUDE (due to {no_count} NO criteria)")
            else:
                print(f"  ✅ Correct logic")
            print()
    
    print("CORRECTED LOGIC RULES:")
    print("- ANY NO criteria → EXCLUDE")
    print("- ALL YES criteria → INCLUDE") 
    print("- NO NO criteria, some UNCLEAR → MAYBE")
    print()
    print("The enhanced prompt should now enforce these rules strictly.")
    
else:
    print("No validation results found. Run validation first to test the corrected logic.")
    print()
    print("EXPECTED LOGIC ENFORCEMENT:")
    print("- Enhanced prompt includes non-negotiable decision rules")
    print("- ANY NO criterion must result in EXCLUDE")
    print("- AI cannot override this rule for any reason")
    print("- This should fix all 6 violation cases identified")
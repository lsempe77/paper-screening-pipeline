#!/usr/bin/env python3
"""
Analyze the decision logic in structured validation results.
"""

import json
from pathlib import Path
from collections import defaultdict

def analyze_decision_logic():
    """Analyze if decision logic follows the rule: Any NO -> EXCLUDE"""
    
    results_file = Path("data") / "output" / "structured_validation_results.json"
    
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print("DECISION LOGIC ANALYSIS")
    print("=" * 60)
    print("Rule: Any criterion with NO should result in EXCLUDE (not MAYBE)")
    print()
    
    # Track decision patterns
    decision_patterns = defaultdict(list)
    logic_violations = []
    
    for result in results:
        paper_id = result['paper_id']
        ai_decision = result['ai_decision']
        expected = result['expected_decision']
        criteria_summary = result['criteria_summary']
        criteria_counts = result['criteria_counts']
        
        # Count criteria assessments
        yes_count = criteria_counts['YES']
        no_count = criteria_counts['NO']
        unclear_count = criteria_counts['UNCLEAR']
        
        # Pattern: (YES, NO, UNCLEAR) -> Decision
        pattern = f"({yes_count}Y, {no_count}N, {unclear_count}U)"
        decision_patterns[pattern].append({
            'paper_id': paper_id,
            'ai_decision': ai_decision,
            'expected': expected,
            'criteria_summary': criteria_summary
        })
        
        # Check for logic violations: NO criteria but not EXCLUDE
        if no_count > 0 and ai_decision != "EXCLUDE":
            logic_violations.append({
                'paper_id': paper_id,
                'ai_decision': ai_decision,
                'expected': expected,
                'no_count': no_count,
                'criteria_summary': criteria_summary,
                'reasoning': result.get('decision_reasoning', 'No reasoning')
            })
    
    print(f"DECISION PATTERN ANALYSIS:")
    print(f"Total papers analyzed: {len(results)}")
    print()
    
    # Sort patterns by decision logic
    for pattern in sorted(decision_patterns.keys()):
        papers = decision_patterns[pattern]
        decisions = defaultdict(int)
        for paper in papers:
            decisions[paper['ai_decision']] += 1
        
        print(f"Pattern {pattern}:")
        for decision, count in decisions.items():
            print(f"  {decision}: {count} papers")
        
        # Show examples if there are logic violations
        violation_examples = [p for p in papers if 'N' in pattern and '0N' not in pattern and p['ai_decision'] != 'EXCLUDE']
        if violation_examples:
            print(f"  ⚠️  LOGIC VIOLATIONS:")
            for ex in violation_examples[:3]:  # Show first 3
                print(f"    {ex['paper_id']}: {ex['ai_decision']} (Expected: {ex['expected']})")
        print()
    
    print(f"\nDETAILED LOGIC VIOLATIONS:")
    print("=" * 60)
    
    if not logic_violations:
        print("✅ No logic violations found! All papers with NO criteria correctly resulted in EXCLUDE.")
    else:
        print(f"❌ Found {len(logic_violations)} logic violations:")
        print()
        
        for i, violation in enumerate(logic_violations, 1):
            print(f"{i}. Paper: {violation['paper_id']}")
            print(f"   AI Decision: {violation['ai_decision']} (should be EXCLUDE)")
            print(f"   Expected: {violation['expected']}")
            print(f"   NO criteria count: {violation['no_count']}")
            print(f"   Criteria with NO:")
            
            for criterion, assessment in violation['criteria_summary'].items():
                if assessment == "NO":
                    print(f"     - {criterion}: NO")
            
            print(f"   AI Reasoning: {violation['reasoning'][:100]}...")
            print()
    
    # Analyze MAYBE decisions
    maybe_decisions = [r for r in results if r['ai_decision'] == 'MAYBE']
    print(f"\nMAYBE DECISION ANALYSIS:")
    print("=" * 60)
    print(f"Total MAYBE decisions: {len(maybe_decisions)}")
    
    maybe_with_no = [m for m in maybe_decisions if m['criteria_counts']['NO'] > 0]
    maybe_only_unclear = [m for m in maybe_decisions if m['criteria_counts']['NO'] == 0]
    
    print(f"MAYBE with NO criteria (violations): {len(maybe_with_no)}")
    print(f"MAYBE with only UNCLEAR criteria (correct): {len(maybe_only_unclear)}")
    print()
    
    if maybe_with_no:
        print("MAYBE decisions that should be EXCLUDE:")
        for decision in maybe_with_no[:5]:  # Show first 5
            print(f"  {decision['paper_id']}: {decision['criteria_counts']['NO']} NO criteria")
    
    # Analyze EXCLUDE decisions  
    exclude_decisions = [r for r in results if r['ai_decision'] == 'EXCLUDE']
    print(f"\nEXCLUDE DECISION ANALYSIS:")
    print("=" * 60)
    print(f"Total EXCLUDE decisions: {len(exclude_decisions)}")
    
    exclude_patterns = defaultdict(int)
    for decision in exclude_decisions:
        counts = decision['criteria_counts']
        pattern = f"({counts['YES']}Y, {counts['NO']}N, {counts['UNCLEAR']}U)"
        exclude_patterns[pattern] += 1
    
    print("EXCLUDE decision patterns:")
    for pattern, count in sorted(exclude_patterns.items()):
        print(f"  {pattern}: {count} papers")
    
    # Check if any EXCLUDE decisions have 0 NO criteria (should these be MAYBE?)
    exclude_no_no = [e for e in exclude_decisions if e['criteria_counts']['NO'] == 0]
    if exclude_no_no:
        print(f"\n⚠️  EXCLUDE decisions with 0 NO criteria (questionable): {len(exclude_no_no)}")
        for decision in exclude_no_no[:3]:
            print(f"  {decision['paper_id']}: {decision['criteria_counts']}")


if __name__ == "__main__":
    analyze_decision_logic()
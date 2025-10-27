#!/usr/bin/env python3
"""
Analyze current MAYBE decisions from validation results.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict

def analyze_maybe_decisions():
    """Analyze current MAYBE decisions to understand patterns and potential improvements."""
    
    print("📋 MAYBE DECISIONS ANALYSIS")
    print("=" * 35)
    print()
    
    # Load validation results
    results_file = Path("data/output/structured_validation_results.json")
    
    if not results_file.exists():
        print("❌ No validation results found. Run validation first.")
        return
    
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Count decision types
    decision_counts = Counter()
    maybe_papers = []
    
    for result in results:
        ai_decision = result.get('ai_decision', 'UNKNOWN')
        decision_counts[ai_decision] += 1
        
        if ai_decision == 'MAYBE':
            maybe_papers.append(result)
    
    # Overall statistics
    total_papers = len(results)
    maybe_count = decision_counts['MAYBE']
    maybe_rate = maybe_count / total_papers * 100 if total_papers > 0 else 0
    
    print("📊 DECISION DISTRIBUTION:")
    for decision, count in sorted(decision_counts.items()):
        rate = count / total_papers * 100 if total_papers > 0 else 0
        print(f"   {decision}: {count} papers ({rate:.1f}%)")
    
    print(f"\n🎯 MAYBE FOCUS: {maybe_count} papers ({maybe_rate:.1f}%)")
    print()
    
    if maybe_count == 0:
        print("✅ No MAYBE decisions found - all papers are clear INCLUDE/EXCLUDE!")
        return
    
    # Analyze MAYBE patterns
    print("🔍 MAYBE DECISION PATTERNS:")
    print("=" * 30)
    
    # Group by criteria patterns
    unclear_patterns = defaultdict(list)
    no_criteria_maybe = []
    
    for paper in maybe_papers:
        criteria_counts = paper.get('criteria_counts', {})
        yes_count = criteria_counts.get('YES', 0)
        no_count = criteria_counts.get('NO', 0)
        unclear_count = criteria_counts.get('UNCLEAR', 0)
        
        # Check for logic violations (MAYBE with NO criteria)
        if no_count > 0:
            no_criteria_maybe.append(paper)
        
        # Pattern analysis
        pattern = f"{yes_count}Y/{no_count}N/{unclear_count}U"
        unclear_patterns[pattern].append(paper)
    
    # Show patterns
    print("📈 CRITERIA PATTERNS:")
    for pattern, papers in sorted(unclear_patterns.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(papers)
        print(f"   {pattern}: {count} papers")
        
        # Show a few examples
        for i, paper in enumerate(papers[:2]):
            title = paper.get('title', 'No title')[:60]
            print(f"     • {paper['paper_id']}: {title}...")
        
        if count > 2:
            print(f"     ... and {count-2} more")
        print()
    
    # Logic violations check
    if no_criteria_maybe:
        print("⚠️  LOGIC VIOLATIONS (MAYBE with NO criteria):")
        print(f"   Found {len(no_criteria_maybe)} papers that should be EXCLUDE")
        for violation in no_criteria_maybe[:5]:
            counts = violation['criteria_counts']
            print(f"   • {violation['paper_id']}: {counts['YES']}Y/{counts['NO']}N/{counts['UNCLEAR']}U")
        print()
    
    # Analyze specific UNCLEAR criteria causing MAYBE decisions
    print("🔬 UNCLEAR CRITERIA ANALYSIS:")
    print("=" * 35)
    
    unclear_criteria_counts = defaultdict(int)
    
    for paper in maybe_papers:
        criteria_summary = paper.get('criteria_summary', {})
        for criterion, assessment in criteria_summary.items():
            if assessment == 'UNCLEAR':
                unclear_criteria_counts[criterion] += 1
    
    print("Most problematic criteria (causing UNCLEAR assessments):")
    for criterion, count in sorted(unclear_criteria_counts.items(), key=lambda x: x[1], reverse=True):
        rate = count / maybe_count * 100 if maybe_count > 0 else 0
        print(f"   {criterion}: {count}/{maybe_count} ({rate:.1f}%)")
    
    print()
    
    # Detailed examples of MAYBE papers
    print("📋 SAMPLE MAYBE DECISIONS FOR REVIEW:")
    print("=" * 40)
    
    # Show a few representative examples
    example_count = min(5, len(maybe_papers))
    for i, paper in enumerate(maybe_papers[:example_count], 1):
        print(f"\n{i}. Paper ID: {paper['paper_id']}")
        print(f"   Title: {paper.get('title', 'No title')}")
        print(f"   Expected: {paper.get('expected_decision', 'Unknown')}")
        
        counts = paper.get('criteria_counts', {})
        print(f"   Criteria: {counts.get('YES', 0)}Y/{counts.get('NO', 0)}N/{counts.get('UNCLEAR', 0)}U")
        
        # Show which criteria are UNCLEAR
        criteria_summary = paper.get('criteria_summary', {})
        unclear_criteria = [k for k, v in criteria_summary.items() if v == 'UNCLEAR']
        if unclear_criteria:
            print(f"   UNCLEAR: {', '.join(unclear_criteria)}")
        
        reasoning = paper.get('decision_reasoning', 'No reasoning')
        print(f"   Reasoning: {reasoning[:100]}...")
        
        if i < example_count:
            print("   " + "-" * 50)
    
    # Summary and recommendations
    print(f"\n💡 ANALYSIS SUMMARY:")
    print("=" * 25)
    
    if maybe_rate > 30:
        print("⚠️  HIGH MAYBE RATE: Consider prompt improvements to reduce ambiguity")
    elif maybe_rate > 15:
        print("🟡 MODERATE MAYBE RATE: Some optimization possible")
    else:
        print("✅ REASONABLE MAYBE RATE: Current prompts performing well")
    
    # Top problematic criteria
    if unclear_criteria_counts:
        top_problematic = max(unclear_criteria_counts.items(), key=lambda x: x[1])
        print(f"🎯 TOP ISSUE: '{top_problematic[0]}' unclear in {top_problematic[1]} papers")
    
    if no_criteria_maybe:
        print(f"⚠️  LOGIC ISSUE: {len(no_criteria_maybe)} papers need decision logic fix")
    
    print(f"\n🔧 RECOMMENDATIONS:")
    
    # Specific recommendations based on patterns
    if 'dual_component' in unclear_criteria_counts and unclear_criteria_counts['dual_component'] > maybe_count * 0.3:
        print("• Consider removing dual_component criterion (redundant)")
    
    if 'study_design' in unclear_criteria_counts and unclear_criteria_counts['study_design'] > maybe_count * 0.2:
        print("• Enhance study design examples in prompt")
    
    if 'outcomes' in unclear_criteria_counts and unclear_criteria_counts['outcomes'] > maybe_count * 0.2:
        print("• Clarify outcome examples in prompt")
    
    if no_criteria_maybe:
        print("• Fix decision logic to enforce: ANY NO → EXCLUDE")
    
    if maybe_rate > 20:
        print("• Add more few-shot examples for borderline cases")
    
    print("\n💾 Analysis complete - review MAYBE papers above for prompt improvements")

if __name__ == "__main__":
    analyze_maybe_decisions()

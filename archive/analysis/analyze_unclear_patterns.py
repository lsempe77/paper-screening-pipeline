#!/usr/bin/env python3
"""
Analyze papers with high UNCLEAR rates to understand prompt restrictiveness.
"""

import json
import sys
from pathlib import Path

def analyze_unclear_patterns():
    """Analyze validation results focusing on high UNCLEAR rates."""
    
    results_file = Path("data/output/structured_validation_results.json")
    
    if not results_file.exists():
        print("❌ No validation results found. Run validation first.")
        return
    
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print("ANALYZING HIGH UNCLEAR RATE PATTERNS")
    print("=" * 60)
    print()
    
    # Analyze all papers for UNCLEAR patterns
    unclear_analysis = []
    
    for result in results:
        if isinstance(result, dict) and 'criteria_summary' in result:
            paper_id = result.get('paper_id', 'unknown')
            criteria_summary = result['criteria_summary']
            
            # Count assessments from criteria_summary
            yes_count = sum(1 for val in criteria_summary.values() if val == 'YES')
            no_count = sum(1 for val in criteria_summary.values() if val == 'NO')
            unclear_count = sum(1 for val in criteria_summary.values() if val == 'UNCLEAR')
            total = len(criteria_summary)
            
            unclear_rate = unclear_count / total if total > 0 else 0
            
            unclear_analysis.append({
                'paper_id': paper_id,
                'unclear_count': unclear_count,
                'unclear_rate': unclear_rate,
                'total_criteria': total,
                'yes_count': yes_count,
                'no_count': no_count,
                'decision': result.get('ai_decision', 'UNKNOWN'),
                'expected_decision': result.get('expected_decision', 'UNKNOWN'),
                'criteria_summary': criteria_summary,
                'decision_reasoning': result.get('decision_reasoning', '')
            })
    
    # Sort by unclear rate (highest first)
    unclear_analysis.sort(key=lambda x: x['unclear_rate'], reverse=True)
    
    # Find papers with high UNCLEAR rates (>= 50%)
    high_unclear_papers = [p for p in unclear_analysis if p['unclear_rate'] >= 0.5]
    
    print(f"PAPERS WITH HIGH UNCLEAR RATES (≥50%):")
    print(f"Found {len(high_unclear_papers)} papers out of {len(unclear_analysis)} total")
    print()
    
    # Show top 10 most unclear papers
    print("TOP 10 MOST UNCLEAR PAPERS:")
    print("Paper ID    | UNCLEAR Rate | Y  N  U | Decision | Pattern")
    print("-" * 60)
    
    for i, paper in enumerate(high_unclear_papers[:10]):
        rate_pct = paper['unclear_rate'] * 100
        pattern = f"{paper['yes_count']}Y {paper['no_count']}N {paper['unclear_count']}U"
        print(f"{paper['paper_id']:11} | {rate_pct:8.1f}%    | {pattern:7} | {paper['decision']:8} |")
    
    print()
    
    # Analyze which criteria are most often UNCLEAR
    criteria_unclear_counts = {}
    criteria_total_counts = {}
    
    for paper in unclear_analysis:
        for criterion, assessment_val in paper['criteria_summary'].items():
            if criterion not in criteria_unclear_counts:
                criteria_unclear_counts[criterion] = 0
                criteria_total_counts[criterion] = 0
            
            criteria_total_counts[criterion] += 1
            if assessment_val == 'UNCLEAR':
                criteria_unclear_counts[criterion] += 1
    
    print("CRITERIA WITH HIGHEST UNCLEAR RATES:")
    print("Criterion                          | UNCLEAR Rate | Count")
    print("-" * 60)
    
    criteria_rates = []
    for criterion, unclear_count in criteria_unclear_counts.items():
        total_count = criteria_total_counts[criterion]
        rate = unclear_count / total_count if total_count > 0 else 0
        criteria_rates.append((criterion, rate, unclear_count, total_count))
    
    criteria_rates.sort(key=lambda x: x[1], reverse=True)
    
    for criterion, rate, unclear_count, total_count in criteria_rates:
        rate_pct = rate * 100
        criterion_short = criterion.replace('_', ' ')[:30]
        print(f"{criterion_short:30} | {rate_pct:8.1f}%    | {unclear_count:2}/{total_count:2}")
    
    print()
    
    # Analyze reasoning patterns for high UNCLEAR papers
    print("SAMPLE UNCLEAR REASONING ANALYSIS:")
    print("-" * 40)
    
    sample_papers = high_unclear_papers[:3]
    for paper in sample_papers:
        print(f"\nPaper {paper['paper_id']} ({paper['unclear_count']}/{paper['total_criteria']} UNCLEAR):")
        print(f"Decision: {paper['decision']} (Expected: {paper['expected_decision']})")
        print(f"Reasoning: {paper['decision_reasoning'][:200]}...")
        
        unclear_criteria = [k for k, v in paper['criteria_summary'].items() if v == 'UNCLEAR']
        print(f"UNCLEAR criteria: {', '.join(unclear_criteria[:3])}")  # Show first 3
    
    print()
    
    # Summary and recommendations
    print("ANALYSIS SUMMARY:")
    print("-" * 20)
    total_papers = len(unclear_analysis)
    high_unclear_count = len(high_unclear_papers)
    high_unclear_pct = (high_unclear_count / total_papers) * 100 if total_papers > 0 else 0
    
    print(f"• {high_unclear_count}/{total_papers} papers ({high_unclear_pct:.1f}%) have ≥50% UNCLEAR criteria")
    
    avg_unclear_rate = sum(p['unclear_rate'] for p in unclear_analysis) / len(unclear_analysis) if unclear_analysis else 0
    print(f"• Average UNCLEAR rate across all papers: {avg_unclear_rate*100:.1f}%")
    
    print()
    print("POTENTIAL ISSUES IDENTIFIED:")
    if high_unclear_pct > 20:
        print("❌ HIGH UNCLEAR RATE: >20% of papers have majority UNCLEAR criteria")
        print("   → Suggests prompts may be too restrictive")
        print("   → AI may need better guidance on what constitutes sufficient evidence")
    
    if criteria_rates and criteria_rates[0][1] > 0.7:
        worst_criterion = criteria_rates[0][0].replace('_', ' ')
        print(f"❌ PROBLEMATIC CRITERION: '{worst_criterion}' is UNCLEAR in >70% of cases")
        print("   → This criterion may need clearer definition or examples")
    
    print()
    print("RECOMMENDATIONS:")
    print("1. ADD FEW-SHOT EXAMPLES: Show concrete examples of YES/NO/UNCLEAR assessments")
    print("2. CLARIFY EVIDENCE STANDARDS: Define what constitutes 'sufficient' vs 'insufficient' evidence")
    print("3. PROVIDE CRITERION-SPECIFIC GUIDANCE: Add examples for problematic criteria")
    print("4. BALANCE CONSERVATISM: Ensure 'be conservative' doesn't lead to excessive UNCLEAR classifications")

if __name__ == "__main__":
    analyze_unclear_patterns()
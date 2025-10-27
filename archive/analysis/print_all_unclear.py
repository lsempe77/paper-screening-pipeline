#!/usr/bin/env python3
"""
Print all papers with UNCLEAR criteria in detail.
"""

import json
from pathlib import Path

def print_all_unclear_details():
    """Print detailed breakdown of all UNCLEAR patterns."""
    
    print("COMPLETE UNCLEAR CRITERIA ANALYSIS")
    print("=" * 50)
    print()
    
    # Load original validation results
    results_file = Path("data/output/structured_validation_results.json")
    if not results_file.exists():
        print("❌ Validation results not found.")
        return
    
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print(f"📊 Analyzing {len(results)} papers for UNCLEAR patterns")
    print()
    
    # Organize papers by UNCLEAR count
    unclear_groups = {}
    
    for result in results:
        if 'criteria_summary' not in result:
            continue
            
        criteria = result['criteria_summary']
        unclear_count = sum(1 for v in criteria.values() if v == 'UNCLEAR')
        
        if unclear_count not in unclear_groups:
            unclear_groups[unclear_count] = []
        
        unclear_groups[unclear_count].append({
            'paper_id': result['paper_id'],
            'title': result.get('title', 'No title'),
            'decision': result.get('ai_decision', 'UNKNOWN'),
            'expected': result.get('expected_decision', 'UNKNOWN'),
            'criteria': criteria,
            'unclear_count': unclear_count,
            'reasoning': result.get('decision_reasoning', '')
        })
    
    # Print by UNCLEAR count (highest first)
    for unclear_count in sorted(unclear_groups.keys(), reverse=True):
        papers = unclear_groups[unclear_count]
        
        print(f"🔍 PAPERS WITH {unclear_count}/8 UNCLEAR CRITERIA ({len(papers)} papers)")
        print("-" * 60)
        
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. Paper ID: {paper['paper_id']}")
            print(f"   Title: {paper['title'][:80]}...")
            print(f"   Decision: {paper['decision']} (Expected: {paper['expected']})")
            
            # Show criteria breakdown
            criteria_display = []
            unclear_criteria = []
            
            for criterion, assessment in paper['criteria'].items():
                if assessment == 'YES':
                    criteria_display.append(f"✅ {criterion}")
                elif assessment == 'NO':
                    criteria_display.append(f"❌ {criterion}")
                elif assessment == 'UNCLEAR':
                    criteria_display.append(f"❓ {criterion}")
                    unclear_criteria.append(criterion)
            
            print(f"   Criteria: {', '.join(criteria_display)}")
            
            if unclear_criteria:
                print(f"   UNCLEAR: {', '.join(unclear_criteria)}")
            
            # Show reasoning if it's a parsing failure
            if 'Failed to parse' in paper['reasoning']:
                print(f"   Issue: JSON parsing failure")
            elif unclear_count >= 6:
                print(f"   Issue: High uncertainty - may need better guidance")
            
            if i >= 3 and len(papers) > 3:  # Show max 3 per group unless small group
                remaining = len(papers) - 3
                print(f"\n   ... and {remaining} more papers with {unclear_count} UNCLEAR criteria")
                break
        
        print()
    
    # Show criterion-specific UNCLEAR rates
    print("📈 CRITERION-SPECIFIC UNCLEAR RATES:")
    print("-" * 40)
    
    criterion_unclear_counts = {}
    criterion_total_counts = {}
    
    for result in results:
        if 'criteria_summary' not in result:
            continue
            
        for criterion, assessment in result['criteria_summary'].items():
            if criterion not in criterion_unclear_counts:
                criterion_unclear_counts[criterion] = 0
                criterion_total_counts[criterion] = 0
            
            criterion_total_counts[criterion] += 1
            if assessment == 'UNCLEAR':
                criterion_unclear_counts[criterion] += 1
    
    # Sort by UNCLEAR rate
    criterion_rates = []
    for criterion in criterion_unclear_counts:
        unclear_count = criterion_unclear_counts[criterion]
        total_count = criterion_total_counts[criterion]
        rate = (unclear_count / total_count) * 100 if total_count > 0 else 0
        criterion_rates.append((criterion, rate, unclear_count, total_count))
    
    criterion_rates.sort(key=lambda x: x[1], reverse=True)
    
    print("Criterion                     | UNCLEAR Rate | Count  | Details")
    print("-" * 65)
    
    for criterion, rate, unclear_count, total_count in criterion_rates:
        criterion_name = criterion.replace('_', ' ')[:25].ljust(25)
        rate_str = f"{rate:6.1f}%"
        count_str = f"{unclear_count:2}/{total_count:2}"
        
        # Add interpretation
        if rate > 50:
            detail = "🔴 CRITICAL - needs improvement"
        elif rate > 40:
            detail = "🟡 HIGH - review guidance"
        elif rate > 30:
            detail = "🟠 MODERATE - acceptable"
        else:
            detail = "🟢 GOOD - working well"
        
        print(f"{criterion_name} | {rate_str:>11} | {count_str:>6} | {detail}")
    
    print()
    
    # Show specific examples of high UNCLEAR papers
    print("🔍 DETAILED EXAMPLES OF PROBLEMATIC PAPERS:")
    print("-" * 45)
    
    # Find papers with 6+ UNCLEAR criteria
    high_unclear_papers = []
    for unclear_count in unclear_groups:
        if unclear_count >= 6:
            high_unclear_papers.extend(unclear_groups[unclear_count])
    
    # Show top 5 most problematic
    for i, paper in enumerate(high_unclear_papers[:5], 1):
        print(f"\nExample {i}: {paper['paper_id']} ({paper['unclear_count']}/8 UNCLEAR)")
        print(f"Title: {paper['title'][:100]}...")
        print(f"Decision: {paper['decision']} | Expected: {paper['expected']}")
        
        # List each UNCLEAR criterion
        unclear_criteria = [k for k, v in paper['criteria'].items() if v == 'UNCLEAR']
        for criterion in unclear_criteria:
            criterion_name = criterion.replace('_', ' ')
            print(f"  ❓ {criterion_name}")
        
        # Show reasoning excerpt
        reasoning = paper['reasoning'][:150]
        if 'Failed to parse' in reasoning:
            print(f"  Issue: JSON parsing failure")
        else:
            print(f"  Reasoning: {reasoning}...")
    
    print()
    
    # Summary statistics
    total_papers = len(results)
    high_unclear_papers_count = sum(len(papers) for unclear_count, papers in unclear_groups.items() if unclear_count >= 4)
    
    print("📊 SUMMARY STATISTICS:")
    print("-" * 22)
    print(f"• Total papers analyzed: {total_papers}")
    print(f"• Papers with ≥4 UNCLEAR criteria: {high_unclear_papers_count}")
    print(f"• Highest UNCLEAR rate criterion: {criterion_rates[0][0]} ({criterion_rates[0][1]:.1f}%)")
    print(f"• Papers with 8/8 UNCLEAR (complete failures): {len(unclear_groups.get(8, []))}")
    print(f"• Papers with 0 UNCLEAR (perfect clarity): {len(unclear_groups.get(0, []))}")

if __name__ == "__main__":
    print_all_unclear_details()
#!/usr/bin/env python3
"""
Quick Decision Analysis Tool
Extracts exact counts of Include/Exclude/Maybe decisions per engine and combined.
"""

import json
import sys
from collections import defaultdict, Counter

def analyze_decisions(results_file):
    """Analyze decision patterns from dual-engine results."""
    
    print("📊 DETAILED DECISION ANALYSIS")
    print("=" * 30)
    
    # Load results
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading results: {e}")
        return
    
    results = data['results']
    metadata = data['metadata']
    
    print(f"📄 Total Papers: {len(results)}")
    print(f"🤖 Engine 1: {metadata['engine1_model']}")
    print(f"🤖 Engine 2: {metadata['engine2_model']}")
    print()
    
    # Count decisions per engine
    engine1_decisions = Counter()
    engine2_decisions = Counter()
    agreement_patterns = Counter()
    
    successful_pairs = 0
    
    for result in results:
        # Engine 1 decisions
        if result.get('engine1', {}).get('success', False):
            decision1 = result['engine1']['decision']
            engine1_decisions[decision1] += 1
        
        # Engine 2 decisions  
        if result.get('engine2', {}).get('success', False):
            decision2 = result['engine2']['decision']
            engine2_decisions[decision2] += 1
        
        # Agreement patterns (only for successful pairs)
        if (result.get('comparison', {}).get('both_success', False)):
            successful_pairs += 1
            decision1 = result['engine1']['decision']
            decision2 = result['engine2']['decision']
            
            if decision1 == decision2:
                agreement_patterns[f"AGREE: {decision1}"] += 1
            else:
                agreement_patterns[f"DISAGREE: {decision1} vs {decision2}"] += 1
    
    # Print Engine 1 results
    print(f"🤖 {metadata['engine1_model']} DECISIONS:")
    total1 = sum(engine1_decisions.values())
    for decision in ['include', 'exclude', 'maybe', 'error']:
        count = engine1_decisions[decision]
        pct = (count / total1 * 100) if total1 > 0 else 0
        print(f"   {decision.upper()}: {count:,} ({pct:.1f}%)")
    print(f"   TOTAL: {total1:,}")
    print()
    
    # Print Engine 2 results
    print(f"🤖 {metadata['engine2_model']} DECISIONS:")
    total2 = sum(engine2_decisions.values())
    for decision in ['include', 'exclude', 'maybe', 'error']:
        count = engine2_decisions[decision]
        pct = (count / total2 * 100) if total2 > 0 else 0
        print(f"   {decision.upper()}: {count:,} ({pct:.1f}%)")
    print(f"   TOTAL: {total2:,}")
    print()
    
    # Agreement/Disagreement breakdown
    print("🤝 AGREEMENT PATTERNS:")
    agreements = 0
    disagreements = 0
    
    for pattern, count in agreement_patterns.most_common():
        pct = (count / successful_pairs * 100) if successful_pairs > 0 else 0
        print(f"   {pattern}: {count:,} ({pct:.1f}%)")
        
        if pattern.startswith("AGREE"):
            agreements += count
        else:
            disagreements += count
    
    print()
    print(f"✅ Total Agreements: {agreements:,} ({agreements/successful_pairs*100:.1f}%)")
    print(f"⚠️  Total Disagreements: {disagreements:,} ({disagreements/successful_pairs*100:.1f}%)")
    print(f"📊 Successful Pairs: {successful_pairs:,}")
    
    # Combined decision analysis (consensus where they agree)
    print(f"\n🎯 CONSENSUS DECISIONS (Where Both Engines Agree):")
    consensus_decisions = Counter()
    
    for result in results:
        if result.get('comparison', {}).get('agreement', False) and result.get('comparison', {}).get('both_success', False):
            # Both engines agree and succeeded
            decision = result['engine1']['decision']  # Same as engine2 since they agree
            consensus_decisions[decision] += 1
    
    total_consensus = sum(consensus_decisions.values())
    for decision in ['include', 'exclude', 'maybe']:
        count = consensus_decisions[decision]
        pct = (count / total_consensus * 100) if total_consensus > 0 else 0
        print(f"   {decision.upper()}: {count:,} ({pct:.1f}%)")
    print(f"   TOTAL CONSENSUS: {total_consensus:,}")
    
    # Disagreement cases require human review
    print(f"\n🔍 HUMAN REVIEW REQUIRED:")
    print(f"   Papers with disagreements: {disagreements:,}")
    print(f"   Estimated review time: {disagreements * 0.5:.1f} hours")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python decision_analysis.py <results_file.json>")
        sys.exit(1)
    
    analyze_decisions(sys.argv[1])
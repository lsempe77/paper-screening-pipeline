#!/usr/bin/env python3
"""
Analyze whether dual component criterion is redundant.
"""

print("DUAL COMPONENT CRITERION REDUNDANCY ANALYSIS")
print("=" * 55)
print()

print("🤔 THE QUESTION:")
print("If we already assess:")
print("• Component A (cash/consumption support): YES/NO/UNCLEAR")
print("• Component B (productive assets): YES/NO/UNCLEAR")
print()
print("Is 'Dual Component' criterion redundant?")
print("Couldn't we just derive it logically as: Component A = YES AND Component B = YES?")
print()

print("📊 CURRENT LOGIC vs PROPOSED LOGIC:")
print()
print("CURRENT (3 separate criteria):")
print("1. Component A (cash): [YES/NO/UNCLEAR]")
print("2. Component B (assets): [YES/NO/UNCLEAR]") 
print("3. Dual component: [YES/NO/UNCLEAR]")
print()
print("PROPOSED (2 criteria + derived logic):")
print("1. Component A (cash): [YES/NO/UNCLEAR]")
print("2. Component B (assets): [YES/NO/UNCLEAR]")
print("3. Dual component: AUTO-DERIVED = (A=YES AND B=YES)")
print()

print("🔍 ANALYZING ACTUAL VALIDATION DATA:")
print()

# Look at the validation results to see patterns
import json
from pathlib import Path

results_file = Path("data/output/structured_validation_results.json")
if results_file.exists():
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    logical_mismatches = []
    unclear_patterns = []
    
    for result in results:
        if 'criteria_summary' in result:
            comp_a = result['criteria_summary'].get('component_a_cash', 'UNKNOWN')
            comp_b = result['criteria_summary'].get('component_b_assets', 'UNKNOWN') 
            dual = result['criteria_summary'].get('dual_component', 'UNKNOWN')
            
            # Check logical consistency
            expected_dual = "YES" if (comp_a == "YES" and comp_b == "YES") else "NO" if (comp_a == "NO" or comp_b == "NO") else "UNCLEAR"
            
            if dual != expected_dual and dual != "UNKNOWN":
                logical_mismatches.append({
                    'paper_id': result.get('paper_id', 'unknown'),
                    'comp_a': comp_a,
                    'comp_b': comp_b,
                    'dual_actual': dual,
                    'dual_expected': expected_dual
                })
            
            # Track unclear patterns
            if dual == "UNCLEAR":
                unclear_patterns.append({
                    'paper_id': result.get('paper_id', 'unknown'),
                    'comp_a': comp_a,
                    'comp_b': comp_b,
                    'dual': dual
                })
    
    print(f"LOGICAL CONSISTENCY CHECK:")
    print(f"• Total papers analyzed: {len(results)}")
    print(f"• Logical mismatches found: {len(logical_mismatches)}")
    print(f"• Papers with dual=UNCLEAR: {len(unclear_patterns)}")
    print()
    
    if logical_mismatches:
        print("LOGICAL MISMATCHES (dual ≠ expected from A&B):")
        for i, mismatch in enumerate(logical_mismatches[:5]):
            print(f"  {i+1}. {mismatch['paper_id']}: A={mismatch['comp_a']}, B={mismatch['comp_b']}")
            print(f"     Actual dual={mismatch['dual_actual']}, Expected={mismatch['dual_expected']}")
        print()
    
    # Analyze unclear patterns
    unclear_breakdown = {}
    for pattern in unclear_patterns:
        key = f"A={pattern['comp_a']}, B={pattern['comp_b']}"
        unclear_breakdown[key] = unclear_breakdown.get(key, 0) + 1
    
    print("UNCLEAR DUAL COMPONENT PATTERNS:")
    for pattern, count in unclear_breakdown.items():
        print(f"  {pattern}: {count} papers")
    print()

print("💡 REDUNDANCY ANALYSIS:")
print()

print("CASE 1: Component A=YES, Component B=YES")
print("→ Dual component MUST be YES (both components present)")
print("→ Redundant assessment!")
print()

print("CASE 2: Component A=NO or Component B=NO") 
print("→ Dual component MUST be NO (missing at least one component)")
print("→ Redundant assessment!")
print()

print("CASE 3: Component A=UNCLEAR or Component B=UNCLEAR")
print("→ Dual component SHOULD be UNCLEAR (insufficient info about components)")
print("→ Could be logically derived!")
print()

print("🎯 RECOMMENDATIONS:")
print()

print("OPTION 1: REMOVE DUAL COMPONENT CRITERION")
print("✅ Simplify from 8 to 7 criteria")
print("✅ Reduce redundancy and potential inconsistency")
print("✅ Auto-derive dual status: (A=YES AND B=YES)")
print("✅ Reduce AI confusion and UNCLEAR rates")
print()

print("OPTION 2: KEEP BUT REFRAME DUAL COMPONENT")
print("• Focus on whether components are described as SEPARATE/DISTINCT")
print("• Assess integration vs independence of components")
print("• But this adds complexity...")
print()

print("OPTION 3: MERGE INTO SINGLE 'PROGRAM COMPONENTS' CRITERION")
print("• Single assessment: Does program include BOTH cash AND assets?")
print("• Simpler logic, clearer assessment")
print("• Reduces from 3 criteria to 1")
print()

print("🏆 RECOMMENDED APPROACH:")
print()
print("Remove 'dual component' as separate criterion because:")
print("1. It's logically redundant (derivable from A & B)")
print("2. It's the highest UNCLEAR rate criterion (55.7%)")
print("3. It adds confusion without additional information")
print("4. Simplification will improve AI performance")
print()
print("NEW STRUCTURE:")
print("1. Component A (cash/consumption support)")
print("2. Component B (productive assets)")
print("3. [AUTO-DERIVED] Dual component = (A=YES AND B=YES)")
print()
print("This maintains all necessary information while eliminating redundancy!")

if __name__ == "__main__":
    pass
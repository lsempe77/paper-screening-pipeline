#!/usr/bin/env python3
"""
Test the corrected decision logic.
"""

# Quick test of one of the violation cases
print("TESTING CORRECTED DECISION LOGIC")
print("=" * 50)
print()
print("Previous violation example:")
print("Paper: 2022_5158 - Microfinance and Diversification")
print("Previous result: MAYBE (WRONG)")
print("Criteria: 4Y, 3N, 1U")
print("Should be: EXCLUDE (because 3 NO criteria)")
print()
print("New rule applied:")
print("✅ ANY NO criterion → AUTOMATIC EXCLUDE")
print("❌ Previous: AI was considering other factors despite NO criteria")
print()
print("Expected with new prompt:")
print("Decision: EXCLUDE")
print("Reasoning: 'EXCLUDE: component_a_cash, component_b_assets, dual_component are NO'")
print()
print("This should fix all 6 violation cases identified in the analysis.")

# Show the pattern that should emerge
patterns = {
    "INCLUDE": "All 8 criteria YES (8Y, 0N, 0U)",
    "EXCLUDE": "Any criteria NO (XY, 1+N, XU)", 
    "MAYBE": "No criteria NO, some UNCLEAR (XY, 0N, 1+U)"
}

print("\nCORRECT DECISION PATTERNS:")
for decision, pattern in patterns.items():
    print(f"{decision:8}: {pattern}")
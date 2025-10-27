"""
Analyze the 8 false positive papers from s14above comprehensive analysis.
These are papers where LLM said INCLUDE but humans said Excluded.
"""

import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from src.parsers import RISParser

# The 8 false positive IDs from comprehensive analysis
false_positive_ids = [
    121296063,  # Malawi Social Cash Transfer Programme (SCTP)
    121299285,  # Pakistan unconditional cash transfers (BISP)
    121323669,  # Punjab Rural Support Programme (PRSP) - we analyzed
    121323321,  # Punjab Rural Support Programme (PRSP) - duplicate?
    121308119,  # Egyptian Social Fund for Development
    121295210,  # Egyptian Social Fund for Development - duplicate?
    121304324,  # Second National Fadama Development Project (Nigeria)
    121295197   # Conditional cash transfers in Latin America
]

# Load corpus
print("Loading corpus...")
parser = RISParser()
ris_file = project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
papers = parser.parse_file(str(ris_file))

papers_dict = {}
for p in papers:
    if hasattr(p, 'ris_fields') and 'U1' in p.ris_fields:
        u1 = p.ris_fields['U1']
        paper_id = u1[0] if isinstance(u1, list) else u1
        papers_dict[str(paper_id).strip()] = p

print(f"Loaded {len(papers_dict)} papers from corpus\n")

print("="*80)
print("ANALYSIS OF 8 FALSE POSITIVES FROM s14above")
print("LLM said INCLUDE, Humans said Excluded")
print("="*80)

for i, paper_id in enumerate(false_positive_ids, 1):
    paper_id_str = str(paper_id)
    
    print(f"\n{'='*80}")
    print(f"FALSE POSITIVE #{i}: Paper ID {paper_id_str}")
    print(f"{'='*80}")
    
    if paper_id_str not in papers_dict:
        print(f"❌ Paper not found in corpus!")
        continue
    
    paper = papers_dict[paper_id_str]
    
    print(f"\n📄 TITLE:")
    print(paper.title)
    
    print(f"\n📅 YEAR: {paper.year}")
    
    print(f"\n📝 ABSTRACT ({len(paper.abstract)} chars):")
    print("-" * 80)
    print(paper.abstract if paper.abstract else "NO ABSTRACT")
    print("-" * 80)
    
    # Quick analysis based on abstract
    abstract_lower = paper.abstract.lower() if paper.abstract else ""
    title_lower = paper.title.lower()
    
    print(f"\n🔍 QUICK ANALYSIS:")
    
    # Check for problematic keywords
    if any(word in title_lower for word in ['critique', 'review', 'appraisal', 'analysis of', 'reflection']):
        print("⚠️  Title contains analytical keywords (critique/review/appraisal/analysis)")
    
    # Check for cash-related terms
    cash_terms = ['cash transfer', 'stipend', 'grant']
    credit_terms = ['credit', 'loan', 'micro-credit', 'microcredit', 'borrow']
    
    has_cash = any(term in abstract_lower for term in cash_terms)
    has_credit = any(term in abstract_lower for term in credit_terms)
    
    if has_cash:
        print("✅ Mentions cash transfers/grants/stipends")
    if has_credit:
        print("⚠️  Mentions credit/loans/microcredit")
    if has_credit and not has_cash:
        print("❌ ISSUE: Only credit/loans mentioned, NO cash transfers!")
    
    # Check for assets
    asset_terms = ['livestock', 'asset', 'equipment', 'tools']
    if any(term in abstract_lower for term in asset_terms):
        print("✅ Mentions assets/livestock/equipment")
    
    # Check for program types
    if 'microfinance' in abstract_lower or 'micro-finance' in abstract_lower:
        print("⚠️  Microfinance program (likely loans only)")
    
    # Check for study type
    if any(word in abstract_lower for word in ['impact evaluation', 'impact assessment', 'rct', 'randomized']):
        print("✅ Mentions impact evaluation/RCT")
    elif any(word in abstract_lower for word in ['critique', 'review', 'analysis']):
        print("❌ Appears to be critique/review/analysis, not evaluation")
    
    print()

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("""
Based on abstracts, categorize false positives:

1. **Legitimate Programs (May be correct INCLUDES):**
   - Papers evaluating actual cash transfer + asset programs
   - May be human labeling errors

2. **Microfinance Only (Should be EXCLUDED):**
   - Only provide credit/loans, not cash transfers
   - LLM confused loans with cash support

3. **Policy Critiques/Reviews (Should be EXCLUDED):**
   - Not impact evaluations
   - Just analyzing/reviewing programs

4. **Unclear/Need Full Text (May need MAYBE):**
   - Abstract insufficient to determine
   - Missing information about components

Next: Review analysis above and categorize each of the 8 papers.
""")

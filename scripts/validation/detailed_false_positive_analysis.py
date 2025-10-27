"""
Detailed analysis of the 2 false positive papers from s14above:
- Paper 121323669: Punjab Rural Support Programme (Pakistan) - LLM says INCLUDE, Human says Excluded
- Paper 121337599: Nigeria's Strategic Plan for Poverty Reduction - LLM says INCLUDE, Human says Excluded

We need to understand:
1. What made the LLM include them?
2. Why did humans exclude them?
3. Which decision is correct?
"""

import sys
from pathlib import Path
import pandas as pd
import yaml

# Add parent directory to path
script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from integrated_screener import IntegratedStructuredScreener
from src.models import Paper, ModelConfig
from src.parsers import RISParser

# Load config
with open(project_dir / 'config' / 'config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# The 2 false positive IDs
false_positive_ids = [121323669, 121337599]

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

# Initialize screener
model_config = ModelConfig(
    provider="openrouter",
    model_name="anthropic/claude-3-haiku",
    temperature=0.1,
    max_tokens=1000,
    api_key=config['openrouter']['api_key']
)
screener = IntegratedStructuredScreener(model_config)

print("="*80)
print("DETAILED ANALYSIS OF FALSE POSITIVES")
print("="*80)

for paper_id in false_positive_ids:
    paper_id_str = str(paper_id)
    
    if paper_id_str not in papers_dict:
        print(f"\n❌ Paper {paper_id_str} not found in corpus!")
        continue
    
    paper = papers_dict[paper_id_str]
    
    print(f"\n{'='*80}")
    print(f"Paper ID: {paper_id_str}")
    print(f"{'='*80}")
    
    print(f"\nTitle: {paper.title}")
    print(f"Year: {paper.year}")
    print(f"Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
    
    print(f"\n📄 FULL ABSTRACT ({len(paper.abstract)} characters):")
    print("-" * 80)
    print(paper.abstract)
    print("-" * 80)
    
    # Screen with LLM
    print("\n🤖 LLM SCREENING RESULTS:")
    result = screener.screen_paper(paper)
    
    print(f"\n**Decision:** {result.final_decision.value.upper()}")
    print(f"**Reasoning:** {result.decision_reasoning}")
    
    # Show all criteria
    print("\n📊 DETAILED CRITERIA ASSESSMENT:")
    criteria_summary = result.get_criteria_summary()
    
    def print_criterion(name, label, assessment_obj):
        status = assessment_obj.assessment
        reasoning = assessment_obj.reasoning
        symbol = "✅" if status == "YES" else ("❌" if status == "NO" else "⚠️")
        print(f"\n{symbol} **{label}:** {status}")
        print(f"   Reasoning: {reasoning}")
    
    print_criterion("program_recognition", "0. Program Recognition (Filter)", result.program_recognition)
    print_criterion("participants_lmic", "1. LMIC Participants", result.participants_lmic)
    print_criterion("component_a_cash", "2. Cash Support Component", result.component_a_cash_support)
    print_criterion("component_b_assets", "3. Productive Assets Component", result.component_b_productive_assets)
    print_criterion("outcomes", "4. Relevant Outcomes", result.relevant_outcomes)
    print_criterion("study_design", "5. Study Design", result.appropriate_study_design)
    print_criterion("year_2004_plus", "6. Publication Year 2004+", result.publication_year_2004_plus)
    print_criterion("completed", "7. Completed Study", result.completed_study)
    
    counts = result.count_criteria_by_status()
    print(f"\n📈 Summary: {counts['YES']} YES, {counts['NO']} NO, {counts['UNCLEAR']} UNCLEAR")
    
    print("\n" + "="*80)
    print("ANALYSIS:")
    print("="*80)
    
    if paper_id == 121323669:
        print("""
**Punjab Rural Support Programme (PRSP) - Pakistan (2004)**

**LLM Decision:** INCLUDE (7 YES, 0 NO, 1 UNCLEAR)
**Human Decision:** Excluded

**Why LLM Included:**
- Program Recognition: YES - identified "Punjab Rural Support Programme" in list
- All 7 criteria marked YES except 1 UNCLEAR
- Follows Rule 0a: Program Recognition YES → INCLUDE

**Why Humans Might Have Excluded:**
- Need to check abstract carefully:
  * Is this actually PRSP implementing cash+assets?
  * Or is it just an "appraisal" study of existing microfinance?
  * Title says "An appraisal of..." suggesting evaluation, not program description
  
**Critical Question:**
Does PRSP in this paper actually provide BOTH:
1. Cash transfers (not just microcredit/loans)
2. Productive assets (not just access to credit)

If PRSP is primarily microcredit (loans, not grants), it should be EXCLUDED.
If abstract shows it's generic microfinance without productive assets, human is correct.
        """)
    
    elif paper_id == 121337599:
        print("""
**Nigeria's Strategic Plan for Poverty Reduction (2010)**

**LLM Decision:** INCLUDE (5 YES, 0 NO, 3 UNCLEAR)
**Human Decision:** Excluded

**Why LLM Included:**
- Program Recognition: YES - identified a program in the list
- No NO criteria, only UNCLEAR
- Follows Rule 0a: Program Recognition YES → INCLUDE

**Why Humans Might Have Excluded:**
- Title: "Economic Policy Reform and Poverty Alleviation: A Critique of..."
- This is a CRITIQUE of the strategic plan, not an impact evaluation
- "Critique" suggests analytical/policy paper, not empirical evaluation
  
**Critical Question:**
1. What program did the LLM identify? (check program_recognition reasoning)
2. Is this an IMPACT EVALUATION or a POLICY CRITIQUE?
3. Does it measure outcomes of a specific program intervention?
4. Does the abstract mention cash transfers + productive assets?

If this is a policy critique without empirical evaluation, it should be EXCLUDED.
Title strongly suggests this is analytical/descriptive, not impact evaluation.
        """)
    
    print("\n" + "="*80)

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("""
Both false positives appear to be cases where:

1. **Program filter is working but may be TOO PERMISSIVE:**
   - Paper 121323669: Identified "PRSP" but this might be a generic microfinance study
   - Paper 121337599: Identified a program but this is a "critique", not evaluation

2. **Key issues:**
   - Need to distinguish PROGRAM EVALUATION from PROGRAM DESCRIPTION
   - Need to distinguish MICROFINANCE (loans) from GRADUATION (cash+assets)
   - Need to distinguish IMPACT EVALUATION from POLICY CRITIQUE/ANALYSIS

3. **Potential prompt improvements:**
   - Add check: "Is this an IMPACT EVALUATION or just describing/analyzing a policy?"
   - Add check: "Does 'critique' or 'analysis' in title suggest NOT an evaluation?"
   - Strengthen cash component: "Microcredit/loans are NOT cash transfers"
   - Strengthen assets component: "Access to credit is NOT productive asset provision"

**Next steps:**
1. Read full abstracts above to determine which decision is correct
2. Update program filter or criteria to catch these edge cases
3. Consider adding study type classification before detailed criteria
""")

"""
Investigate discrepancies in s14above.xlsx analysis
Focus on:
1. False Negatives: 3 papers (Human: Include, LLM: Exclude)  
2. False Positive INCLUDES: Papers where LLM says INCLUDE but human says Excluded
"""

import sys
from pathlib import Path
import pandas as pd

script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from src.parsers import RISParser

# Load results
results_file = project_dir / "scripts" / "validation" / "s14_comprehensive_results.csv"
results_df = pd.read_csv(results_file)

print("="*80)
print("INVESTIGATING s14above.xlsx DISCREPANCIES")
print("="*80)

# False Negatives
print("\n" + "="*80)
print("1. FALSE NEGATIVES (Human: Included/Maybe, LLM: EXCLUDE)")
print("="*80)

false_negatives = results_df[
    (results_df['human_label'].str.contains('Include', na=False) | 
     results_df['human_label'].str.contains('Maybe', na=False)) & 
    (results_df['llm_decision'] == 'EXCLUDE')
]

print(f"\nTotal: {len(false_negatives)} papers\n")

# Load corpus
parser = RISParser()
ris_files = [
    project_dir / "data" / "input" / "Excluded by DEP classifier (n=54,924).txt",
    project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
]

corpus_lookup = {}
for ris_file in ris_files:
    papers = parser.parse_file(str(ris_file))
    for paper in papers:
        if hasattr(paper, 'ris_fields') and 'U1' in paper.ris_fields:
            u1 = paper.ris_fields['U1']
            paper_id = u1[0] if isinstance(u1, list) else u1
            corpus_lookup[str(paper_id).strip()] = paper

for idx, row in false_negatives.iterrows():
    paper_id = str(row['paper_id'])
    print(f"\nFALSE NEGATIVE {idx+1}: Paper ID {paper_id}")
    print("-"*80)
    print(f"Human Label: {row['human_label']}")
    print(f"LLM Decision: {row['llm_decision']}")
    print(f"Title: {row['title']}")
    
    if paper_id in corpus_lookup:
        paper = corpus_lookup[paper_id]
        print(f"\nAbstract ({len(paper.abstract)} chars):")
        print(paper.abstract)
        print(f"\nYear: {paper.year}")
    else:
        print("\n⚠️ Paper not found in corpus")
    
    print("\n" + "="*80)

# False Positive INCLUDES only
print("\n" + "="*80)
print("2. FALSE POSITIVE INCLUDES (Human: Excluded, LLM: INCLUDE)")
print("="*80)

false_pos_includes = results_df[
    (results_df['human_label'] == 'Excluded') & 
    (results_df['llm_decision'] == 'INCLUDE')
]

print(f"\nTotal: {len(false_pos_includes)} papers")
print("(These are papers where LLM confidently says INCLUDE but human said Excluded)")
print()

for idx, row in false_pos_includes.iterrows():
    paper_id = str(row['paper_id'])
    print(f"\nFALSE POSITIVE INCLUDE {idx+1}: Paper ID {paper_id}")
    print("-"*80)
    print(f"Title: {row['title']}")
    
    if paper_id in corpus_lookup:
        paper = corpus_lookup[paper_id]
        print(f"\nAbstract ({len(paper.abstract)} chars):")
        print(paper.abstract)
        print(f"\nYear: {paper.year}")
    else:
        print("\n⚠️ Paper not found in corpus")
    
    print("\n" + "="*80)

print("\n" + "="*80)
print("ANALYSIS QUESTIONS")
print("="*80)
print("""
False Negatives (3 papers):
- Are these like s3above (mislabeled as Include when they should be Exclude)?
- Do they meet strict inclusion criteria (specific program + cash + assets + evaluation)?

False Positive Includes (8 papers):
- Are these actually relevant programs that humans mislabeled?
- Notable: SCTP (Malawi), BISP (Pakistan) - these ARE known programs
- Do they have both cash AND assets components?
- Are they proper impact evaluations?

Next Steps:
1. Review each false negative abstract - likely mislabeled like s3above
2. Review false positive includes - may be correct inclusions!
3. Document any label corrections needed
4. Update validation file with corrections
""")

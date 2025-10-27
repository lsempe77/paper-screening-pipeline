"""Investigate the 2 false negative papers"""
import sys
from pathlib import Path

script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from src.parsers import RISParser

# The 2 INCLUDE papers that were marked as EXCLUDE
false_negative_ids = ['121323949', '121345309']

# Load corpus
print("Loading corpus to find abstracts...")
parser = RISParser()
ris_files = [
    project_dir / "data" / "input" / "Excluded by DEP classifier (n=54,924).txt",
    project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
]

corpus_papers = {}
for ris_file in ris_files:
    papers = parser.parse_file(str(ris_file))
    for paper in papers:
        if hasattr(paper, 'ris_fields') and 'U1' in paper.ris_fields:
            u1_value = paper.ris_fields['U1']
            paper_id = u1_value[0] if isinstance(u1_value, list) else u1_value
            corpus_papers[str(paper_id).strip()] = paper
    print(f"  Loaded {len(papers)} from {ris_file.name}")

print(f"\nTotal corpus papers indexed: {len(corpus_papers)}")

# Find and display the 2 false negatives
for idx, paper_id in enumerate(false_negative_ids, 1):
    print(f"\n{'='*80}")
    print(f"FALSE NEGATIVE #{idx}: Paper ID {paper_id}")
    print('='*80)
    
    if paper_id in corpus_papers:
        paper = corpus_papers[paper_id]
        print(f"Title: {paper.title}")
        print(f"\nAbstract ({len(paper.abstract)} chars):")
        print(paper.abstract)
        print(f"\nYear: {paper.year}")
        print(f"Authors: {', '.join(paper.authors[:3])}..." if len(paper.authors) > 3 else f"Authors: {', '.join(paper.authors)}")
    else:
        print(f"ERROR: Paper {paper_id} not found in corpus!")

print("\n" + "="*80)
print("ANALYSIS QUESTIONS:")
print("="*80)
print("1. Why did the LLM mark these as EXCLUDE?")
print("2. Are these actually relevant (should they be INCLUDE)?")
print("3. What criteria did they fail?")
print("   - Paper 1: program=NO, participants=UNCLEAR, cash=UNCLEAR, assets=UNCLEAR, outcomes=NO")
print("   - Paper 2: program=NO, participants=YES, cash=YES, assets=NO, outcomes=YES")

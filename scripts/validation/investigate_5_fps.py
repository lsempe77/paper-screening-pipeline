"""
Investigate the 5 hard false positives (LLM=INCLUDE, Human=Excluded)
"""
import sys
from pathlib import Path

script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

import pandas as pd
from src.parsers import RISParser

# The 5 false positives
fp_ids = [
    121296063,  # Malawi SCTP
    121308863,  # Tribal Sub-Plan (TSP)
    121328933,  # "Looking beyond Cash Transfers"
    121328658,  # PES (Payments for Environmental Services)
    121337599,  # Nigeria Economic Policy Reform
]

# Load corpus
parser = RISParser()
ris_files = [
    project_dir / "data" / "input" / "Excluded by DEP classifier (n=54,924).txt",
    project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
]

corpus_lookup = {}
for ris_file in ris_files:
    if ris_file.exists():
        papers = parser.parse_file(str(ris_file))
        for paper in papers:
            if hasattr(paper, 'ris_fields') and 'U1' in paper.ris_fields:
                paper_ids = paper.ris_fields['U1']
                if isinstance(paper_ids, list):
                    paper_id = paper_ids[0] if paper_ids else None
                else:
                    paper_id = paper_ids
                
                if paper_id:
                    corpus_lookup[str(paper_id)] = paper

print("=" * 80)
print("INVESTIGATING 5 HARD FALSE POSITIVES")
print("=" * 80)

for fp_id in fp_ids:
    paper = corpus_lookup.get(str(fp_id))
    if not paper:
        print(f"\n{fp_id}: NOT FOUND IN CORPUS")
        continue
    
    print(f"\n{'=' * 80}")
    print(f"ID: {fp_id}")
    print(f"Title: {paper.title}")
    print(f"\nAbstract:\n{paper.abstract}")
    print(f"\n{'=' * 80}")

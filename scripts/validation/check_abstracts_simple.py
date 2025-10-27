"""
Debug: Check if abstracts actually exist for the false negative papers using RISParser.
"""

import sys
from pathlib import Path

project_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_dir))

from src.parsers import RISParser

false_negative_ids = [121300172, 121340461, 121360003, 121337938]

print("Loading papers using RISParser...\n")
parser = RISParser()
ris_file = project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"

papers = parser.parse_file(str(ris_file))
print(f"Loaded {len(papers)} papers\n")

# Create lookup dict using U1 field from ris_fields
papers_dict = {}
for p in papers:
    if hasattr(p, 'ris_fields') and 'U1' in p.ris_fields:
        u1 = p.ris_fields['U1']
        paper_id = u1[0] if isinstance(u1, list) else u1
        papers_dict[str(paper_id).strip()] = p

for paper_id in false_negative_ids:
    print("=" * 80)
    print(f"Paper ID: {paper_id}")
    print("=" * 80)
    
    paper = papers_dict.get(str(paper_id))
    
    if paper:
        print(f"✓ FOUND\n")
        print(f"Title: {paper.title}\n")
        
        if paper.abstract:
            print(f"Abstract: YES ({len(paper.abstract)} chars)")
            print(f"\nFull abstract:")
            print(paper.abstract)
        else:
            print("Abstract: NO (empty or not in RIS)")
    else:
        print(f"✗ NOT FOUND in parsed papers")
        print(f"\nSample paper IDs from corpus: {list(papers_dict.keys())[:5]}")
    
    print("\n")

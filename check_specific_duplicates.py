#!/usr/bin/env python3
"""Check specific papers to see if they're truly duplicates."""

from src.parsers import RISParser

# Parse RIS file
parser = RISParser()
papers = parser.parse_file('data/input/Not excluded by DEP classifier (n=12,394).txt')

# Check specific U1 IDs
target_u1s = {
    'South Africa group': ['121347521', '121340645'],
    'Minimum Wages group': ['121334204', '121336728']
}

for group_name, u1_ids in target_u1s.items():
    print(f"\n{'='*80}")
    print(f"{group_name}")
    print('='*80)
    
    for u1_id in u1_ids:
        for paper in papers:
            u1_field = paper.ris_fields.get('U1', [])
            paper_u1 = u1_field[0] if isinstance(u1_field, list) and u1_field else str(u1_field)
            
            if paper_u1 == u1_id:
                print(f"\n📄 U1: {u1_id}")
                print(f"   Title: {paper.title}")
                print(f"   Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
                print(f"   Journal: {paper.journal}")
                print(f"   Year: {paper.year}")
                print(f"   Abstract (first 200 chars): {paper.abstract[:200] if paper.abstract else 'N/A'}...")
                break

# Now let's find all papers that our script thinks are duplicates
print("\n" + "="*80)
print("CHECKING ALL DETECTED 'DUPLICATES'")
print("="*80)

from collections import defaultdict

title_to_papers = defaultdict(list)
for paper in papers:
    title_to_papers[paper.title].append(paper)

# Show first 5 "duplicate" groups with full details
duplicate_groups = {title: papers_list for title, papers_list in title_to_papers.items() if len(papers_list) > 1}
print(f"\nFound {len(duplicate_groups)} groups of papers with identical titles")
print("\nFirst 5 examples with full comparison:")

for i, (title, papers_list) in enumerate(list(duplicate_groups.items())[:5], 1):
    print(f"\n{'='*80}")
    print(f"Group {i}: {len(papers_list)} papers with title: {title[:80]}...")
    print('='*80)
    
    for j, paper in enumerate(papers_list, 1):
        u1_field = paper.ris_fields.get('U1', [])
        paper_u1 = u1_field[0] if isinstance(u1_field, list) and u1_field else str(u1_field)
        
        print(f"\n  Paper {j}:")
        print(f"    U1: {paper_u1}")
        print(f"    Full Title: {paper.title}")
        print(f"    Authors: {', '.join(paper.authors) if paper.authors else 'N/A'}")
        print(f"    Journal: {paper.journal}")
        print(f"    Year: {paper.year}")
        print(f"    DOI: {paper.doi}")
        print(f"    Abstract length: {len(paper.abstract) if paper.abstract else 0} chars")
        
        # Check if abstracts are identical
        if j > 1:
            prev_paper = papers_list[j-2]
            if paper.abstract and prev_paper.abstract:
                if paper.abstract == prev_paper.abstract:
                    print(f"    ⚠️ IDENTICAL abstract to Paper {j-1}")
                else:
                    print(f"    ✓ DIFFERENT abstract from Paper {j-1}")

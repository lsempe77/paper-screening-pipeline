#!/usr/bin/env python3
"""
Smart duplicate detection that distinguishes between:
1. Different papers with same title (KEEP BOTH)
2. Same paper in different versions - working paper vs published (FLAG/DEDUPLICATE)
"""

from src.parsers import RISParser
from collections import defaultdict
import difflib

def are_likely_same_paper(paper1, paper2):
    """
    Determine if two papers are likely the same work in different versions.
    
    Returns:
        - 'SAME_WORK': Same paper, different versions (working paper vs published)
        - 'DIFFERENT': Different papers despite same title
    """
    
    # Check 1: Same authors (or very similar author list)
    authors1 = set([a.lower().strip() for a in paper1.authors])
    authors2 = set([a.lower().strip() for a in paper2.authors])
    
    # Calculate author overlap
    if authors1 and authors2:
        author_overlap = len(authors1 & authors2) / max(len(authors1), len(authors2))
    else:
        author_overlap = 0
    
    # Check 2: Abstract similarity (if both have abstracts)
    abstract_similarity = 0
    if paper1.abstract and paper2.abstract and len(paper1.abstract) > 100 and len(paper2.abstract) > 100:
        # Use sequence matcher for similarity
        abstract_similarity = difflib.SequenceMatcher(
            None, 
            paper1.abstract.lower()[:500], 
            paper2.abstract.lower()[:500]
        ).ratio()
    
    # Decision logic
    if author_overlap > 0.7 and abstract_similarity > 0.6:
        return 'SAME_WORK'
    elif author_overlap < 0.3:
        return 'DIFFERENT'
    else:
        return 'UNCERTAIN'

# Parse RIS file
parser = RISParser()
papers = parser.parse_file('data/input/Not excluded by DEP classifier (n=12,394).txt')

# Group by title
title_to_papers = defaultdict(list)
for paper in papers:
    title_to_papers[paper.title].append(paper)

# Analyze duplicate groups
same_work_count = 0
different_papers_count = 0
uncertain_count = 0

print("SMART DUPLICATE ANALYSIS")
print("=" * 80)

for title, papers_list in title_to_papers.items():
    if len(papers_list) > 1:
        # Compare each pair
        for i in range(len(papers_list)):
            for j in range(i + 1, len(papers_list)):
                paper1 = papers_list[i]
                paper2 = papers_list[j]
                
                result = are_likely_same_paper(paper1, paper2)
                
                u1_1 = paper1.ris_fields.get('U1', [''])[0]
                u1_2 = paper2.ris_fields.get('U1', [''])[0]
                
                if result == 'SAME_WORK':
                    same_work_count += 1
                    print(f"\n[!] SAME WORK - Different versions:")
                    print(f"   Title: {title[:80]}...")
                    print(f"   Paper 1 (U1: {u1_1}): {paper1.year} - {paper1.journal[:50] if paper1.journal else 'No journal'}")
                    print(f"   Paper 2 (U1: {u1_2}): {paper2.year} - {paper2.journal[:50] if paper2.journal else 'No journal'}")
                    print(f"   Authors 1: {', '.join(paper1.authors[:3])}")
                    print(f"   Authors 2: {', '.join(paper2.authors[:3])}")
                    
                elif result == 'DIFFERENT':
                    different_papers_count += 1
                    
                else:  # UNCERTAIN
                    uncertain_count += 1
                    print(f"\n[?] UNCERTAIN:")
                    print(f"   Title: {title[:80]}...")
                    print(f"   Paper 1 (U1: {u1_1}): {paper1.year} - {', '.join(paper1.authors[:2])}")
                    print(f"   Paper 2 (U1: {u1_2}): {paper2.year} - {', '.join(paper2.authors[:2])}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total title groups with 'duplicates': {len([p for p in title_to_papers.values() if len(p) > 1])}")
print(f"Same work (different versions): {same_work_count} pairs")
print(f"Different papers (same title): {different_papers_count} pairs")
print(f"Uncertain cases: {uncertain_count} pairs")
print(f"\nRECOMMENDATION:")
print(f"  - Keep different papers: {different_papers_count}")
print(f"  - Consider deduplicating same work: {same_work_count}")
print(f"  - Manual review needed: {uncertain_count}")

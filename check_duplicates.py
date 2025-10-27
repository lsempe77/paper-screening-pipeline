#!/usr/bin/env python3
"""Check for duplicate papers in RIS file."""

from src.parsers import RISParser
from collections import Counter

# Parse RIS file
parser = RISParser()
papers = parser.parse_file('data/input/Not excluded by DEP classifier (n=12,394).txt')

print(f"Total papers parsed: {len(papers)}")

# Check for duplicate titles
titles = [p.title for p in papers]
unique_titles = set(titles)
print(f"Unique titles: {len(unique_titles)}")
print(f"Duplicate papers in source: {len(papers) - len(unique_titles)}")

# Count duplicates
title_counts = Counter(titles)
duplicates = {title: count for title, count in title_counts.items() if count > 1}
print(f"\nNumber of duplicate title groups: {len(duplicates)}")

if duplicates:
    print("\nFirst 10 duplicate examples:")
    for i, (title, count) in enumerate(list(duplicates.items())[:10], 1):
        print(f"\n{i}. Count={count}: {title[:100]}...")
        # Find the U1 IDs for these duplicates
        u1_ids = []
        for paper in papers:
            if paper.title == title:
                u1_field = paper.ris_fields.get('U1', [])
                if u1_field:
                    u1_ids.append(u1_field[0] if isinstance(u1_field, list) else u1_field)
        print(f"   U1 IDs: {u1_ids}")

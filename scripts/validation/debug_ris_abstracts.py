"""
Debug: Check if abstracts actually exist in the RIS file for the false negative papers.
"""

import rispy
from pathlib import Path

project_dir = Path(__file__).parent.parent.parent
ris_file = project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"

false_negative_ids = [121300172, 121340461, 121360003, 121337938]

print(f"Reading RIS file: {ris_file}\n")

with open(ris_file, 'r', encoding='utf-8', errors='ignore') as f:
    entries = list(rispy.load(f))

print(f"Total entries loaded: {len(entries)}\n")

for paper_id in false_negative_ids:
    print("=" * 80)
    print(f"Searching for Paper ID: {paper_id}")
    print("=" * 80)
    
    found = False
    for entry in entries:
        # Try different ID fields
        entry_id = None
        
        # Check U1 field (custom field we used before)
        if 'id' in entry:
            entry_id = str(entry['id'])
        
        # Check other potential ID fields
        if not entry_id and 'custom1' in entry:
            entry_id = str(entry['custom1'])
            
        if not entry_id and 'accession_number' in entry:
            entry_id = str(entry['accession_number'])
        
        if entry_id == str(paper_id):
            found = True
            print(f"✓ FOUND in RIS file!\n")
            
            print(f"Title: {entry.get('title', 'N/A')}\n")
            
            abstract = entry.get('abstract', '')
            if abstract:
                print(f"Abstract: YES ({len(abstract)} chars)")
                print(f"First 300 chars: {abstract[:300]}...\n")
            else:
                print("Abstract: NO\n")
            
            # Show all fields to debug
            print("Available fields in entry:")
            for key in sorted(entry.keys()):
                value = entry[key]
                if isinstance(value, str) and len(value) > 100:
                    print(f"  {key}: {value[:80]}... ({len(value)} chars)")
                else:
                    print(f"  {key}: {value}")
            break
    
    if not found:
        print(f"✗ NOT FOUND in RIS file")
        print(f"   Checking first entry to see ID field format...\n")
        if entries:
            first = entries[0]
            print(f"   Sample entry fields: {list(first.keys())}")
            print(f"   Sample ID field: {first.get('id', 'N/A')}")
    
    print()

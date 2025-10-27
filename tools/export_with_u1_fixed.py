#!/usr/bin/env python3
"""
FIXED: Script to add U1 fields from original RIS file to dual-engine results.
Uses composite key (title + year + authors) instead of just title.
"""

import json
import sys
import pandas as pd
from datetime import datetime
from collections import defaultdict
import re

def normalize_title(title):
    """Normalize title for comparison."""
    return title.lower().strip()

def parse_ris_for_u1_mapping(ris_file_path):
    """Parse RIS file to create mapping of paper identifiers to U1 values."""
    print(f"📖 Parsing RIS file: {ris_file_path}")
    
    # Store all records with their full info
    records = []
    current_record = {}
    
    with open(ris_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            # Parse RIS field
            if '  - ' in line:
                field, value = line.split('  - ', 1)
                if field in ['T1', 'PY', 'U1', 'JF', 'AU', 'A1']:
                    if field == 'AU' or field == 'A1':
                        # Authors can be multiple
                        if 'authors' not in current_record:
                            current_record['authors'] = []
                        current_record['authors'].append(value)
                    else:
                        current_record[field] = value
            elif line == 'ER  -':
                # End of record - save it
                if 'U1' in current_record and 'T1' in current_record:
                    records.append(current_record.copy())
                # Reset for next record
                current_record = {}
    
    print(f"📊 Found {len(records)} records with U1 IDs")
    
    # Create mapping with composite key
    u1_mapping = {}
    title_only_mapping = defaultdict(list)  # For fallback matching
    
    for record in records:
        u1_id = record['U1']
        title = normalize_title(record['T1'])
        year = record.get('PY', '')
        authors = record.get('authors', [])
        
        # Store by title for fallback
        title_only_mapping[title].append({
            'u1': u1_id,
            'year': year,
            'authors': authors,
            'journal': record.get('JF', '')
        })
        
        # Create composite key: title + year + first author
        first_author = authors[0] if authors else ''
        composite_key = f"{title}||{year}||{first_author.lower()}"
        u1_mapping[composite_key] = u1_id
    
    return u1_mapping, title_only_mapping, records

def find_best_u1_match(paper_title, paper_year, paper_authors, u1_mapping, title_only_mapping):
    """Find the best U1 match for a paper using multiple strategies."""
    
    title = normalize_title(paper_title)
    year = str(paper_year) if paper_year else ''
    
    # Strategy 1: Try composite key with first author
    first_author = paper_authors[0] if paper_authors else ''
    composite_key = f"{title}||{year}||{first_author.lower()}"
    
    if composite_key in u1_mapping:
        return u1_mapping[composite_key], 'EXACT_MATCH'
    
    # Strategy 2: Try title + year only
    year_key = f"{title}||{year}||"
    matches = [k for k in u1_mapping.keys() if k.startswith(year_key)]
    if len(matches) == 1:
        return u1_mapping[matches[0]], 'TITLE_YEAR_MATCH'
    
    # Strategy 3: Use title only (but warn if multiple options)
    if title in title_only_mapping:
        candidates = title_only_mapping[title]
        
        if len(candidates) == 1:
            return candidates[0]['u1'], 'TITLE_ONLY_MATCH'
        
        # Multiple candidates - try to match by year
        year_matches = [c for c in candidates if c['year'] == year]
        if len(year_matches) == 1:
            return year_matches[0]['u1'], 'TITLE_YEAR_MATCH'
        elif len(year_matches) > 1:
            # Multiple matches even with year - try author
            if paper_authors:
                for candidate in year_matches:
                    # Check if any author matches
                    for paper_author in paper_authors:
                        for candidate_author in candidate['authors']:
                            if paper_author.lower() in candidate_author.lower() or candidate_author.lower() in paper_author.lower():
                                return candidate['u1'], 'TITLE_YEAR_AUTHOR_MATCH'
            # Still ambiguous - return first match but warn
            return year_matches[0]['u1'], 'AMBIGUOUS_MATCH'
        else:
            # No year match - return first candidate but warn
            return candidates[0]['u1'], 'AMBIGUOUS_MATCH'
    
    return '', 'NO_MATCH'

def export_with_u1_mapping(results_file, ris_file, output_file=None):
    """Export dual-engine results with U1 item_id from mapping."""
    
    # Parse RIS file
    u1_mapping, title_only_mapping, ris_records = parse_ris_for_u1_mapping(ris_file)
    
    # Load results
    print(f"📄 Loading results from: {results_file}")
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data.get('results', [])
    print(f"📊 Processing {len(results)} papers")
    
    # Generate output filename if not provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/output/dual_engine_results_with_u1_FIXED_{timestamp}.csv"
    
    # Track matching statistics
    match_stats = defaultdict(int)
    
    # Prepare data for CSV
    csv_data = []
    
    for i, result in enumerate(results, 1):
        title = result.get('title', '').strip()
        year = result.get('year', '')
        authors = result.get('authors', [])
        
        # Find best U1 match
        u1_id, match_type = find_best_u1_match(title, year, authors, u1_mapping, title_only_mapping)
        match_stats[match_type] += 1
        
        def clean_text(text):
            """Clean text to prevent CSV parsing issues."""
            if not text:
                return ""
            text = str(text).replace('"', "'").replace('\n', ' ').replace('\r', ' ')
            text = ' '.join(text.split())
            return text
        
        # Basic paper information
        row = {
            # Paper identifiers and metadata
            'item_id': u1_id,
            'match_quality': match_type,  # NEW: Track match quality
            'paper_id': result.get('paper_id', ''),
            'title': clean_text(result.get('title', '')),
            'authors': '; '.join(result.get('authors', [])) if result.get('authors') else '',
            'journal': clean_text(result.get('journal', '')),
            'year': result.get('year', ''),
            'doi': result.get('doi', ''),
            'abstract': clean_text(result.get('abstract', '')),
            
            # Engine 1 results
            'engine1_decision': result.get('engine1', {}).get('decision', ''),
            'engine1_success': result.get('engine1', {}).get('success', False),
            'engine1_processing_time': result.get('engine1', {}).get('processing_time', 0),
            'engine1_reasoning': clean_text(result.get('engine1', {}).get('reasoning', '')),
            'engine1_error': clean_text(result.get('engine1', {}).get('error', '')),
            
            # Engine 2 results  
            'engine2_decision': result.get('engine2', {}).get('decision', ''),
            'engine2_success': result.get('engine2', {}).get('success', False),
            'engine2_processing_time': result.get('engine2', {}).get('processing_time', 0),
            'engine2_reasoning': clean_text(result.get('engine2', {}).get('reasoning', '')),
            'engine2_error': clean_text(result.get('engine2', {}).get('error', '')),
            
            # Comparison and agreement
            'both_engines_successful': result.get('comparison', {}).get('both_success', False),
            'agreement': result.get('comparison', {}).get('agreement', False),
            'needs_human_review': result.get('comparison', {}).get('needs_review', False),
        }
        
        # Add consensus decision
        if row['both_engines_successful']:
            if row['agreement']:
                row['consensus_decision'] = row['engine1_decision']
            else:
                row['consensus_decision'] = 'DISAGREEMENT'
        else:
            row['consensus_decision'] = 'ERROR'
        
        # Add metadata
        row['worker_id'] = result.get('worker_id', '')
        row['processed_at'] = result.get('processed_at', '')
        row['processing_order'] = i
        
        # Add detailed criteria if available
        engine1_criteria = result.get('engine1', {}).get('criteria', {})
        engine2_criteria = result.get('engine2', {}).get('criteria', {})
        
        # Engine 1 criteria
        for criterion_name, criterion_data in engine1_criteria.items():
            if isinstance(criterion_data, dict):
                row[f'engine1_{criterion_name}_assessment'] = criterion_data.get('assessment', '')
                row[f'engine1_{criterion_name}_reasoning'] = clean_text(criterion_data.get('reasoning', ''))
        
        # Engine 2 criteria  
        for criterion_name, criterion_data in engine2_criteria.items():
            if isinstance(criterion_data, dict):
                row[f'engine2_{criterion_name}_assessment'] = criterion_data.get('assessment', '')
                row[f'engine2_{criterion_name}_reasoning'] = clean_text(criterion_data.get('reasoning', ''))
        
        # Add review priority
        if row['needs_human_review']:
            if row['engine1_decision'] == 'include' or row['engine2_decision'] == 'include':
                row['review_priority'] = 'HIGH - DISAGREEMENT'
            else:
                row['review_priority'] = 'MEDIUM - DISAGREEMENT'  
        else:
            row['review_priority'] = 'LOW - CONSENSUS'
        
        # Add speed comparison
        engine1_time = row['engine1_processing_time']
        engine2_time = row['engine2_processing_time']
        if engine1_time > 0 and engine2_time > 0:
            if engine1_time < engine2_time:
                row['faster_engine'] = 'Engine 1'
                row['speed_difference_seconds'] = round(engine2_time - engine1_time, 2)
            else:
                row['faster_engine'] = 'Engine 2'  
                row['speed_difference_seconds'] = round(engine1_time - engine2_time, 2)
        else:
            row['faster_engine'] = ''
            row['speed_difference_seconds'] = 0
        
        csv_data.append(row)
    
    # Create DataFrame and export
    df = pd.DataFrame(csv_data)
    
    # Clean text fields to prevent CSV corruption
    print(f"🧹 Cleaning text fields...")
    for col in df.columns:
        if df[col].dtype == 'object':  # String columns
            # Remove null bytes and normalize newlines
            df[col] = df[col].astype(str).str.replace('\x00', '', regex=False)
            df[col] = df[col].str.replace('\r\n', ' ', regex=False)
            df[col] = df[col].str.replace('\r', ' ', regex=False)
            df[col] = df[col].str.replace('\n', ' ', regex=False)
            df[col] = df[col].str.replace('\t', ' ', regex=False)
            # Normalize whitespace
            df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
    
    # Check for duplicate U1 IDs
    duplicate_u1s = df[df['item_id'] != ''].groupby('item_id').size()
    duplicates = duplicate_u1s[duplicate_u1s > 1]
    
    # Save CSV with proper escaping for Excel compatibility
    df.to_csv(
        output_file, 
        index=False, 
        quoting=2,  # QUOTE_NONNUMERIC - quote all non-numeric fields
        encoding='utf-8-sig',  # Add BOM for Excel compatibility
        lineterminator='\n'
    )
    
    print(f"\n💾 CSV Export Complete!")
    print(f"   📄 Output file: {output_file}")
    print(f"   📊 Rows: {len(df):,}")
    print(f"   📋 Columns: {len(df.columns)}")
    
    print(f"\n🔍 U1 MAPPING STATISTICS:")
    for match_type, count in sorted(match_stats.items()):
        pct = (count / len(results)) * 100
        print(f"   {match_type}: {count:,} ({pct:.1f}%)")
    
    if len(duplicates) > 0:
        print(f"\n⚠️ WARNING: {len(duplicates)} duplicate U1 IDs found!")
        print(f"   These papers may need manual review.")
        print(f"   First 5 duplicates:")
        for u1_id, count in list(duplicates.items())[:5]:
            print(f"      U1 {u1_id}: appears {count} times")
            dup_papers = df[df['item_id'] == u1_id][['title', 'year', 'match_quality']].head(count)
            for idx, row in dup_papers.iterrows():
                print(f"         - {row['year']} | {row['match_quality']}: {row['title'][:60]}...")
    else:
        print(f"\n✅ No duplicate U1 IDs - Perfect mapping!")
    
    return output_file

def main():
    if len(sys.argv) != 3:
        print("Usage: python export_with_u1_fixed.py <results_json> <ris_file>")
        print("Example: python export_with_u1_fixed.py data/output/batch_dual_screening_20251025_014003.json \"data/input/Not excluded by DEP classifier (n=12,394).txt\"")
        sys.exit(1)
    
    results_file = sys.argv[1]
    ris_file = sys.argv[2]
    
    print("🔍 DUAL-ENGINE RESULTS CSV EXPORT WITH FIXED U1 MAPPING")
    print("=" * 60)
    
    # Export with improved U1 mapping
    output_file = export_with_u1_mapping(results_file, ris_file)
    
    print(f"\n✅ Export completed successfully!")
    print(f"   📄 Full CSV: {output_file}")

if __name__ == "__main__":
    main()

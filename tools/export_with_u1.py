#!/usr/bin/env python3
"""
Script to add U1 fields from original RIS file to existing dual-engine results
and export to CSV with proper item_id.
"""

import json
import sys
import pandas as pd
from datetime import datetime
from collections import Counter
import re

def parse_ris_for_u1_mapping(ris_file_path):
    """Parse RIS file to create mapping of paper identifiers to U1 values."""
    print(f"📖 Parsing RIS file: {ris_file_path}")
    
    u1_mapping = {}
    current_record = {}
    
    with open(ris_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            # Parse RIS field
            if line.startswith(('TY  ', 'T1  ', 'JF  ', 'PY  ', 'U1  ', 'ER  ')):
                if '  - ' in line:
                    field, value = line.split('  - ', 1)
                    current_record[field] = value
                elif line == 'ER  -':
                    # End of record - process it
                    if 'U1' in current_record and 'T1' in current_record:
                        u1_id = current_record['U1']
                        title = current_record['T1']
                        
                        # Create mapping by title (primary key)
                        u1_mapping[title] = u1_id
                        
                        # Also try to map by year_id format if we can extract it
                        if 'PY' in current_record:
                            year = current_record['PY']
                            # Try to create year_id format like "2023_3117"
                            # We'll need to match this during export
                        
                    # Reset for next record
                    current_record = {}
    
    print(f"📊 Found {len(u1_mapping)} U1 mappings")
    return u1_mapping

def export_with_u1_mapping(results_file, u1_mapping, output_file=None):
    """Export dual-engine results with U1 item_id from mapping."""
    
    # Load results
    print(f"📄 Loading results from: {results_file}")
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data.get('results', [])
    print(f"📊 Processing {len(results)} papers")
    
    # Generate output filename if not provided
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/output/dual_engine_results_with_u1_{timestamp}.csv"
    
    # Prepare data for CSV
    csv_data = []
    u1_found = 0
    u1_missing = 0
    
    for i, result in enumerate(results, 1):
        # Try to find U1 by title
        title = result.get('title', '').strip()
        u1_id = u1_mapping.get(title, '')
        
        if u1_id:
            u1_found += 1
        else:
            u1_missing += 1
            # Try partial title match as fallback
            for mapped_title, mapped_u1 in u1_mapping.items():
                if len(title) > 20 and len(mapped_title) > 20:
                    # Compare first 50 characters for partial match
                    if title[:50].lower() == mapped_title[:50].lower():
                        u1_id = mapped_u1
                        u1_found += 1
                        u1_missing -= 1
                        break
        
        def clean_text(text):
            """Clean text to prevent CSV parsing issues."""
            if not text:
                return ""
            # Remove internal quotes, newlines, and excessive whitespace
            text = str(text).replace('"', "'").replace('\n', ' ').replace('\r', ' ')
            # Normalize whitespace
            text = ' '.join(text.split())
            return text
        
        # Basic paper information
        row = {
            # Paper identifiers and metadata
            'item_id': u1_id,  # Use U1 from RIS mapping
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
    
    # Save CSV with proper quoting to handle long text fields
    df.to_csv(output_file, index=False, quoting=1, escapechar='\\', doublequote=True)
    
    print(f"\n💾 CSV Export Complete!")
    print(f"   📄 Output file: {output_file}")
    print(f"   📊 Rows: {len(df):,}")
    print(f"   📋 Columns: {len(df.columns)}")
    print(f"\n🔍 U1 MAPPING RESULTS:")
    print(f"   ✅ U1 found: {u1_found:,} ({u1_found/len(results)*100:.1f}%)")
    print(f"   ❌ U1 missing: {u1_missing:,} ({u1_missing/len(results)*100:.1f}%)")
    
    return output_file

def main():
    if len(sys.argv) != 3:
        print("Usage: python export_with_u1.py <results_json> <ris_file>")
        print("Example: python export_with_u1.py data/output/batch_dual_screening_20251025_014003.json \"data/input/Not excluded by DEP classifier (n=12,394).txt\"")
        sys.exit(1)
    
    results_file = sys.argv[1]
    ris_file = sys.argv[2]
    
    print("🔍 DUAL-ENGINE RESULTS CSV EXPORT WITH U1 MAPPING")
    print("=" * 55)
    
    # Parse RIS for U1 mapping
    u1_mapping = parse_ris_for_u1_mapping(ris_file)
    
    # Export with U1 mapping
    output_file = export_with_u1_mapping(results_file, u1_mapping)
    
    print(f"\n✅ Export completed successfully!")
    print(f"   📄 Full CSV: {output_file}")

if __name__ == "__main__":
    main()
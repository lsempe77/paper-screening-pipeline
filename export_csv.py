#!/usr/bin/env python3
"""
Dual-Engine Results CSV Export Tool

Exports comprehensive dual-engine screening results to CSV format
with all key fields for analysis, review, and stakeholder reporting.
"""

import json
import pandas as pd
import sys
import os
from datetime import datetime

def export_to_csv(results_file, output_file=None):
    """Export dual-engine results to comprehensive CSV."""
    
    print("📊 DUAL-ENGINE RESULTS CSV EXPORT")
    print("=" * 35)
    
    # Load results
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading results: {e}")
        return None
    
    results = data['results']
    metadata = data['metadata']
    
    print(f"📄 Loading {len(results)} papers from: {os.path.basename(results_file)}")
    print(f"🤖 Engine 1: {metadata['engine1_model']}")
    print(f"🤖 Engine 2: {metadata['engine2_model']}")
    
    # Prepare data for CSV
    csv_data = []
    
    for i, result in enumerate(results, 1):
        # Basic paper information
        row = {
            # Paper identifiers and metadata
            'item_id': result.get('u1', ''),  # Use actual U1 field from RIS
            'paper_id': result.get('paper_id', ''),
            'title': result.get('title', ''),
            'authors': '; '.join(result.get('authors', [])) if result.get('authors') else '',
            'journal': result.get('journal', ''),
            'year': result.get('year', ''),
            'doi': result.get('doi', ''),
            'abstract': result.get('abstract', ''),
            
            # Engine 1 results
            'engine1_decision': result.get('engine1', {}).get('decision', ''),
            'engine1_success': result.get('engine1', {}).get('success', False),
            'engine1_processing_time': result.get('engine1', {}).get('processing_time', 0),
            'engine1_reasoning': result.get('engine1', {}).get('reasoning', ''),
            'engine1_error': result.get('engine1', {}).get('error', ''),
            
            # Engine 2 results  
            'engine2_decision': result.get('engine2', {}).get('decision', ''),
            'engine2_success': result.get('engine2', {}).get('success', False),
            'engine2_processing_time': result.get('engine2', {}).get('processing_time', 0),
            'engine2_reasoning': result.get('engine2', {}).get('reasoning', ''),
            'engine2_error': result.get('engine2', {}).get('error', ''),
            
            # Comparison and agreement
            'both_engines_successful': result.get('comparison', {}).get('both_success', False),
            'agreement': result.get('comparison', {}).get('agreement', False),
            'needs_human_review': result.get('comparison', {}).get('needs_review', False),
            
            # Consensus decision (where they agree)
            'consensus_decision': result.get('engine1', {}).get('decision', '') if result.get('comparison', {}).get('agreement', False) else 'DISAGREEMENT',
            
            # Processing metadata
            'worker_id': result.get('worker_id', ''),
            'processed_at': result.get('processed_at', ''),
            'processing_order': i
        }
        
        # Add criteria details from Engine 1 (if available)
        engine1_criteria = result.get('engine1', {}).get('criteria', {})
        if engine1_criteria:
            for criterion, details in engine1_criteria.items():
                row[f'engine1_{criterion}_assessment'] = details.get('assessment', '')
                row[f'engine1_{criterion}_reasoning'] = details.get('reasoning', '')
        
        # Add criteria details from Engine 2 (if available)
        engine2_criteria = result.get('engine2', {}).get('criteria', {})
        if engine2_criteria:
            for criterion, details in engine2_criteria.items():
                row[f'engine2_{criterion}_assessment'] = details.get('assessment', '')
                row[f'engine2_{criterion}_reasoning'] = details.get('reasoning', '')
        
        # Agreement status for easy filtering
        if result.get('comparison', {}).get('both_success', False):
            if result.get('comparison', {}).get('agreement', False):
                row['review_priority'] = 'LOW - CONSENSUS'
            else:
                row['review_priority'] = 'HIGH - DISAGREEMENT'
        else:
            row['review_priority'] = 'MEDIUM - ENGINE ERROR'
        
        # Speed comparison
        time1 = result.get('engine1', {}).get('processing_time', 0)
        time2 = result.get('engine2', {}).get('processing_time', 0)
        if time1 > 0 and time2 > 0:
            row['faster_engine'] = 'Engine 1' if time1 < time2 else 'Engine 2'
            row['speed_difference_seconds'] = abs(time1 - time2)
        else:
            row['faster_engine'] = ''
            row['speed_difference_seconds'] = 0
        
        csv_data.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(csv_data)
    
    # Prepare output filename
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/output/dual_engine_results_{timestamp}.csv"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Export to CSV
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n💾 CSV Export Complete!")
    print(f"   📄 Output file: {output_file}")
    print(f"   📊 Rows: {len(df):,}")
    print(f"   📋 Columns: {len(df.columns)}")
    
    # Summary statistics
    print(f"\n📈 SUMMARY STATISTICS:")
    
    # Agreement summary
    both_success = df['both_engines_successful'].sum()
    agreements = df['agreement'].sum() 
    disagreements = both_success - agreements
    
    print(f"   ✅ Both engines successful: {both_success:,} ({both_success/len(df)*100:.1f}%)")
    print(f"   🤝 Agreements: {agreements:,} ({agreements/both_success*100:.1f}% of successful)")
    print(f"   ⚠️  Disagreements: {disagreements:,} ({disagreements/both_success*100:.1f}% of successful)")
    
    # Decision breakdown
    print(f"\n🎯 DECISION BREAKDOWN:")
    engine1_decisions = df['engine1_decision'].value_counts()
    engine2_decisions = df['engine2_decision'].value_counts()
    
    print(f"   Engine 1 ({metadata['engine1_model']}):")
    for decision, count in engine1_decisions.items():
        if decision != '':
            print(f"      {decision}: {count:,} ({count/len(df)*100:.1f}%)")
    
    print(f"   Engine 2 ({metadata['engine2_model']}):")
    for decision, count in engine2_decisions.items():
        if decision != '':
            print(f"      {decision}: {count:,} ({count/len(df)*100:.1f}%)")
    
    # Human review workload
    needs_review = df['needs_human_review'].sum()
    print(f"\n🔍 HUMAN REVIEW:")
    print(f"   Papers requiring review: {needs_review:,}")
    print(f"   Estimated review time: {needs_review * 0.5:.1f} hours")
    
    # Performance comparison
    faster_engine_counts = df['faster_engine'].value_counts()
    if len(faster_engine_counts) > 0:
        print(f"\n⚡ SPEED COMPARISON:")
        for engine, count in faster_engine_counts.items():
            if engine != '':
                print(f"   {engine} faster: {count:,} papers ({count/len(df)*100:.1f}%)")
        
        avg_speed_diff = df[df['speed_difference_seconds'] > 0]['speed_difference_seconds'].mean()
        print(f"   Average speed difference: {avg_speed_diff:.1f} seconds")
    
    print(f"\n📋 CSV COLUMNS INCLUDED:")
    print("   📄 Paper Info: paper_id, title, authors, journal, year, doi, abstract")
    print("   🤖 Engine Results: decisions, success status, processing times, reasoning")
    print("   🤝 Agreement: consensus status, review requirements, priority levels")
    print("   📊 Criteria: detailed assessments and reasoning (if available)")
    print("   ⚡ Performance: speed comparisons and processing metadata")
    
    return output_file

def create_summary_csv(results_file, output_file=None):
    """Create a simplified summary CSV for quick review."""
    
    # Load results
    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data['results']
    metadata = data['metadata']
    
    # Create simplified summary
    summary_data = []
    
    for i, result in enumerate(results, 1):
        row = {
            'paper_id': result.get('paper_id', ''),
            'title': result.get('title', '')[:100] + '...' if len(result.get('title', '')) > 100 else result.get('title', ''),
            'year': result.get('year', ''),
            'engine1_decision': result.get('engine1', {}).get('decision', ''),
            'engine2_decision': result.get('engine2', {}).get('decision', ''),
            'agreement': 'YES' if result.get('comparison', {}).get('agreement', False) else 'NO',
            'needs_human_review': 'YES' if result.get('comparison', {}).get('needs_review', False) else 'NO',
            'consensus_decision': result.get('engine1', {}).get('decision', '') if result.get('comparison', {}).get('agreement', False) else 'REVIEW_NEEDED',
            'engine1_time_sec': result.get('engine1', {}).get('processing_time', 0),
            'engine2_time_sec': result.get('engine2', {}).get('processing_time', 0)
        }
        summary_data.append(row)
    
    # Create summary DataFrame
    summary_df = pd.DataFrame(summary_data)
    
    # Prepare output filename
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/output/dual_engine_summary_{timestamp}.csv"
    
    # Export summary CSV
    summary_df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"   📋 Summary CSV: {output_file}")
    return output_file

def main():
    """Main entry point."""
    
    if len(sys.argv) < 2:
        print("Usage: python export_csv.py <results_file.json> [output_file.csv]")
        print("\nExample:")
        print('  python export_csv.py "data/output/batch_dual_screening_20251025_014003.json"')
        sys.exit(1)
    
    results_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(results_file):
        print(f"❌ ERROR: Results file not found: {results_file}")
        sys.exit(1)
    
    try:
        # Export comprehensive CSV
        full_csv = export_to_csv(results_file, output_file)
        
        # Create summary CSV
        summary_csv = None
        if full_csv:
            summary_csv = create_summary_csv(results_file, full_csv.replace('.csv', '_summary.csv'))
        
        print(f"\n✅ Export completed successfully!")
        print(f"   📄 Full CSV: {full_csv}")
        if summary_csv:
            print(f"   📋 Summary CSV: {summary_csv}")
        
    except Exception as e:
        print(f"❌ ERROR during export: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Comprehensive duplicate analysis for the compact CSV.
Adds columns indicating duplicate status and type.
"""

import pandas as pd
import difflib
from collections import defaultdict
from datetime import datetime

def analyze_and_mark_duplicates(csv_file):
    """Analyze duplicates and add identification columns."""
    
    print(f"📄 Loading CSV: {csv_file}")
    df = pd.read_csv(csv_file, low_memory=False)
    
    print(f"   Total rows: {len(df):,}")
    
    # Check for duplicate U1 IDs
    print(f"\n🔍 Checking for duplicate U1 IDs...")
    duplicate_u1s = df[df['item_id'] != ''].groupby('item_id').size()
    duplicates_count = (duplicate_u1s > 1).sum()
    
    if duplicates_count > 0:
        print(f"   ❌ Found {duplicates_count} duplicate U1 IDs")
        for u1_id, count in duplicate_u1s[duplicate_u1s > 1].items():
            print(f"      U1 {u1_id}: appears {count} times")
    else:
        print(f"   ✅ No duplicate U1 IDs found!")
    
    # Analyze title duplicates
    print(f"\n🔍 Analyzing title duplicates...")
    
    # Initialize new columns
    df['duplicate_status'] = 'UNIQUE'
    df['duplicate_type'] = ''
    df['duplicate_group_id'] = ''
    df['duplicate_notes'] = ''
    
    # Group by title
    title_groups = df.groupby('title')
    
    duplicate_title_groups = 0
    same_work_count = 0
    title_collision_count = 0
    
    for title, group in title_groups:
        if len(group) > 1:
            duplicate_title_groups += 1
            group_id = f"DUP_{duplicate_title_groups}"
            
            # Analyze this group
            rows = group.to_dict('records')
            indices = group.index.tolist()
            
            # Check if same work (same authors and year)
            first_row = rows[0]
            first_authors = str(first_row.get('authors', '')).lower()
            first_year = first_row.get('year', '')
            
            is_same_work = True
            for row in rows[1:]:
                row_authors = str(row.get('authors', '')).lower()
                row_year = row.get('year', '')
                
                # Check author similarity
                author_similarity = difflib.SequenceMatcher(None, first_authors, row_authors).ratio()
                year_match = (first_year == row_year)
                
                if author_similarity < 0.7 or not year_match:
                    is_same_work = False
                    break
            
            # Mark all rows in this group
            for idx in indices:
                df.at[idx, 'duplicate_group_id'] = group_id
                df.at[idx, 'duplicate_status'] = 'DUPLICATE'
                
                if is_same_work:
                    df.at[idx, 'duplicate_type'] = 'SAME_WORK_DIFFERENT_VERSION'
                    df.at[idx, 'duplicate_notes'] = f'Same study, different publication (e.g., working paper vs journal). Group: {group_id}'
                    same_work_count += 1
                else:
                    df.at[idx, 'duplicate_type'] = 'TITLE_COLLISION'
                    df.at[idx, 'duplicate_notes'] = f'Different papers with same title. Group: {group_id}'
                    title_collision_count += 1
    
    # Summary
    print(f"\n📊 DUPLICATE ANALYSIS RESULTS:")
    print(f"   Total papers: {len(df):,}")
    print(f"   Unique papers: {(df['duplicate_status'] == 'UNIQUE').sum():,}")
    print(f"   Papers with duplicates: {(df['duplicate_status'] == 'DUPLICATE').sum():,}")
    print(f"\n   Duplicate breakdown:")
    print(f"   - Same work (different versions): {same_work_count}")
    print(f"   - Title collisions (different papers): {title_collision_count}")
    print(f"   - Total duplicate groups: {duplicate_title_groups}")
    
    # Show examples
    if duplicate_title_groups > 0:
        print(f"\n📋 Example duplicate groups:")
        
        example_groups = df[df['duplicate_status'] == 'DUPLICATE'].groupby('duplicate_group_id').head(2)
        
        for group_id in df[df['duplicate_status'] == 'DUPLICATE']['duplicate_group_id'].unique()[:3]:
            print(f"\n   {group_id}:")
            group_rows = df[df['duplicate_group_id'] == group_id]
            for idx, row in group_rows.iterrows():
                print(f"      U1: {row['item_id']} | {row['year']} | {row['duplicate_type']}")
                print(f"      Title: {row['title'][:80]}...")
                print(f"      Authors: {str(row.get('authors', ''))[:80]}...")
    
    # Save with new columns
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Create shorter filename
    import os
    output_file = os.path.join(os.path.dirname(csv_file), f'screening_results_FINAL_{timestamp}.csv')
    
    df.to_csv(output_file, index=False, quoting=2, encoding='utf-8-sig', lineterminator='\n')
    
    print(f"\n💾 Saved with duplicate analysis: {output_file}")
    
    # Create summary report
    print(f"\n📄 Creating detailed duplicate report...")
    
    if duplicate_title_groups > 0:
        report_file = os.path.join(os.path.dirname(csv_file), f'duplicate_report_{timestamp}.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("DUPLICATE ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total papers: {len(df):,}\n")
            f.write(f"Unique papers: {(df['duplicate_status'] == 'UNIQUE').sum():,}\n")
            f.write(f"Papers with duplicates: {(df['duplicate_status'] == 'DUPLICATE').sum():,}\n\n")
            f.write(f"Same work (different versions): {same_work_count}\n")
            f.write(f"Title collisions (different papers): {title_collision_count}\n")
            f.write(f"Total duplicate groups: {duplicate_title_groups}\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("DETAILED DUPLICATE GROUPS\n")
            f.write("=" * 80 + "\n\n")
            
            for group_id in sorted(df[df['duplicate_status'] == 'DUPLICATE']['duplicate_group_id'].unique()):
                group_rows = df[df['duplicate_group_id'] == group_id]
                
                f.write(f"\n{group_id}: {group_rows.iloc[0]['duplicate_type']}\n")
                f.write("-" * 80 + "\n")
                f.write(f"Title: {group_rows.iloc[0]['title']}\n\n")
                
                for idx, row in group_rows.iterrows():
                    f.write(f"  Paper #{idx + 1}:\n")
                    f.write(f"    U1 ID: {row['item_id']}\n")
                    f.write(f"    Year: {row['year']}\n")
                    f.write(f"    Authors: {row.get('authors', 'N/A')}\n")
                    f.write(f"    Journal: {row.get('journal', 'N/A')}\n")
                    f.write(f"    DOI: {row.get('doi', 'N/A')}\n")
                    f.write(f"    Engine 1: {row.get('engine1_decision', 'N/A')}\n")
                    f.write(f"    Engine 2: {row.get('engine2_decision', 'N/A')}\n")
                    f.write(f"    Consensus: {row.get('consensus_decision', 'N/A')}\n")
                    f.write("\n")
        
        print(f"📄 Detailed report saved: {report_file}")
    
    return df, output_file

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python verify_and_mark_duplicates.py <csv_file>")
        print("Example: python verify_and_mark_duplicates.py data/output/results_COMPACT.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    analyze_and_mark_duplicates(csv_file)

"""
Correct validation labels in s20above.xlsx based on false negative analysis

CORRECTIONS TO MAKE:
✅ Case 1 (ID: 121378353): TMRI - cash/food only, no productive assets → EXCLUDE
❓ Case 2 (ID: 121326700): "complementary programming" - keep for full text review  
✅ Case 3 (ID: 121295397): China PRP - medical assistance only, no productive assets → EXCLUDE

This corrects 2 out of 3 false negatives, leaving 1 for full-text analysis.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def correct_s20_labels():
    """Correct validation labels in s20above.xlsx"""
    
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent.parent
    s20_path = project_dir / "data" / "input" / "s20above.xlsx"
    
    print("="*80)
    print("CORRECTING s20above.xlsx VALIDATION LABELS")
    print("="*80)
    
    # Load current data
    df = pd.read_excel(s20_path)
    print(f"Loaded {len(df)} papers from s20above.xlsx")
    
    # Show current label distribution
    print(f"\nCurrent label distribution:")
    print(df['include'].value_counts())
    
    # Create backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = project_dir / "backups" / f"s20above_backup_{timestamp}.xlsx"
    backup_path.parent.mkdir(exist_ok=True)
    df.to_excel(backup_path, index=False)
    print(f"\n✓ Backup created: {backup_path}")
    
    # Papers to correct (excluding Case 2 which needs full-text review)
    corrections = [
        {
            'id': 121378353,
            'title': 'Social assistance and adaptation to flooding in Bangladesh',
            'reason': 'TMRI provides cash/food transfers only - no productive assets component',
            'old_label': 'Included (TA)',
            'new_label': 'Excluded'
        },
        {
            'id': 121295397, 
            'title': 'The effects of poverty reduction policy on health services utilization...',
            'reason': 'China PRP provides medical financial assistance only - no productive assets',
            'old_label': 'Included (TA)',
            'new_label': 'Excluded'
        }
    ]
    
    print(f"\n" + "="*80)
    print("APPLYING CORRECTIONS")
    print("="*80)
    
    corrections_made = 0
    
    for correction in corrections:
        paper_id = correction['id']
        
        # Find the paper
        mask = df['ID'] == paper_id
        if not mask.any():
            print(f"❌ Paper {paper_id} not found")
            continue
        
        # Get current label
        current_label = df.loc[mask, 'include'].values[0]
        
        print(f"\n📄 Paper {paper_id}:")
        print(f"   Title: {correction['title'][:60]}...")
        print(f"   Current: {current_label}")
        print(f"   New: {correction['new_label']}")
        print(f"   Reason: {correction['reason']}")
        
        # Apply correction
        if current_label == correction['old_label']:
            df.loc[mask, 'include'] = correction['new_label']
            corrections_made += 1
            print(f"   ✓ Corrected")
        else:
            print(f"   ⚠️  Expected '{correction['old_label']}' but found '{current_label}'")
    
    # Show updated distribution
    print(f"\n" + "="*80)
    print("UPDATED LABEL DISTRIBUTION")
    print("="*80)
    print(df['include'].value_counts())
    
    # Save corrected file
    corrected_path = project_dir / "data" / "input" / "s20above_CORRECTED.xlsx"
    df.to_excel(corrected_path, index=False)
    
    print(f"\n✓ Corrections applied: {corrections_made}")
    print(f"✓ Corrected file saved: {corrected_path}")
    
    print(f"\n" + "="*80)
    print("CASE 2 LEFT FOR FULL-TEXT REVIEW")
    print("="*80)
    print(f"Paper ID: 121326700")
    print(f"Title: Sustainable Poverty Reduction through Social Assistance...")
    print(f"Reason: 'Complementary programming' may include productive assets")
    print(f"Action: Keep as 'Included (TA)' pending full-text analysis")
    
    print(f"\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Review corrected file: s20above_CORRECTED.xlsx")
    print("2. If satisfied, rename to s20above.xlsx")
    print("3. Re-run comprehensive analysis (expect 1 false negative remaining)")
    print("4. Schedule Case 2 for full-text review to check for productive assets")
    
    return corrections_made

if __name__ == "__main__":
    corrections_made = correct_s20_labels()
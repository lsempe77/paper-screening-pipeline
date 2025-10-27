"""
Correct labels for 3 false negatives in s14above.xlsx.
Creates backup before making changes.

Papers to correct (from "Included (TA)" to "Excluded"):
- 121300172: Nutrition/WASH program, no cash/assets
- 121360003: Generic financial inclusion study, no cash/assets  
- 121337938: Generic microfinance, no cash/assets

Paper 121340461 remains "Maybe (TA)" (missing abstract, correctly MAYBE by LLM)
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil

# Paths
project_dir = Path(__file__).parent.parent.parent
input_file = project_dir / "data" / "input" / "s14above.xlsx"
backup_dir = project_dir / "backups"
backup_dir.mkdir(exist_ok=True)

# Create timestamped backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = backup_dir / f"s14above_backup_{timestamp}.xlsx"
shutil.copy2(input_file, backup_file)
print(f"✓ Backup created: {backup_file}")

# Load data
df = pd.read_excel(input_file)
print(f"\n✓ Loaded s14above.xlsx: {len(df)} papers")

# Papers to correct
corrections = {
    121300172: {
        'old_label': 'Included (TA)',
        'new_label': 'Excluded',
        'reason': 'Nutrition/WASH program (Growth through Nutrition, Ethiopia). No cash transfers or productive assets. SBCC intervention only.'
    },
    121360003: {
        'old_label': 'Included (TA)',
        'new_label': 'Excluded',
        'reason': 'Generic financial inclusion study (Ethiopia). Observational econometric analysis. No specific program, no cash transfers, no productive assets.'
    },
    121337938: {
        'old_label': 'Included (TA)',
        'new_label': 'Excluded',
        'reason': 'Generic microfinance study (Ghana). Microfinance loans only, no cash component. Assets = household durables (not productive assets).'
    }
}

# Apply corrections
print(f"\n{'='*80}")
print("APPLYING CORRECTIONS")
print(f"{'='*80}\n")

for paper_id, correction in corrections.items():
    # Find paper
    mask = df['ID'] == paper_id
    if not mask.any():
        print(f"⚠️  Paper {paper_id} not found in dataset")
        continue
    
    # Get current label
    current_label = df.loc[mask, 'include'].values[0]
    
    if current_label != correction['old_label']:
        print(f"⚠️  Paper {paper_id}: Expected '{correction['old_label']}', found '{current_label}'")
        continue
    
    # Apply correction
    df.loc[mask, 'include'] = correction['new_label']
    
    # Get paper info
    title = df.loc[mask, 'Title'].values[0]
    
    print(f"Paper {paper_id}:")
    print(f"  Title: {title[:80]}...")
    print(f"  Changed: {correction['old_label']} → {correction['new_label']}")
    print(f"  Reason: {correction['reason']}")
    print()

# Create corrected file (with _CORRECTED suffix, to be renamed later)
corrected_file = project_dir / "data" / "input" / "s14above_CORRECTED.xlsx"
df.to_excel(corrected_file, index=False)
print(f"✓ Corrected file saved: {corrected_file}")

# Summary
print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
print(f"✓ Backup created: {backup_file.name}")
print(f"✓ Corrections applied: 3 papers")
print(f"✓ Corrected file: {corrected_file.name}")
print(f"\nLabel distribution after corrections:")
label_counts = df['include'].value_counts()
for label, count in label_counts.items():
    print(f"  {label}: {count}")

print(f"\n{'='*80}")
print("NEXT STEPS")
print(f"{'='*80}")
print("1. Review the corrected file: s14above_CORRECTED.xlsx")
print("2. If satisfied, rename to s14above.xlsx:")
print(f"   Move-Item '{corrected_file}' '{input_file}'")
print("3. Update documentation in docs/s14_LABEL_CORRECTIONS.md")

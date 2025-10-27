"""
Correct validation labels for false negatives
After investigation, papers 121323949 and 121345309 should be Excluded
"""
import pandas as pd
import shutil
from datetime import datetime
from pathlib import Path

# Paths
input_dir = Path("data/input")
original_file = input_dir / "s3above.xlsx"
backup_file = input_dir / f"s3above_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
corrected_file = input_dir / "s3above_corrected.xlsx"

print("="*80)
print("CORRECTING VALIDATION LABELS")
print("="*80)

# Create backup
shutil.copy(original_file, backup_file)
print(f"\n✓ Backup created: {backup_file.name}")

# Load data
df = pd.read_excel(original_file)
print(f"\n✓ Loaded {len(df)} papers from {original_file.name}")

# Show before
print("\nBefore corrections:")
print(df['include'].value_counts())

# Make corrections
paper1_idx = df[df['ID'] == 121323949].index
paper2_idx = df[df['ID'] == 121345309].index

if len(paper1_idx) > 0:
    old_label_1 = df.loc[paper1_idx[0], 'include']
    df.loc[paper1_idx[0], 'include'] = 'Excluded'
    print(f"\n✓ Paper 121323949: '{old_label_1}' → 'Excluded'")
    print(f"  Title: {df.loc[paper1_idx[0], 'Title'][:80]}...")
    
if len(paper2_idx) > 0:
    old_label_2 = df.loc[paper2_idx[0], 'include']
    df.loc[paper2_idx[0], 'include'] = 'Excluded'
    print(f"\n✓ Paper 121345309: '{old_label_2}' → 'Excluded'")
    print(f"  Title: {df.loc[paper2_idx[0], 'Title'][:80]}...")

# Show after
print("\nAfter corrections:")
print(df['include'].value_counts())

# Save corrected file
df.to_excel(corrected_file, index=False)
print(f"\n✓ Corrected file saved as: {corrected_file.name}")

print("\n" + "="*80)
print("NEXT STEPS:")
print("="*80)
print("1. Close the original s3above.xlsx file if open")
print("2. Delete or rename the original file")
print("3. Rename s3above_corrected.xlsx to s3above.xlsx")
print("4. Re-run the validation test")

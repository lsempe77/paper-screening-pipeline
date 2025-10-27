# Tools Directory

This directory contains utility scripts for data analysis, export, and visualization of screening results.

## 📊 Analysis Tools

### `analyze_dual_results.py`
Comprehensive analysis tool for dual-engine screening results.
- Generates agreement statistics
- Identifies disagreement patterns
- Creates performance metrics

### `decision_analysis.py`
Detailed statistical analysis of screening decisions.
- Decision distribution analysis
- Engine comparison metrics
- Quality assurance reports

## 📄 Export Tools

### `export_with_u1_fixed.py` ⭐ **RECOMMENDED**
**Fixed export script with proper U1 mapping and CSV escaping.**
- Uses composite key matching (title + year + authors) to prevent duplicate U1 IDs
- Proper CSV escaping to prevent corruption
- Handles papers with identical titles correctly
- Text cleaning for maximum compatibility
- **Use this for all production exports**

### `export_csv_compact.py` 🎯 **FOR LARGE DATASETS**
**Compact CSV export without large text fields.**
- Removes abstracts and reasoning text to prevent CSV corruption
- Reduces file size by ~90% (5 MB vs 58 MB)
- Keeps all essential screening data (decisions, criteria, metadata)
- Perfect for Excel/PowerShell compatibility
- **Use this if you experience CSV corruption issues**

### `export_csv.py`
Basic CSV export functionality for screening results.
- Standard CSV format export
- All paper metadata included
- Engine results and reasoning

### `export_with_u1.py` ⚠️ **DEPRECATED**
Original export script - has known issues with duplicate U1 IDs.
- **Use `export_with_u1_fixed.py` instead**

### `deduplicate_csv.py`
Remove duplicate U1 IDs from existing CSV files.
- Keeps first occurrence of each U1 ID
- Useful for fixing old exports

### `fix_csv_escaping.py`
Repair tool for corrupted CSV files.
- Re-exports with proper character escaping
- Fixes newline/quote/tab issues
- Adds UTF-8 BOM for Excel compatibility

### `verify_and_mark_duplicates.py` 🔍 **VERIFICATION**
**Comprehensive duplicate analysis and verification tool.**
- Confirms zero duplicate U1 IDs in final CSV
- Identifies and marks title duplicates with detailed classification
- Distinguishes between "same work/different versions" vs "title collisions"
- Creates detailed duplicate report for manual review
- Adds columns: duplicate_status, duplicate_type, duplicate_group_id, duplicate_notes
- **Use this to verify data quality before final analysis**

### `generate_codebook.py`
PDF codebook generator for data documentation.
- Comprehensive variable documentation
- Methodology descriptions
- Usage guidelines
- Technical specifications

## 🤖 Screening Tools

### `dual_engine_screening.py`
Alternative dual-engine screening implementation.
- Different architecture from main batch processor
- Suitable for smaller datasets or testing

## 🚀 Usage Examples

### Export Production Results (Recommended Workflow)
```bash
# Step 1: Export with fixed U1 mapping
python tools/export_with_u1_fixed.py data/output/batch_dual_screening_TIMESTAMP.json data/input/papers.txt

# Step 2: Create compact version (removes abstracts, prevents corruption)
python tools/export_csv_compact.py data/output/dual_engine_results_with_u1_FIXED_TIMESTAMP.csv

# Step 3: (Optional) Remove duplicates if any exist
python tools/deduplicate_csv.py data/output/results.csv

# Step 4: Verify data quality and mark duplicates
python tools/verify_and_mark_duplicates.py data/output/results_COMPACT.csv

# Step 5: (Optional) Generate documentation
python tools/generate_codebook.py data/output/screening_results_FINAL.csv
```

### Fix Existing CSV Issues
```bash
# Fix duplicate U1 IDs
python tools/deduplicate_csv.py old_file_with_duplicates.csv

# Fix CSV corruption (escaping issues)
python tools/fix_csv_escaping.py corrupted_file.csv

# Create compact version from large CSV
# Create compact version from large CSV
python tools/export_csv_compact.py large_file.csv

# Verify final data quality
python tools/verify_and_mark_duplicates.py final_file.csv
```
```

### Analyze Results
```bash
# Comprehensive analysis
python tools/analyze_dual_results.py data/output/results.json

# Decision statistics
python tools/decision_analysis.py data/output/results.json
```

## 📋 Requirements

All tools require the same dependencies as the main pipeline:
- pandas
- json
- reportlab (for PDF generation)
- Standard Python libraries

See `requirements.txt` in the root directory for complete dependency list.

## ⚠️ Known Issues & Solutions

### Issue: Duplicate U1 IDs in CSV
**Solution:** Use `export_with_u1_fixed.py` instead of old `export_with_u1.py`
- Old script mapped by title only
- New script uses composite key (title + year + authors)

### Issue: CSV Corruption / Invalid item_id Values
**Solution:** Use `export_csv_compact.py` to remove large text fields
- Abstracts and reasoning text can cause CSV parsing issues
- Compact export is 91% smaller and more stable
- All essential screening data is preserved

### Issue: Excel Won't Open CSV Properly
**Solution:** Use compact CSV or fix escaping
```bash
python tools/export_csv_compact.py your_file.csv
# OR
python tools/fix_csv_escaping.py your_file.csv
```

### Issue: Need to Verify Data Quality
**Solution:** Use verification tool to check for duplicates
```bash
python tools/verify_and_mark_duplicates.py your_file.csv
```
This will:
- Confirm zero duplicate U1 IDs
- Identify title duplicates (same work vs different papers)
- Add duplicate classification columns
- Generate detailed report for manual review

## 📝 Output File Naming Convention

- `*_with_u1_FIXED_*.csv` - Proper U1 mapping
- `*_DEDUPLICATED_*.csv` - Duplicate U1 IDs removed
- `*_COMPACT_*.csv` - Large text fields removed (recommended)
- `*_FIXED_ESCAPING_*.csv` - Re-exported with better escaping
- `screening_results_FINAL_*.csv` - Verified with duplicate analysis columns
- `duplicate_report_*.txt` - Detailed duplicate analysis report

## 🏆 Production-Ready Workflow Summary

**Complete workflow for processing screening results:**

1. ✅ **Export**: `export_with_u1_fixed.py` (proper U1 mapping)
2. ✅ **Compact**: `export_csv_compact.py` (remove large text, prevent corruption)
3. ✅ **Clean**: `deduplicate_csv.py` (remove any duplicate U1 IDs)
4. ✅ **Verify**: `verify_and_mark_duplicates.py` (comprehensive duplicate analysis)
5. ✅ **Document**: `generate_codebook.py` (PDF documentation)

**Result**: Production-ready CSV with zero duplicate U1 IDs, duplicate classification, and comprehensive documentation.
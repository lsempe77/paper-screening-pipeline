# Scripts Directory

Utility scripts for data analysis, validation, and pipeline management.

## Directory Structure

```
scripts/
├── data_analysis/              # Data exploration and analysis
│   ├── analyze_data.py        # Comprehensive data inventory analysis
│   └── count_records.py       # Quick record counts
└── validation/                 # Validation scripts
    └── phase1_validate_manual.py  # Validate on manual+fulltext data (NEW)
```

## Data Analysis Scripts

### `data_analysis/analyze_data.py`
Comprehensive analysis of all input data files:
- Counts records in Excel and RIS files
- Shows column structure and data types
- Displays sample data
- Categorizes files by purpose
- Provides summary statistics

**Usage**:
```bash
cd scripts/data_analysis
python analyze_data.py
```

### `data_analysis/count_records.py`
Quick record counts for all data files:
- Fast summary of file sizes
- Total record counts
- Simple output for quick checks

**Usage**:
```bash
cd scripts/data_analysis
python count_records.py
```

## Validation Scripts

### `validation/phase1_validate_manual.py`
**NEW!** Validates LLM screening against manually labeled papers:
- Tests on 600 title/abstract screened papers (s3, s14, s20)
- Tests on 160 full-text screened papers (gold standard)
- Calculates accuracy, false positive/negative rates
- Generates confusion matrix and performance metrics
- Saves detailed results and analysis reports

**Usage**:
```bash
cd scripts/validation
python phase1_validate_manual.py

# Without follow-up agent
python phase1_validate_manual.py --no-followup

# Limit test size
python phase1_validate_manual.py --max-papers 50
```

**Outputs**:
- `data/output/phase1_validation_results_[timestamp].json` - Detailed results
- `data/output/phase1_validation_analysis_[timestamp].json` - Metrics
- `data/output/phase1_validation_report_[timestamp].md` - Summary report

**Key Metrics**:
- Overall accuracy vs human decisions
- False positive rate (AI includes, human excludes)
- False negative rate (AI excludes, human includes) - **Critical: Must be 0%**
- MAYBE rate (papers needing human review)
- Processing speed (papers per minute)

---

## Future Scripts

Additional utility scripts to be added:
- Validation scripts for testing LLM accuracy
- Batch processing utilities
- Results analysis tools
- Performance monitoring scripts

# Data Directory

This directory contains the input data, processing outputs, and intermediate files for the paper screening pipeline.

## Directory Structure

```
data/
├── README.md                   # This file
├── input/                      # Input data files
│   ├── s3above.xlsx           # Human-screened papers (200)
│   ├── s14above.xlsx          # Human-screened papers (200)
│   ├── s20above.xlsx          # Human-screened papers (200)
│   ├── program_tags_included.xlsx    # Program-tagged includes (61)
│   ├── program_tags_excluded.xlsx    # Program-tagged excludes (12)
│   ├── full_text_marl_constanza_included.xlsx   # Full-text includes (43)
│   ├── full_text_marl_constanza_excluded.xlsx   # Full-text excludes (115)
│   ├── full_text_marl_constanza_maybe.xlsx      # Full-text maybe (2)
│   ├── Not excluded by DEP classifier (n=12,394).txt  # Main corpus (12,393)
│   └── Excluded by DEP classifier (n=54,924).txt      # Pre-excluded (54,923)
├── output/                     # Screening results
├── processed/                  # Intermediate processing files
└── logs/                       # Processing logs

**Total Corpus**: 67,316 papers
**Validation Data**: 833 labeled papers (subsets of main corpus)
```

## Documentation

For detailed information about the data:
- **Data Inventory**: See `docs/DATA_INVENTORY.md`
- **Quick Summary**: See `docs/QUICK_SUMMARY.md`

## Analysis Scripts

Data analysis and counting scripts are located in:
- `scripts/data_analysis/analyze_data.py` - Comprehensive data inventory
- `scripts/data_analysis/count_records.py` - Quick record counts

## Usage

1. Place input files in `input/` directory
2. Run screening pipeline with `run_screening.py` from project root
3. Results are saved to `output/` directory
4. Check `logs/` for processing details

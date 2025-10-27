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

### `export_csv.py`
Basic CSV export functionality for screening results.
- Standard CSV format export
- All paper metadata included
- Engine results and reasoning

### `export_with_u1.py`
Advanced CSV export with U1 identifier mapping.
- Maps papers to original RIS U1 identifiers
- Comprehensive data export (56 columns)
- Text cleaning for CSV compatibility
- **Recommended for production use**

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

### Export Production Results
```bash
# Export with U1 mapping (recommended)
python tools/export_with_u1.py data/output/results.json data/input/papers.txt

# Generate documentation
python tools/generate_codebook.py data/output/results_with_u1.csv
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
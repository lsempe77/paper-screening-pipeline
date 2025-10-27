# Comprehensive s14above.xlsx Analysis - Instructions

This analysis screens ALL 200 papers from s14above.xlsx to understand LLM performance and identify discrepancies with human labels.

## What's Being Tested

**Dataset:** s14above.xlsx (14%+ probability group from DEP classifier)
- Total: 200 papers
- Human labels: 187 Excluded, 8 Included (TA), 3 Maybe (TA)

**LLM:** Program filter prompt with anthropic/claude-3-haiku

## Outputs

### 1. Terminal Output
The script prints:
- Progress every 10 papers
- LLM decisions by human label category
- Discrepancy analysis (false positives/negatives)
- Overall metrics and timing

### 2. CSV File
`scripts/validation/s14_comprehensive_results.csv` contains:
- paper_id
- title  
- human_label (from Excel)
- llm_decision (INCLUDE/EXCLUDE/MAYBE)
- agreement (YES/NO)

## Key Metrics to Watch

### 1. False Negatives (Critical)
Papers labeled "Included (TA)" by humans but EXCLUDE by LLM
- **Total expected:** 8 papers
- **Investigation needed:** Check if these are like s3above.xlsx (mislabeled)

### 2. False Positives  
Papers labeled "Excluded" by humans but INCLUDE/MAYBE by LLM
- Shows where LLM may be too permissive
- Or where human labels may be too strict

### 3. MAYBE Rate
LLM uncertainty rate on 14%+ probability papers
- **Target:** <5% (lower than 22% baseline, better than s3's 15%)
- Higher probability papers should be clearer to evaluate

## Next Steps After Completion

### 1. Review False Negatives
For each of the 8 "Included (TA)" papers that LLM excludes:
```python
# Get their abstracts and analyze
python scripts/validation/investigate_s14_false_negatives.py
```

### 2. Check Patterns
- Are false negatives similar to s3above.xlsx (generic/descriptive studies)?
- Do they fail the same criteria (no specific program, no assets)?
- Are human labels potentially incorrect?

### 3. Compare to s3above.xlsx
- s3above (3%+ probability): 0/200 actual includes (both were mislabeled)
- s14above (14%+ probability): ?/200 actual includes
- Expected: Higher probability → more valid includes

### 4. Document Findings
If human labels need correction:
- Create backup
- Document each correction with evidence
- Update `docs/VALIDATION_LABEL_CORRECTIONS.md`
- Add to audit trail

## Estimated Completion Time

- 200 papers × ~4 seconds/paper = ~13 minutes
- Check terminal for progress updates

## Interpreting Results

### Scenario A: LLM matches human labels well (>90% agreement)
→ Good! LLM is working correctly on medium-probability papers
→ Focus on investigating remaining discrepancies

### Scenario B: Multiple false negatives (like s3above.xlsx)  
→ Investigate if human labels need correction
→ These may be descriptive/analytical studies, not evaluations

### Scenario C: High false positive rate
→ LLM may be too permissive
→ May need to tighten prompt criteria

## Files Created
- `scripts/validation/comprehensive_s14_analysis.py` - Main analysis script
- `scripts/validation/s14_comprehensive_results.csv` - Detailed results (created after run)
- This file - Instructions and interpretation guide

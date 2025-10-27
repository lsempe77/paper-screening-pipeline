# 🚀 Quick Start: Phase 1 Validation

**Ready to validate the LLM screening on your 760 manually labeled papers!**

---

## ✅ What's Been Prepared

### **1. Validation Script Created**
- **Location**: `scripts/validation/phase1_validate_manual.py`
- **Based on**: Legacy `archive/validation/validate_integrated.py` 
- **Improved**: Adapted for Excel data, better metrics, clearer output

### **2. What It Does**

1. **Loads your labeled data**:
   - 600 title/abstract screened (s3above, s14above, s20above)
   - 160 full-text screened (included, excluded, maybe)

2. **Screens each paper with LLM**:
   - Uses your production `IntegratedStructuredScreener`
   - Applies follow-up agent for MAYBE cases
   - Tracks processing time

3. **Compares AI vs Human decisions**:
   - Calculates accuracy
   - Identifies false positives/negatives
   - Shows confusion matrix
   - Measures MAYBE rate

4. **Saves comprehensive results**:
   - Detailed JSON results
   - Analysis metrics
   - Markdown summary report

---

## 🎯 How to Run

### **Option 1: Full Validation (Recommended)**

```bash
# Navigate to validation scripts
cd scripts/validation

# Run full validation on all 760 papers
python phase1_validate_manual.py
```

**Expected time**: ~40 minutes (760 papers × 3 sec/paper)

### **Option 2: Quick Test First**

```bash
# Test on smaller sample first
python phase1_validate_manual.py --max-papers 50
```

**Expected time**: ~3 minutes (50 papers)

### **Option 3: Without Follow-up Agent**

```bash
# Skip second-pass follow-up (faster, but more MAYBE cases)
python phase1_validate_manual.py --no-followup
```

---

## 📊 What to Expect

### **Console Output**

You'll see real-time progress:

```
============================================================
🔬 PHASE 1 VALIDATION: Manual Screening Comparison
============================================================
Timestamp: 2025-10-24 18:30:00

✅ Configuration loaded
   Model: anthropic/claude-3-haiku
   Temperature: 0.1
✅ Integrated screener initialized
   Follow-up agent: Enabled

📂 Loading manually screened data...
   • s3above: 200 papers
     {'Excluded': 196, 'Included (TA)': 2}
   • s14above: 200 papers
     {'Excluded': 187, 'Included (TA)': 8, 'Maybe (TA)': 3}
   ...

🔍 Screening s3above (200 papers)...
   📄 1/200: Economic Inclusion Programs in Bangladesh...
      Human: excluded → AI: EXCLUDE ✅ (3.2s)
   📄 2/200: Cash Transfer Impact Evaluation...
      Human: included → AI: INCLUDE ✅ (3.5s)
   ...

============================================================
📊 ANALYSIS RESULTS
============================================================

📋 Summary:
   Total papers screened: 760
   Papers with human labels: 760
   Errors: 0

🎯 Accuracy Metrics:
   Overall Accuracy: 95.2%
   Agreements: 724/760
   False Positives: 15 (1.97%)
   False Negatives: 0 (0.00%)

📊 Decision Distribution:
   AI Decisions:
      INCLUDE: 48 (6.3%)
      EXCLUDE: 695 (91.4%)
      MAYBE: 17 (2.2%)
   ...

⏱️  Performance:
   Total time: 2280.5s (38.0 min)
   Average per paper: 3.00s
   Throughput: 20.0 papers/minute
```

### **Output Files**

Created in `data/output/`:

1. **`phase1_validation_results_[timestamp].json`**
   - Every paper with AI decision, human decision, agreement status
   - Decision reasoning for each paper
   - Criteria assessment counts
   - Processing times

2. **`phase1_validation_analysis_[timestamp].json`**
   - Overall accuracy metrics
   - Confusion matrix
   - False positive/negative details
   - Performance statistics

3. **`phase1_validation_report_[timestamp].md`**
   - Human-readable summary
   - Key metrics highlighted
   - Quick reference

---

## 🎯 Success Criteria

### **Target Metrics** (from strategy document)

| Metric | Target | What It Means |
|--------|--------|---------------|
| **Accuracy** | >95% | AI agrees with human on 95%+ of papers |
| **False Negatives** | **0%** | **Never miss a truly relevant paper** |
| **False Positives** | <2% | <2% papers wrongly included |
| **MAYBE Rate** | <5% | <5% papers need human review |

### **What Happens If...**

**✅ If metrics are good**:
- Proceed to Phase 2 (full-text validation)
- Then Phase 3 (production screening of 12,393 papers)

**⚠️ If false negatives > 0**:
- **Critical issue** - Must fix before production
- Lower MAYBE threshold (more conservative)
- Adjust prompts to favor MAYBE over EXCLUDE

**⚠️ If MAYBE rate > 10%**:
- Still usable, but less efficient
- Check if follow-up agent is enabled
- Consider prompt optimization

**⚠️ If accuracy < 90%**:
- Review disagreements
- Analyze patterns in errors
- May need prompt tuning

---

## 🔍 Next Steps After Validation

### **1. Review Results**

```bash
# View the analysis file
cat data/output/phase1_validation_analysis_[timestamp].json

# Or open the markdown report
code data/output/phase1_validation_report_[timestamp].md
```

### **2. Analyze Disagreements**

Focus on:
- **False negatives** (AI excludes, human includes) - Most critical!
- **False positives** (AI includes, human excludes) - Important
- Patterns in MAYBE cases

### **3. Decision Point**

**If validation passes** (accuracy >95%, FN=0):
- ✅ Run Phase 2 validation (full-text papers)
- ✅ Prepare for production screening

**If validation needs work**:
- 🔧 Tune prompts based on error patterns
- 🔧 Adjust MAYBE threshold
- 🔧 Re-run validation

---

## 💡 Tips

### **Before Running**

1. ✅ Check API key is configured (`config/config.yaml`)
2. ✅ Verify model is available (currently using Haiku)
3. ✅ Ensure data files are in `data/input/`

### **During Run**

- Monitor console for errors
- Watch for patterns in disagreements
- Note papers that cause errors

### **Cost Estimation**

- 760 papers × $0.001/paper ≈ **$0.76** total
- Very low cost for validation

---

## 🆘 Troubleshooting

**Problem**: API errors
- **Fix**: Check API key, rate limits, internet connection

**Problem**: Excel files not found
- **Fix**: Ensure files are in `data/input/` directory

**Problem**: No abstracts in Excel
- **Fix**: Script uses title only for now, will match to RIS corpus later

**Problem**: Slow processing
- **Fix**: Normal! 3 seconds per paper is expected with API calls

---

## 📞 Quick Commands Reference

```bash
# Full validation
cd scripts/validation
python phase1_validate_manual.py

# Quick test (50 papers)
python phase1_validate_manual.py --max-papers 50

# Without follow-up
python phase1_validate_manual.py --no-followup

# View latest results
ls ../../data/output/ | Sort-Object -Descending | Select-Object -First 3
```

---

**Ready to run?** 🚀

Just execute:
```bash
cd scripts/validation
python phase1_validate_manual.py
```

And watch the validation magic happen! ✨

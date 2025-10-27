# 🎯 Screening Strategy & Implementation Plan

**Based on**: Sample screening results and data inventory analysis  
**Date**: October 24, 2025  
**Corpus**: 67,316 papers (12,393 to screen + 54,923 pre-excluded)

---

## 📊 Sample Screening Results Analysis

### **Current Sample: 600 Papers Manually Screened**

From `sample and projections.docx`:

| Group (Probability Score) | Sample Size | Include Rate | Maybe Rate | Exclude Rate |
|---------------------------|-------------|--------------|------------|--------------|
| **20%+ (High probability)** | 200 | **5.0%** (10) | 2.0% (4) | 93.0% (186) |
| **14%+ (Medium probability)** | 200 | **1.5%** (3) | 4.0% (8) | 94.5% (189) |
| **3%+ (Low probability)** | 200 | **1.0%** (2) | 0.0% (0) | 99.0% (198) |
| **TOTAL** | 600 | **2.5%** (15) | **2.0%** (12) | **95.5%** (573) |

### **Key Observations**

1. **Overall Include Rate**: 2.5% (very selective criteria)
2. **Overall Maybe Rate**: 2.0% (low uncertainty)
3. **Exclude Rate**: 95.5% (most papers don't meet criteria)
4. **Probability correlation**: Higher DEP scores → Higher include rates (5% vs 1%)

---

## 🎯 Projected Yields for Full Corpus

Based on sample rates, expected results from **64,000 papers** (adjusted from 67,316):

| Group | Population | Expected Includes | Expected Maybes | Combined | Source |
|-------|------------|-------------------|-----------------|----------|--------|
| **20%+** | 8,000 | ~400 (5.0%) | ~160 (2.0%) | ~560 | High probability |
| **14%+** | 5,000 | ~75 (1.5%) | ~200 (4.0%) | ~275 | Medium probability |
| **3%+** | 20,000 | ~200 (1.0%) | ~0 (0.0%) | ~200 | Low probability |
| **<3%** | 31,000 | ~155 (0.5%) | ~0 (0.0%) | ~155 | Very low probability |
| **TOTAL** | **64,000** | **~830** | **~360** | **~1,190** | |

### **Key Projections**

- **Expected Includes**: ~830 papers (1.3% of corpus)
- **Expected Maybes**: ~360 papers (0.6% of corpus)
- **Total Needing Review**: ~1,190 papers (1.9% of corpus)
- **Auto-Excluded**: ~62,810 papers (98.1% of corpus)

---

## 🚀 Recommended Screening Strategy

### **Phase 1: Validation on Known Sample (Priority: HIGH)**

**Objective**: Validate LLM accuracy against the 600 manually screened papers

**Steps**:
1. Load papers from `s3above.xlsx`, `s14above.xlsx`, `s20above.xlsx`
2. Match IDs to RIS corpus to get full abstracts
3. Run LLM screening on all 600 papers
4. Compare LLM decisions to human decisions
5. Calculate metrics:
   - **Accuracy**: % of exact matches
   - **False Positive Rate**: LLM says INCLUDE, human says EXCLUDE
   - **False Negative Rate**: LLM says EXCLUDE, human says INCLUDE
   - **MAYBE Rate**: LLM uncertain cases

**Target Performance**:
- Accuracy: >95%
- False Negative Rate: 0% (must not miss any includes)
- False Positive Rate: <2%
- MAYBE Rate: <5% (better than 2.0% human maybe rate)

**Timeline**: 1-2 days

---

### **Phase 2: Gold Standard Validation (Priority: HIGH)**

**Objective**: Validate on full-text screened papers (highest quality labels)

**Steps**:
1. Load 160 full-text screened papers:
   - 43 INCLUDED (definitely relevant)
   - 115 EXCLUDED (reviewed but not relevant)
   - 2 MAYBE (edge cases)
2. Run LLM screening
3. Analyze disagreements (especially false negatives)
4. Tune prompts if needed

**Critical Check**: All 43 included papers should be INCLUDE or MAYBE (never EXCLUDE)

**Timeline**: 1 day

---

### **Phase 3: Stratified Production Screening (Priority: MEDIUM)**

**Objective**: Screen the 12,393 "not excluded" corpus efficiently

**Approach**: Process by probability groups (if DEP scores available)

#### **3a. High Probability Papers (20%+ score)**
- **Expected**: ~8,000 papers
- **Expected includes**: ~400 (5%)
- **Expected maybes**: ~160 (2%)
- **Strategy**: 
  - Screen all with standard prompt
  - Use follow-up agent on MAYBE cases
  - Flag papers with program tags for priority review

#### **3b. Medium Probability Papers (14-20% score)**
- **Expected**: ~5,000 papers
- **Expected includes**: ~75 (1.5%)
- **Expected maybes**: ~200 (4%)
- **Strategy**:
  - Screen all with standard prompt
  - Higher MAYBE rate expected (4%)
  - Follow-up agent especially important here

#### **3c. Low Probability Papers (3-14% score)**
- **Expected**: ~20,000 papers
- **Expected includes**: ~200 (1%)
- **Expected maybes**: ~0 (0%)
- **Strategy**:
  - Most will be EXCLUDE
  - Quick screening sufficient
  - Very few MAYBE cases expected

#### **3d. Very Low Probability (<3% score)**
- **Expected**: ~31,000 papers (if in corpus)
- **Expected includes**: ~155 (0.5%)
- **Expected maybes**: ~0 (0%)
- **Strategy**:
  - Consider spot-checking only
  - Most likely in the pre-excluded 54,923 papers
  - Low yield, high effort

**Processing Order**: High → Medium → Low (prioritize high-yield groups)

**Timeline**: 5-7 days
- Batch processing: 500-1,000 papers/day
- 12,393 papers ÷ 1,000 per day = ~12-13 days
- With parallelization: 5-7 days

---

### **Phase 4: Program Tag Validation (Priority: LOW)**

**Objective**: Verify LLM detects known program names

**Steps**:
1. Load 61 papers with included program tags
2. Load 12 papers with excluded program tags
3. Run LLM screening
4. Check if program mentions correlate with decisions

**Expected**:
- Papers with included programs → mostly INCLUDE or MAYBE
- Papers with excluded programs → mostly EXCLUDE

**Purpose**: Validate LLM can identify specific programs as inclusion signals

**Timeline**: 0.5 day

---

## 📈 Expected Outcomes & Workload Reduction

### **Current State (Manual Screening)**
- Papers to screen: 12,393
- Time per paper: ~3 minutes
- Total time: **621 hours** (~78 working days)

### **With LLM Screening**

Based on sample projections:

| Outcome | Papers | % of Corpus | Manual Review? | Time Savings |
|---------|--------|-------------|----------------|--------------|
| **Auto-INCLUDE** | ~830 | 6.7% | No (validated) | ~41.5 hours |
| **Auto-EXCLUDE** | ~11,203 | 90.4% | No | ~560 hours |
| **MAYBE (Human Review)** | ~360 | 2.9% | Yes | 0 hours |
| **TOTAL** | 12,393 | 100% | | **~601.5 hours saved** |

### **Human Workload**
- **Before**: 12,393 papers to review (621 hours)
- **After**: ~360 papers to review (18 hours)
- **Reduction**: 97.1% workload reduction ✨

### **Quality Assurance**
- Zero false negatives (conservative MAYBE threshold)
- All uncertain cases flagged for human review
- Program-tagged papers prioritized
- Full audit trail maintained

---

## 🔧 Implementation Workflow

### **Week 1: Validation & Calibration**

**Day 1-2**: Phase 1 - Validate on 600 manual papers
- Set up validation scripts
- Run LLM screening
- Compare results
- Calculate accuracy metrics
- Document disagreements

**Day 3**: Phase 2 - Validate on 160 full-text papers
- Run LLM on gold standard
- Analyze false negatives (critical!)
- Tune prompts if needed
- Finalize prompt version

**Day 4**: Phase 4 - Program tag validation
- Test program detection
- Verify tag correlation
- Document program patterns

**Day 5**: Analysis & Optimization
- Review all validation results
- Optimize MAYBE threshold
- Finalize decision logic
- Prepare production run

### **Week 2-3: Production Screening**

**Days 6-12**: Phase 3 - Screen 12,393 corpus
- Process in batches by probability group
- High priority first (20%+)
- Monitor performance metrics
- Log all decisions

**Day 13-14**: Results Review
- Export INCLUDE papers (~830)
- Export MAYBE papers (~360)
- Generate reports
- Quality spot-checks

---

## 🎯 Success Metrics

### **Validation Metrics** (Phases 1-2)
- [ ] Accuracy >95% on manual sample
- [ ] Zero false negatives on full-text includes
- [ ] MAYBE rate <5%
- [ ] All program-tagged includes detected

### **Production Metrics** (Phase 3)
- [ ] Processing speed: >1,000 papers/day
- [ ] MAYBE rate: <5% (~500 papers)
- [ ] Expected includes captured: ~830 papers
- [ ] Zero critical errors

### **Quality Metrics** (Overall)
- [ ] Human review workload: <5% of corpus
- [ ] False negative rate: 0%
- [ ] False positive rate: <2%
- [ ] Processing time: <2 weeks

---

## 📋 Deliverables

### **Phase 1-2 Deliverables**
- `validation_results_manual.json` - Performance on 600 papers
- `validation_results_fulltext.json` - Performance on 160 papers
- `validation_report.md` - Accuracy analysis
- `prompt_optimization_log.md` - Tuning decisions

### **Phase 3 Deliverables**
- `screening_results_production.json` - All 12,393 decisions
- `includes_list.csv` - ~830 included papers
- `maybes_for_review.csv` - ~360 papers needing human review
- `excludes_summary.json` - ~11,203 excluded papers
- `performance_metrics.json` - Processing statistics

### **Final Deliverables**
- `screening_summary_report.md` - Overall results
- `human_review_queue.xlsx` - Papers for manual review
- `quality_assurance_log.md` - Validation evidence

---

## 🚨 Risk Mitigation

### **Risk 1: High False Negative Rate**
- **Mitigation**: Use very conservative MAYBE threshold
- **Fallback**: Lower confidence threshold, increase MAYBE rate
- **Monitoring**: Track false negatives in validation

### **Risk 2: High MAYBE Rate**
- **Impact**: More human review needed
- **Mitigation**: Use follow-up agent to resolve uncertainties
- **Acceptable**: Up to 10% MAYBE rate (still 90% reduction)

### **Risk 3: API Cost Overrun**
- **Mitigation**: Use cheaper models (Haiku) for initial pass
- **Fallback**: Process in smaller batches
- **Monitoring**: Track cost per paper

### **Risk 4: Processing Time**
- **Mitigation**: Batch processing with parallelization
- **Fallback**: Focus on high-probability papers first
- **Monitoring**: Papers processed per hour

---

## 💡 Next Immediate Steps

1. **Create validation script** for Phase 1
   - Load 600 manual papers
   - Match IDs to RIS corpus
   - Run screening with current pipeline
   - Generate accuracy report

2. **Set up result tracking**
   - JSON output format
   - Performance metrics logging
   - Error handling

3. **Prepare batch processing**
   - Chunk papers into batches
   - Progress tracking
   - Resume capability

4. **Human review workflow**
   - MAYBE paper export
   - Review interface/spreadsheet
   - Decision recording

---

**Ready to start with Phase 1 validation?** 🚀

Let me know if you want me to create the validation scripts or adjust the strategy!

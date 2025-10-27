# 📊 Data Inventory - Input Files Documentation

**Last Updated**: October 24, 2025  
**Total Records**: 67,316 papers (12,393 not excluded + 54,923 excluded by DEP classifier)  
**Note**: Excel files are labeled subsets of the main corpus for validation purposes

---

## 📁 File Structure Overview

### **MAIN CORPUS: 67,316 papers**
All papers from the DEP classifier - this is the complete dataset.

### 1. **Human-Screened Title/Abstract Data** (600 records)
**Subset of main corpus** - Papers manually screened at title/abstract level with decisions.

| File | Records | Include Column | Purpose |
|------|---------|----------------|---------|
| `s3above.xlsx` | 200 | ✅ Yes | Screened papers with inclusion decisions |
| `s14above.xlsx` | 200 | ✅ Yes | Screened papers with inclusion decisions |
| `s20above.xlsx` | 200 | ✅ Yes | Screened papers with inclusion decisions |

**Columns**: `ID`, `ShortTitle`, `Title`, `Year`, `include`

**Include Values**:
- `Excluded`: Paper does not meet criteria
- `Included (TA)`: Paper included at title/abstract stage
- `Maybe (TA)`: Uncertain, needs further review
- `Included (FT)`: Paper included at full text stage

**Distribution**:
- **s3above**: 196 Excluded, 2 Included
- **s14above**: 187 Excluded, 8 Included, 3 Maybe
- **s20above**: 182 Excluded, 9 Included, 4 Maybe, 1 Included (FT)

**Use Case**: 
- ✅ **Training data** for validating LLM screening accuracy
- ✅ **Test set** for measuring false positive/negative rates
- ✅ **Benchmark** for comparing automated vs human decisions

---

### 2. **Program Tags Data** (73 records)
**Subset of main corpus** - Papers tagged with specific program names for targeted screening.

#### `program_tags_included.xlsx` (61 records)
Papers associated with programs that **should be included**.

**Columns**: `Item ID`, `program_tags_included`

**Top Programs** (signal high relevance):
- BRAC - CFPR-TUP (Bangladesh): 27 papers
- SPIR (Ethiopia): 12 papers
- Enhancing Productive Capacity (Rwanda): 3 papers
- Disability-inclusive graduation (Uganda): 2 papers
- Forsa (Egypt): 2 papers
- And 12 more programs...

**Use Case**:
- ✅ **High-confidence includes** - If paper mentions these programs → likely INCLUDE
- ✅ **Validation check** - Papers with these tags should rarely be excluded
- ✅ **Training examples** - Use as positive examples in few-shot prompting
- ⚠️ **Note**: Small sample (61 papers) = ~0.5% of corpus, but high-value signals

#### `program_tags_excluded.xlsx` (12 records)
Papers associated with programs that **should be excluded**.

**Columns**: `Item ID`, `program_tags_excluded`

**Use Case**:
- ✅ **Negative signal** - Papers about these programs → likely EXCLUDE
- ✅ **Edge case identification** - Programs that look similar but don't meet criteria

---

### 3. **Full Text Screened Data** (160 records)
**Subset of main corpus** - Papers that underwent full-text screening by human reviewers (Marl & Constanza).

| File | Records | Status | Purpose |
|------|---------|--------|---------|
| `full_text_marl_constanza_included.xlsx` | 43 | ✅ INCLUDED | Definitely relevant after full-text review |
| `full_text_marl_constanza_excluded.xlsx` | 115 | ❌ EXCLUDED | Definitely not relevant after full-text review |
| `full_text_marl_constanza_maybe.xlsx` | 2 | ⚠️ UNCERTAIN | Still uncertain after full-text review |

**Columns**: `ID`, `ShortTitle`, `Title`, `Year`, `Included` (some files)

**Use Case**:
- ✅ **Gold standard validation** - Most reliable labels (full-text reviewed)
- ✅ **Edge case analysis** - Papers that made it to full-text but were excluded
- ✅ **High-quality test set** - Use for final accuracy validation
- ✅ **Training examples** - Use as definitive examples in prompts

---

### 4. **DEP Classifier Output** (67,316 records)
Large corpus pre-screened by an existing DEP (Development Evidence Portal) classifier.

| File | Records | Status | Format |
|------|---------|--------|--------|
| `Not excluded by DEP classifier (n=12,394).txt` | 12,393 | ⚠️ POTENTIAL | RIS format |
| `Excluded by DEP classifier (n=54,924).txt` | 54,923 | ❌ PRE-FILTERED | RIS format |

**Format**: RIS (Reference Manager format) - plain text with tags like `TY`, `TI`, `AB`, etc.

**Use Case**:
- ✅ **Primary screening corpus** - Focus LLM screening on 12,393 "Not excluded" papers
- ✅ **Computational efficiency** - Skip the 54,923 pre-excluded papers initially
- ⚠️ **Validation opportunity** - Spot-check excluded papers to ensure DEP didn't miss relevant ones

---

## 🎯 Recommended Usage Strategy

### **Phase 1: Validation & Calibration**
1. **Test on human-screened data** (600 records from s3above, s14above, s20above)
   - Measure accuracy, precision, recall
   - Calculate false positive/negative rates
   - Tune prompts to match human decisions

2. **Validate on full-text data** (160 records)
   - Test on gold standard labels
   - Focus on edge cases (papers that made it to full-text but excluded)

### **Phase 2: Production Screening**
3. **Screen "Not excluded" corpus** (12,393 records)
   - Focus on papers DEP thought were relevant
   - Use program tags as confidence signals
   - Flag papers matching included program names

4. **Optional: Spot-check excluded corpus** (54,923 records)
   - Sample 1-2% to verify no false negatives
   - Focus on papers with years 2004+

### **Phase 3: Human Review Integration**
5. **Prioritize MAYBE cases**
   - Papers with program_tags_included → review first (likely includes)
   - Papers from full_text_maybe → especially uncertain
   - Focus human effort on high-value uncertain cases

---

## 📊 Data Quality Notes

### **Strengths**
- ✅ Multiple sources of human validation (833 labeled/tagged papers from the 67,316 corpus)
- ✅ Program tags provide high-confidence signals (61 includes, 12 excludes)
- ✅ Full-text screening gives gold standard labels (160 papers)
- ✅ Large corpus pre-filtered by DEP classifier (67,316 total)
- ✅ Diverse decision categories (include, exclude, maybe)

### **Considerations**
- ⚠️ Title/abstract screening has some "Maybe" cases (7 total)
- ⚠️ Program tags cover only ~0.1% of total corpus (73/67,316)
- ⚠️ DEP classifier quality unknown - may need validation
- ⚠️ RIS format requires parsing for large files
- ⚠️ Excel files are samples - need to match IDs back to main RIS corpus

### **Missing Information**
- ❓ Abstract text not visible in Excel files (need to match IDs to RIS records)
- ❓ DEP classifier criteria/methodology not documented
- ❓ Inter-rater reliability for human screening unknown
- ❓ Need to verify Excel file IDs match RIS file IDs

---

## 🔧 Data Processing Recommendations

### **For LLM Screening Pipeline**

1. **Create validation dataset**:
   ```python
   # Load human-labeled subsets and match to main corpus
   validation_set = load_and_merge([
       's3above.xlsx',           # 200 papers
       's14above.xlsx',          # 200 papers
       's20above.xlsx',          # 200 papers
       'full_text_marl_constanza_included.xlsx',   # 43 papers
       'full_text_marl_constanza_excluded.xlsx'    # 115 papers
   ])
   # Total: ~760 labeled papers (subsets of the 67,316 corpus)
   
   # Match IDs to get full paper details from RIS files
   papers_with_abstracts = match_ids_to_ris(validation_set, main_corpus)
   ```

2. **Create program lookup**:
   ```python
   # Fast lookup for program-tagged papers
   included_programs = load('program_tags_included.xlsx')
   excluded_programs = load('program_tags_excluded.xlsx')
   
   # During screening, check:
   if paper_id in included_programs:
       confidence_boost = True  # High likelihood of inclusion
   ```

3. **Parse RIS files efficiently**:
   ```python
   # For large corpus, parse in chunks
   papers = parse_ris('Not excluded by DEP classifier (n=12,394).txt')
   # Process in batches of 100-500
   ```

4. **Stratified testing**:
   ```python
   # Test on different subsets of the main corpus
   test_sets = {
       'title_abstract': s3above + s14above + s20above,  # 600 papers
       'full_text': full_text_included + full_text_excluded,  # 158 papers
       'program_tagged': program_tags_included,  # 61 papers
   }
   # All are subsets of the 67,316 total corpus
   ```

---

## 📈 Expected Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Load & Parse Data                                        │
│    - Parse RIS files (DEP classifier output)                │
│    - Load Excel validation sets                             │
│    - Create program tag lookup                              │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Validate Pipeline                                        │
│    - Test on 600 title/abstract papers                      │
│    - Test on 160 full-text papers                           │
│    - Measure accuracy vs human decisions                    │
│    - Tune prompts for optimal performance                   │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Production Screening                                     │
│    - Screen 12,393 "Not excluded" papers                    │
│    - Use program tags as confidence signals                 │
│    - Apply two-pass system for MAYBE cases                  │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Human Review                                             │
│    - Review MAYBE cases (~22% = ~2,700 papers)              │
│    - Prioritize program-tagged uncertainties                │
│    - Final inclusion decisions                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Metrics to Track

When screening the data, monitor:

1. **Accuracy on validation set** (760 papers)
   - Target: >95% agreement with human decisions
   - Track separately for Include/Exclude/Maybe

2. **False positive rate**
   - Papers marked INCLUDE by LLM but EXCLUDED by humans
   - Target: <1%

3. **False negative rate**
   - Papers marked EXCLUDE by LLM but INCLUDED by humans
   - Target: 0% (conservative approach)

4. **MAYBE rate**
   - Percentage requiring human review
   - Current system: ~22%
   - With program tags: potentially lower

5. **Program tag agreement**
   - Papers with included programs should → INCLUDE
   - Papers with excluded programs should → EXCLUDE
   - Track mismatches for edge cases

---

## 📝 Next Steps

1. ✅ **Parse RIS files** - Create parser for DEP classifier output
2. ✅ **Create validation script** - Test pipeline on human-screened papers
3. ✅ **Integrate program tags** - Add confidence boosting for tagged papers
4. ✅ **Batch processing** - Set up for screening 12,393 "Not excluded" corpus
5. ✅ **Results analysis** - Compare LLM vs human decisions, analyze patterns
6. ✅ **Human review workflow** - Set up system for reviewing MAYBE cases

---

**For Questions or Issues**: Check `scripts/data_analysis/analyze_data.py` for data exploration code.

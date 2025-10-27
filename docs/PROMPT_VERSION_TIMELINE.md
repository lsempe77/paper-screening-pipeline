# Prompt Version Timeline - s14 False Positive Analysis

## Key Finding: Both analyses used DIFFERENT prompt versions!

### Timeline of Events

**October 24, 2025 - 20:27:08**
- `s14_comprehensive_results.csv` created
- Ran ALL 200 papers from s14above.xlsx
- Used `structured_screening_with_program_filter.txt` (older version)
- Found 8 false positives

**October 24, 2025 - 20:49:45**
- `comprehensive_s14_analysis.py` last modified
- Script uses `use_program_filter=True`

**October 24, 2025 - 21:10:12**  ⬅️ **PROMPT UPDATED**
- `structured_screening_with_program_filter.txt` modified
- Recent updates applied:
  - Expanded outcomes criterion
  - Missing abstract handling
  - Python-based year assessment
  - **BUT: No microcredit fix yet!**

**October 24, 2025 - 21:18:31**
- `analyze_s14_false_positives.py` created
- Ran random sample of 10 papers
- Used UPDATED prompt (21:10:12 version)
- Found 2 false positives (121323669, 121337599)

---

## Analysis

### Papers appearing in BOTH analyses:
- **121323669**: PRSP microcredit appraisal (2004)
- **121337599**: Nigeria critique paper

### Why they appear in both?

**Answer**: Because **neither prompt version** had the microcredit fix!

- **Comprehensive analysis (20:27)**: Used pre-21:10 prompt
  - No microcredit fix
  - Classified loans as "cash support" ❌

- **Random sample analysis (21:18)**: Used post-21:10 prompt
  - Still no microcredit fix (wasn't added yet)
  - Still classified loans as "cash support" ❌

### Conclusion

Both 121323669 and 121337599 appear as false positives in both analyses **because microcredit/loans confusion exists in BOTH prompt versions**. The recent updates (outcomes, missing abstract, Python year) did NOT address the fundamental issue:

**The prompt does not explicitly exclude loans/credit from "cash support"**

---

## All 8 False Positives from Comprehensive Analysis

### Legitimate INCLUDES (humans wrong):
1. **121296063**: Malawi SCTP - actual cash transfers + assets ✅
2. **121299285**: Pakistan BISP - actual unconditional cash transfers ✅

### Should be EXCLUDED (LLM wrong):

#### Microfinance only (5 papers):
3. **121323669**: PRSP microcredit - "borrow from PRSP", "loaning procedure" ❌
4. **121323321**: PRSP microcredit duplicate (2005) ❌
5. **121308119**: Egyptian SFD - "supporting microcredit" ❌
6. **121295210**: Egyptian SFD duplicate ❌
7. **121304324**: Fadama - "provide loan facilities" ❌

#### Review paper (1 paper):
8. **121295197**: CCT Latin America - "analyze and synthesize evidence from case studies" ❌

---

## Next Steps

### Priority 1: Fix Cash Support Criterion
Add explicit exclusions to prompt:

```
COMPONENT 1: Cash Support
✅ YES: Cash transfers, cash grants, cash payments, direct income support
❌ NO: Microcredit, loans, borrowing, lending, credit access, microfinance, debt

IMPORTANT: Financial support through DEBT (loans/credit) is NOT cash support!

Examples:
- "unconditional cash transfer" → YES ✅
- "conditional cash transfer (CCT)" → YES ✅
- "PRSP micro-credit programme" → NO ❌
- "provide loan facilities" → NO ❌
- "supporting microcredit" → NO ❌
```

### Priority 2: Fix Study Type Filter
Add review paper exclusion:

```
Study Type Pre-Filter:
- "analyze and synthesize evidence" → EXCLUDE (review/synthesis)
- "systematic review" → EXCLUDE
- "meta-analysis" → EXCLUDE
```

### Priority 3: Re-test on 8 False Positives
Expected results after fix:
- Papers 1-2 (SCTP, BISP): Remain INCLUDE ✅ (correct)
- Papers 3-7 (microfinance): Become EXCLUDE ✅ (correct)
- Paper 8 (review): Become EXCLUDE ✅ (correct)

Success rate: 8/8 correct = 100%

### Priority 4: Correct Human Labels
Papers that need human label correction:
- 121296063 (Malawi SCTP): "Excluded by TA" → "Included (TA)"
- 121299285 (Pakistan BISP): "Excluded by TA" → "Included (TA)"

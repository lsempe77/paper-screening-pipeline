# Potential Fixes for False Positives

## Problem Identified
The program filter (Rule 0a) is too permissive and causes false positives.

**Current Logic:**
```
IF program_recognition == YES:
    → INCLUDE (bypass all other criteria)
```

## Root Causes

### 1. Microfinance vs Graduation Programs
- **Issue:** LLM marks microcredit/loans as "cash support" 
- **Example:** Paper 121323669 - PRSP microcredit marked YES for cash support
- **Reality:** Loans ≠ Cash transfers/grants

### 2. Policy Critiques vs Impact Evaluations
- **Issue:** Papers that analyze/critique programs get included
- **Example:** Paper 121337599 - "A Critique of..." Nigeria's plan
- **Reality:** Critique/analysis ≠ Impact evaluation

### 3. Program Description vs Program Evaluation
- **Issue:** Papers mentioning programs but not evaluating them
- **Reality:** Need to distinguish evaluation from description

## Potential Solutions

### Option 1: Remove Rule 0a Entirely
**Change:** Remove program filter bypass, evaluate all criteria for every paper

**Pros:**
- Most conservative approach
- Zero false positives from program filter
- Forces proper cash+assets verification

**Cons:**
- May increase MAYBE rate
- Loses efficiency of quick program recognition

**Implementation:**
- Remove Rule 0a from decision_processor.py
- Keep program_recognition as criterion but don't bypass on YES
- Apply standard decision rules (Rule 1, 2, 3) to all papers

### Option 2: Strengthen Program Filter
**Change:** Add secondary checks before applying Rule 0a

**Additional checks:**
1. "Is this an IMPACT EVALUATION (not critique/analysis/description)?"
2. "Does the abstract mention the program IMPLEMENTING cash transfers (not loans)?"
3. "Does the abstract mention PROVIDING productive assets?"
4. "Are keywords like 'critique', 'analysis', 'review' in title?"

**Pros:**
- Keeps efficiency of program filter
- Catches edge cases

**Cons:**
- More complex logic
- Still relies on LLM interpretation

**Implementation:**
- Add to program_recognition criterion in prompt
- Require ALL three conditions: (1) Program in list, (2) Impact evaluation, (3) Cash+assets mentioned

### Option 3: Fix Cash Criterion Definition
**Change:** Strengthen cash support criterion to explicitly exclude loans/credit

**Add to prompt:**
```
CRITICAL DISTINCTIONS:
- ✅ YES: Cash transfers, grants, stipends, consumption support
- ❌ NO: Microcredit, loans, borrowing, lending, credit access
- Remember: DEBT IS NOT CASH SUPPORT
```

**Add examples:**
```
Example: "PRSP micro-credit programme" → NO (loans, not transfers)
Example: "access to credit" → NO (borrowing, not grants)
Example: "cash transfer programme" → YES (direct transfers)
```

**Pros:**
- Fixes cash misclassification
- Catches microfinance studies
- Paper 121323669 would get NO for cash → EXCLUDE via Rule 1

**Cons:**
- Doesn't fix policy critique issue
- Doesn't fix study type issue

**Implementation:**
- Update cash support criterion in prompt
- Add examples and negative cases
- Emphasize loans ≠ transfers

### Option 4: Add Study Type Pre-Filter
**Change:** Add initial classification before criteria assessment

**New first step:**
```
STEP 0: Study Type Classification
Is this paper:
A) Impact evaluation of a specific program intervention
B) Policy analysis/critique/review
C) Program description/implementation study
D) Theoretical/conceptual paper

ONLY proceed with criteria assessment if (A)
If (B), (C), or (D) → EXCLUDE
```

**Pros:**
- Catches policy critiques (Paper 121337599)
- Catches descriptive studies
- Clear separation of study types

**Cons:**
- Adds complexity
- Another LLM judgment call

## Recommended Approach

**Combination of Options 3 + 4:**

1. **Add study type check** before program filter
2. **Strengthen cash criterion** to exclude loans/credit
3. **Keep Rule 0a** but only apply if:
   - Study type = Impact evaluation
   - Program in list
   - Cash support ≠ loans (verified in criterion)

This gives defense in depth without removing the efficiency of program recognition.

## Testing Plan

1. Re-run on 8 false positive papers
2. Verify all 8 now correctly EXCLUDED
3. Re-run on 200 s14above papers
4. Check false positive rate drops to 0%
5. Monitor MAYBE rate (should not increase significantly)

## Files to Modify

- `prompts/structured_screening_with_program_filter.txt`
  - Add study type classification section
  - Strengthen cash support criterion with examples
  - Add negative examples (loans, credit)
  
- `decision_processor.py` (if changing Rule 0a logic)
  - Potentially add study type check
  - Keep or modify program filter bypass

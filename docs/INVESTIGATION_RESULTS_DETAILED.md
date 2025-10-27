# Investigation Results: 5 False Positives + 1 False Negative

**Date:** October 24, 2025  
**Method:** Full abstract review + detailed LLM reasoning analysis

---

## FALSE POSITIVES (LLM=INCLUDE, Human=Excluded)

### 1. ✅ **121296063 - Malawi SCTP** - LLM IS CORRECT, HUMANS WRONG

**Decision:** INCLUDE (via Rule 0a: Program Recognition YES)

**Abstract Summary (8906 chars):**
- **Program:** Malawi Social Cash Transfer Programme (SCTP) - Endline Impact Report
- **Components:** 
  - ✅ Unconditional social cash transfers (bimonthly payments)
  - ✅ Productive assets - "noticeable impacts on ownership of both agricultural and non-agricultural assets"
  - Quote: "agricultural asset expenditure", "livestock based wealth", "hand hoes"
- **Study Design:** Randomized Controlled Trial (RCT)
  - Treatment: 1,678 households from 14 VCs
  - Control: 1,853 households from 15 VCs
  - Baseline, Midline, Endline data collection
- **Outcomes Measured:** Consumption, food security, assets, income, child health, schooling, well-being
- **Results:** 23% increase in consumption, strong food security improvements, asset accumulation

**LLM Assessment:**
- Program Recognition: YES ✅
- Cash Support: YES ✅
- Productive Assets: YES ✅
- Study Design: YES (RCT) ✅
- All other criteria: YES ✅

**VERDICT: This is a LEGITIMATE INCLUDE. Humans made an error.**
- This is exactly the type of program we're looking for
- Cash + assets + RCT evaluation of ultra-poor program
- Should be changed from "Excluded" to "Included (TA)"

---

### 2. ✅ **121299285 - Pakistan BISP** - LLM IS CORRECT, HUMANS WRONG

**Decision:** INCLUDE (via Rule 0a: Program Recognition YES)

**Abstract Summary (1999 chars):**
- **Program:** BISP (Benazir Income Support Programme) - Pakistan's unconditional cash transfer program
- **Components:**
  - ✅ Unconditional cash transfers
  - ❌ NO productive assets mentioned
- **Study Design:** Quasi-experimental Difference-in-Differences
  - Used 3 rounds of BISP impact assessment survey (2011, 2016, 2019)
  - Used Principal Component Analysis + DiD design
- **Outcomes Measured:** Socioeconomic status, household well-being
- **Results:** Limited impact on well-being (attributed to inflation, unemployment, payment challenges)

**LLM Assessment:**
- Program Recognition: YES ✅ (BISP is known program)
- Cash Support: YES ✅
- Productive Assets: NO ❌
- Study Design: YES (quasi-experimental) ✅
- All other criteria: YES ✅

**VERDICT: This is DEBATABLE but likely INCLUDE.**
- BISP is a major unconditional cash transfer program
- Quasi-experimental impact evaluation
- **Issue:** No productive assets component
- **However:** The prompt recognizes BISP as a "known relevant program" which triggers auto-INCLUDE via Rule 0a
- **Question for user:** Should pure cash transfer programs without assets be included? If NO, need to move BISP to irrelevant programs list

---

### 3. ⚠️ **121310791 - Gaza CCT** - PROCESSING ERROR, NEEDS RE-RUN

**Decision:** MAYBE (due to processing error)

**Abstract Summary (1323 chars):**
- **Program:** Palestinian National Cash Transfer Programme (Gaza)
- **Components:**
  - ✅ Quarterly cash payments to extremely poor households
  - ❌ NO productive assets mentioned
- **Study Type:** Appears to be mixed methods research (2013)
- **Focus:** Child protection, psychosocial wellbeing, caregiver resources
- **Outcomes:** Education, health access, child protection from exploitation/abuse/neglect

**LLM Assessment:**
- **ERROR:** "Missing criteria" processing failure
- All criteria marked as UNCLEAR due to error

**VERDICT: INCONCLUSIVE - NEEDS RE-SCREENING**
- LLM failed to parse response properly (JSON error)
- Cannot assess until re-run succeeds
- Based on abstract:
  - ✅ Cash transfers (quarterly payments)
  - ❌ No productive assets
  - ⚠️ Study design unclear - "mixed methods primary research" but no mention of control group or impact evaluation design
  - This looks more like an exploratory/descriptive study than quantitative impact evaluation

---

### 4. ❌ **121295197 - CCT Latin America Review** - LLM IS WRONG, HUMANS CORRECT

**Decision:** EXCLUDE (via Rule 1: Productive Assets = NO)

**Abstract Summary (849 chars):**
- **Type:** SYNTHESIS/REVIEW PAPER - "analyze and synthesize evidence from case studies"
- **Programs Covered:** CCTs in Brazil, Honduras, Mexico, Nicaragua
- **Components:** Cash grants conditional on education/health/nutrition participation
- **Content:** Analyzes trends, costs, impacts, social relations from multiple case studies
- **Quote:** "contributors analyze and synthesize evidence from case studies"

**LLM Assessment:**
- Program Recognition: UNCLEAR ❌ (should be NO - this is a review)
- Cash Support: YES
- Productive Assets: NO ✅ (correct)
- Study Design: UNCLEAR (should be NO - it's a synthesis, not original evaluation)

**VERDICT: This is a FALSE POSITIVE. Should be EXCLUDED.**
- **This is a REVIEW/SYNTHESIS paper, NOT an original impact evaluation**
- It synthesizes evidence FROM case studies, it's not conducting original research
- Study design criterion should catch this but marked as UNCLEAR
- **Action needed:** Strengthen study design criterion to detect review papers

**Why LLM missed it:**
- Program Recognition didn't flag as review (marked UNCLEAR instead of NO)
- Study Design didn't catch synthesis nature (marked UNCLEAR)
- Excluded only because Productive Assets = NO (lucky catch, not intentional)

---

### 5. ⚠️ **121328933 - Ghana LEAP** - UNCLEAR, LIKELY SHOULD BE EXCLUDED

**Decision:** INCLUDE (via Rule 0a: Program Recognition YES for LEAP)

**Abstract Summary (880 chars):**
- **Program:** Compares TWO programs:
  1. LEAP (Livelihood Empowerment Against Poverty) - cash transfers
  2. Rural Enterprise Program - skills/technology transfer
- **Argument:** Paper argues "look beyond cash transfers" to "skills and technology transfer"
- **Focus:** Comparative study of two poverty reduction policies
- **Emphasis:** Skills/technology transfer > cash transfers alone

**LLM Assessment:**
- Program Recognition: YES (LEAP is in known relevant programs list) ✅
- Cash Support: YES (LEAP includes cash transfers) ✅
- Productive Assets: UNCLEAR ❌
- Study Design: UNCLEAR ❌

**VERDICT: AMBIGUOUS - LIKELY SHOULD BE EXCLUDED**

**Issues:**
1. **Comparative study** - focuses on LEAP vs Rural Enterprise Program
2. **Main argument:** Skills/technology transfer > cash transfers
3. **Study design UNCLEAR** - no mention of impact evaluation methods
4. **Productive assets UNCLEAR** - doesn't specify if LEAP includes assets
5. Title says "Looking BEYOND Cash Transfers" - suggests cash alone is insufficient

**Analysis:**
- If this is just a descriptive comparison without quantitative impact evaluation → EXCLUDE
- If LEAP doesn't include productive assets in this study → EXCLUDE (pure cash only)
- If it's arguing against cash transfers in favor of skills → questionable fit

**Action needed:** Manually review abstract more carefully or check full paper to determine:
- Does it use quantitative impact evaluation methods?
- Does it evaluate LEAP's cash+asset components or just cash?
- Is this original research or policy commentary?

---

## FALSE NEGATIVE (LLM=EXCLUDE, Human=Included)

### 6. ❓ **121354173 - Ethiopia Livelihood** - UNCLEAR WHY HUMANS INCLUDED

**Decision:** EXCLUDE (via Rule 1: Cash Support = NO)

**Abstract Summary (2448 chars):**
- **Study Type:** Generic livelihood diversification study (NOT a specific program)
- **Location:** Jimma zone, Oromia, Southwest Ethiopia
- **Focus:** Impact of livelihood diversification on household poverty
- **Methods:** 
  - Cross-sectional survey (385 households)
  - Propensity Score Matching (PSM) to compare diversified vs non-diversified households
- **Components:**
  - ❌ NO cash transfers mentioned
  - ✅ Livestock ownership as factor
  - ❌ NO specific economic inclusion program identified
- **Findings:** Households with diversified livelihoods 9% better off in poverty terms

**LLM Assessment:**
- Program Recognition: UNCLEAR ✅ (correct - no specific program)
- Cash Support: NO ✅ (correct - "does not mention any cash transfers, focuses on livelihood diversification and access to credit")
- Productive Assets: YES (livestock ownership mentioned)
- Study Design: YES (PSM - quasi-experimental)
- **Decision:** EXCLUDE because Cash Support = NO

**VERDICT: LLM IS CORRECT. UNCLEAR WHY HUMANS INCLUDED THIS.**

**Analysis:**
- This is **NOT** an evaluation of a specific economic inclusion program
- It's a **generic study** comparing households that diversified livelihoods vs those that didn't
- No cash transfer component
- No specific program intervention
- Just observational study of livelihood diversification strategies

**Questions for humans:**
- Did humans identify a specific program we're missing?
- Is there a Ethiopia government program on livelihood diversification?
- Was this included by mistake in the validation set?

**Most likely:** Human inclusion error - this doesn't fit our criteria

---

## SUMMARY AND RECOMMENDATIONS

### True Status Breakdown:

**False Positives (LLM=INCLUDE, should be EXCLUDE):**
1. ❌ **121295197** - CCT Latin America Review (synthesis paper)
2. ⚠️ **121328933** - Ghana LEAP (unclear study design, comparative study)
3. ⚠️ **121310791** - Gaza CCT (needs re-run, likely no assets + unclear design)

**Actually Correct (LLM=INCLUDE, should be INCLUDE):**
4. ✅ **121296063** - Malawi SCTP (humans wrong)
5. ✅ **121299285** - Pakistan BISP (humans wrong - unless pure cash programs excluded)

**False Negative Status:**
6. ✅ **121354173** - Ethiopia Livelihood (LLM correct, humans wrong)

---

### Action Items:

#### 1. URGENT: Strengthen Review Paper Detection
**Problem:** 121295197 is a synthesis paper but only excluded due to NO assets (luck, not design)

**Fix:** Add to Program Recognition or Study Design:
```
Study Type Pre-Filter:
- "analyze and synthesize evidence" → EXCLUDE (review)
- "systematic review" → EXCLUDE
- "meta-analysis" → EXCLUDE  
- "contributors analyze" → EXCLUDE (edited volume)
```

#### 2. Correct Human Labels (3 papers):
- **121296063** (Malawi SCTP): Change from "Excluded" to "Included (TA)"
- **121299285** (Pakistan BISP): Change from "Excluded" to "Included (TA)" [IF pure cash programs are acceptable]
- **121354173** (Ethiopia): Change from "Included (TA)" to "Excluded"

#### 3. Decide Policy on Pure Cash Transfer Programs:
**Question:** Should programs with ONLY cash transfers (no assets) be included?
- **Current prompt:** Lists some pure cash programs (BISP) as "relevant"
- **User decision needed:** 
  - If YES → Keep BISP in relevant list
  - If NO → Move BISP to irrelevant list, clarify that cash+assets required

#### 4. Manual Review Required:
- **121310791** (Gaza CCT): Re-screen after fixing JSON error, check study design
- **121328933** (Ghana LEAP): Check full paper - is it quantitative impact evaluation?

#### 5. Update Relevant Programs List Guidance:
Current issue: LLM auto-includes any paper mentioning programs from relevant list
**Add guideline:** "Program must be EVALUATED in the paper, not just MENTIONED or COMPARED"

---

## Revised False Positive Count:

**Original claim:** 5 false positives  
**After investigation:**
- **Definite FPs:** 1 (CCT Review)
- **Likely FPs:** 2 (Ghana LEAP, Gaza CCT)
- **Actually correct:** 2 (Malawi SCTP, Pakistan BISP)

**If all corrections applied:** 1-3 false positives remaining (vs 8 before fix!)
**False positive rate:** 0.5-1.6% (down from 4.2%)
**Improvement:** 62-88% reduction in false positive rate! 🎉

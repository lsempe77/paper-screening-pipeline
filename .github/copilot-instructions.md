---
applyTo: "**/*.py"
---

# Paper Screening Pipeline - Copilot Instructions

- Always organise files in correct folders according to their purpose (e.g., prompts, config, src/models, etc.)


## 🎯 Project Overview
This is an **LLM-powered systematic review screening pipeline** using a **hybrid architecture**:
- **LLM Component**: Assesses research papers against 7 inclusion criteria
- **Python Logic**: Makes deterministic final decisions based on criteria assessments
- **Two-Pass System**: Follow-up agent resolves uncertain cases to reduce human workload

## 🏗️ Architecture Principles

### 1. **Hybrid LLM + Traditional Logic Pattern**
When creating features that involve LLM decisions:
```python
# ✅ CORRECT: Separation of concerns
llm_response = get_llm_assessment()  # LLM does what it's good at
final_decision = apply_deterministic_logic(llm_response)  # Python does what it's good at

# ❌ AVOID: Letting LLM make final decisions directly
final_decision = llm.decide_everything()  # Not explainable, not deterministic
```

### 2. **Structured Output with JSON Schema**
Always enforce structured JSON responses from LLMs:
```python
# Define clear schema in prompts
schema = {
    "criteria_evaluation": {
        "criterion_name": {
            "assessment": "YES/NO/UNCLEAR",  # Constrained values
            "reasoning": "explicit evidence"
        }
    }
}
```

## 📝 Code Style Standards

### General Python Standards
- Follow **PEP 8** style guide strictly
- Use **type hints** for all function parameters and returns
- Write **docstrings** for all classes and public methods
- Use **dataclasses** for data structures (see `src/models/__init__.py`)
- Prefer **enums** over string constants for categorical values

### Naming Conventions
```python
# Classes: PascalCase
class IntegratedStructuredScreener:
    pass

# Functions/methods: snake_case with descriptive names
def screen_paper(self, paper: Paper) -> StructuredScreeningResult:
    pass

# Constants: UPPER_SNAKE_CASE
CRITERION_LABELS = {...}

# Private methods: prefix with underscore
def _load_criteria_only_prompt(self) -> str:
    pass
```

### Error Handling Pattern
Always handle LLM and API failures gracefully:
```python
try:
    llm_response = call_llm_api()
    result = process_response(llm_response)
except json.JSONDecodeError as e:
    return _create_error_result(f"JSON parsing failed: {e}")
except Exception as e:
    return _create_error_result(f"Processing error: {e}")
```

## 🔧 Component-Specific Guidelines

### Working with LLM APIs (`integrated_screener.py`)
1. **Use OpenAI-compatible client** via OpenRouter
2. **Set low temperature** (0.1) for consistency
3. **Implement retry logic** with exponential backoff
4. **Track processing time** for performance monitoring
5. **Store raw responses** for audit trails

Example:
```python
response = self.client.chat.completions.create(
    model=self.model_config.model_name,
    messages=[
        {"role": "system", "content": "Expert role description"},
        {"role": "user", "content": formatted_prompt}
    ],
    temperature=0.1,  # Low for consistency
    max_tokens=1500
)
```

### Decision Processing (`decision_processor.py`)
1. **Keep logic deterministic and explainable**
2. **Return detailed reasoning** for every decision
3. **Document which rule was applied**
4. **Count assessments** (YES/NO/UNCLEAR) for metrics
5. **Create error results** rather than raising exceptions

Example:
```python
def _apply_decision_logic(self, criteria_assessments, counts):
    # Rule 1: ANY NO → EXCLUDE
    if counts['NO'] > 0:
        return FinalDecision.EXCLUDE, "reason", "Rule 1: ANY NO → EXCLUDE"
    
    # Rule 2: ALL YES → INCLUDE
    if counts['YES'] == 7:
        return FinalDecision.INCLUDE, "reason", "Rule 2: ALL YES → INCLUDE"
    
    # Rule 3: Some UNCLEAR → MAYBE
    return FinalDecision.MAYBE, "reason", "Rule 3: 0 NO + some UNCLEAR → MAYBE"
```

### Prompt Engineering (`prompts/` directory)
1. **Start with clear role definition** for the LLM
2. **Provide explicit assessment guidelines** (YES/NO/UNCLEAR criteria)
3. **Include concrete examples** for edge cases
4. **Specify JSON schema** exactly
5. **Add inference rules** for common ambiguous cases
6. **Use markdown formatting** for readability

Structure:
```
1. Role definition
2. Task description
3. JSON format requirements
4. Criteria with assessment guides
5. Examples for each criterion
6. Inference guidelines
7. Output schema
```

### Configuration Management (`config/config.yaml`)
1. **Separate API keys** from code
2. **Support multiple model tiers** (fast/accurate/premium)
3. **Include retry and timeout settings**
4. **Document all configuration options**
5. **Provide example config** without secrets

## 🧪 Testing & Validation

### Test Structure
Create test scripts in `archive/testing/` with clear naming:
- `test_<component>_<specific_feature>.py`
- Include expected outcomes in docstrings
- Use real paper examples for integration tests

### Validation Approach
1. **Validate on labeled dataset** (papers with known outcomes)
2. **Track false positive/negative rates**
3. **Monitor MAYBE rate** (target: <25%)
4. **Measure processing time** per paper
5. **Test JSON parsing robustness**

## 📊 Data Models

### Use Dataclasses for Structured Data
```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List

@dataclass
class Paper:
    """Represents a research paper with metadata."""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    year: Optional[int] = None
    # ... more fields
    
    def __post_init__(self):
        """Initialize computed fields."""
        if not self.paper_id:
            self.paper_id = f"{self.year}_{hash(self.title) % 10000:04d}"

class ScreeningDecision(Enum):
    """Enumeration of possible decisions."""
    INCLUDE = "include"
    EXCLUDE = "exclude"
    MAYBE = "maybe"
```

### Result Objects
Always include:
- Final decision with reasoning
- Individual criterion assessments
- Processing metadata (time, model used)
- Raw LLM response (for debugging)
- Logic rule applied (for explainability)

## 🚀 Production Considerations

### Performance Optimization
1. **Use cheaper models** for initial screening (Haiku)
2. **Reserve expensive models** for uncertain cases (Sonnet/Opus)
3. **Batch process** papers efficiently
4. **Add delays** between API calls to respect rate limits
5. **Cache results** to avoid reprocessing

### Error Recovery
1. **Log all errors** with context
2. **Continue processing** other papers on individual failures
3. **Save partial results** regularly
4. **Provide fallback prompts** if files missing
5. **Validate JSON** before processing

### Monitoring & Logging
```python
# Track key metrics
metrics = {
    'total_papers': len(papers),
    'include_count': sum(1 for r in results if r.decision == INCLUDE),
    'exclude_count': sum(1 for r in results if r.decision == EXCLUDE),
    'maybe_count': sum(1 for r in results if r.decision == MAYBE),
    'average_processing_time': mean([r.processing_time for r in results])
}
```

## 🔄 Follow-Up Agent Pattern

When implementing iterative refinement:
```python
# 1. Check if follow-up needed
if use_followup_agent and result.decision == MAYBE:
    # 2. Identify unresolved criteria
    unclear_criteria = [k for k, v in assessments.items() if v == "UNCLEAR"]
    
    # 3. Create focused prompt with context
    followup_prompt = format_followup(
        paper_info=paper_info,
        initial_assessment=initial_json,
        unclear_targets=unclear_criteria
    )
    
    # 4. Get refined assessment
    followup_response = call_llm(followup_prompt)
    
    # 5. Merge results and track changes
    combined_result = merge_assessments(initial, followup)
    combined_result.raw_response = json.dumps({
        "first_pass": initial_raw,
        "followup_pass": followup_raw
    })
```

## 📁 File Organization

### Project Structure
```
project_root/
├── integrated_screener.py      # Main screening engine
├── decision_processor.py       # Deterministic logic
├── run_screening.py           # CLI entry point
├── config/                    # Configuration files
├── prompts/                   # LLM prompt templates
├── src/
│   ├── models/               # Data models
│   ├── parsers/              # File parsers
│   └── utils/                # Utility functions
├── data/
│   ├── input/                # Input papers
│   ├── output/               # Results
│   └── processed/            # Intermediate data
├── logs/                     # Application logs
└── archive/                  # Development history
    ├── analysis/
    ├── testing/
    └── validation/
```

### Archive Strategy
Keep development history but separate from production:
- Move old scripts to `archive/`
- Organize by purpose (analysis, testing, validation, development)
- Keep one clear production path in root

## 🎯 When Creating New Features

### Checklist for LLM-Based Features
- [ ] Define clear JSON schema for LLM output
- [ ] Create structured prompt with examples
- [ ] Implement robust JSON parsing with error handling
- [ ] Add deterministic decision logic (don't rely only on LLM)
- [ ] Include processing time tracking
- [ ] Store raw responses for debugging
- [ ] Add unit tests with expected outcomes
- [ ] Validate on real data
- [ ] Document in README with examples
- [ ] Consider two-pass pattern for uncertain cases

### Checklist for Screening Logic
- [ ] Keep rules simple and explainable
- [ ] Prefer conservative decisions (MAYBE over wrong answer)
- [ ] Return detailed reasoning strings
- [ ] Document which rule was applied
- [ ] Count assessment types for metrics
- [ ] Handle missing/invalid data gracefully

## 💡 Best Practices from This Project

### What Works Well
1. **Hybrid approach**: LLM for assessment, Python for decisions
2. **Structured JSON**: Forces consistent output format
3. **Two-pass system**: Reduces uncertainty without more training data
4. **Conservative logic**: Zero false positives/negatives
5. **Prompt optimization**: 20% reduction in MAYBE rate through better prompts
6. **Dataclasses + Enums**: Type-safe, clear data models

### What to Avoid
1. ❌ Letting LLM make final inclusion decisions directly
2. ❌ Unstructured text responses (hard to parse reliably)
3. ❌ Complex multi-step reasoning in single prompt
4. ❌ Assuming LLM responses will always be valid
5. ❌ Mixing assessment criteria (evaluate independently)

## 📚 Key Files Reference

- **`integrated_screener.py`**: Main screening class with LLM integration
- **`decision_processor.py`**: Deterministic decision rules (3 simple rules)
- **`run_screening.py`**: Production CLI for batch processing
- **`prompts/structured_screening_criteria_optimized.txt`**: Primary prompt (22% MAYBE rate)
- **`prompts/structured_screening_followup.txt`**: Follow-up prompt for uncertain cases
- **`config/config.yaml`**: API keys, model selection, parameters
- **`src/models/__init__.py`**: Data models (Paper, Result, Enums)

## 🔍 Debugging Tips

1. **Enable verbose logging**: Set `logging.basicConfig(level=logging.DEBUG)`
2. **Check raw responses**: Always stored in `result.raw_response`
3. **Validate JSON manually**: Print LLM response before parsing
4. **Test single paper**: Use `screener.screen_paper(test_paper, debug=True)`
5. **Check prompt loading**: Verify optimized prompt file exists and loads
6. **Monitor API errors**: Log all OpenRouter API responses

## 📊 **CRITICAL: Document All Analytical Processes**

### Why Documentation Matters
This pipeline makes **critical decisions** about research inclusion/exclusion. All analytical processes, investigations, and decisions must be thoroughly documented for:
- **Reproducibility**: Others can understand and replicate your decisions
- **Audit trail**: Track why validation labels were changed
- **Quality assurance**: Identify patterns in errors or improvements
- **Knowledge transfer**: Preserve institutional knowledge

### 🚨 **IMPORTANT: Use Existing Documentation Files**

**DO NOT create new documentation files** without checking if a relevant file already exists. **ALWAYS update existing files** rather than creating duplicates.

#### Existing Documentation Structure

```
docs/
├── VALIDATION_LABEL_CORRECTIONS.md   # ALL validation label corrections (consolidated)
├── CORRECTION_SUMMARY.md             # High-level summary of all corrections
├── DATA_INVENTORY.md                 # Data structure documentation
├── QUICK_SUMMARY.md                  # Quick reference
└── PRODUCTION_DEPLOYMENT_COMPLETE.md # Deployment guide
```

#### When to Update Which File

1. **Label Corrections:**
   - **Primary:** `VALIDATION_LABEL_CORRECTIONS.md` (add to appropriate section by validation set)
   - **Summary:** `CORRECTION_SUMMARY.md` (update totals and audit trail)
   - **Detailed analysis:** Add to VALIDATION_LABEL_CORRECTIONS.md with full abstracts if needed

2. **Prompt Changes:**
   - Update `CORRECTION_SUMMARY.md` in "Prompt Improvements" section
   - Document in relevant correction file if prompt change drove corrections

3. **Validation Results:**
   - Update `CORRECTION_SUMMARY.md` in "Impact" section
   - Update specific validation file if extensive analysis needed

4. **Production Changes:**
   - Update `PRODUCTION_DEPLOYMENT_COMPLETE.md`

#### ✅ Correct Approach
```python
# When adding new corrections:
# 1. Check existing files first
# 2. Add to VALIDATION_LABEL_CORRECTIONS.md under appropriate validation set
# 3. Update CORRECTION_SUMMARY.md totals and audit trail
# 4. Only create new detailed file if needed for extensive analysis
```

#### ❌ Avoid
```python
# DON'T create new files like:
# - docs/s3_corrections.md (use VALIDATION_LABEL_CORRECTIONS.md)
# - docs/s14_corrections.md (use VALIDATION_LABEL_CORRECTIONS.md)
# - docs/new_validation_summary.md (use CORRECTION_SUMMARY.md)
# - docs/prompt_changes_oct24.md (update CORRECTION_SUMMARY.md)
```

### Documentation Requirements

#### 1. **Investigation Scripts**
When investigating issues (false positives/negatives, high MAYBE rates, etc.):
```python
# ✅ GOOD: Create investigation scripts in scripts/validation/
# Example: investigate_false_negatives.py
"""
Investigation: Why are papers X and Y marked as false negatives?
Date: YYYY-MM-DD
Context: Testing program filter prompt on 20 validation papers
"""
```

#### 2. **Markdown Documentation**
For each significant analysis or decision:
- **Create in `docs/` folder** with descriptive name
- **Include date and context**
- **Document the problem, analysis, and conclusion**
- **Show evidence (abstracts, criteria assessments, reasoning)**

Example structure:
```markdown
# [Issue Name] - Analysis and Resolution

**Date:** YYYY-MM-DD
**Context:** What prompted this investigation
**Outcome:** What was decided/changed

## Problem Description
[What was the issue?]

## Analysis Process
[Step-by-step investigation]

## Evidence
[Abstracts, data, LLM assessments]

## Conclusion
[What was decided and why]

## Actions Taken
[Changes made to code/data/prompts]

## Audit Trail
[Table of file changes with dates]
```

#### 3. **Validation Label Changes**
**CRITICAL**: When correcting validation labels:
1. ✅ **Create backup** before any changes
2. ✅ **Document reason** for each correction with evidence
3. ✅ **Create audit trail** with date, ID, old label, new label, rationale
4. ✅ **Save scripts** that made the changes (reproducibility)
5. ✅ **Cross-reference** with analysis documents

Example: `docs/VALIDATION_LABEL_CORRECTIONS.md`

#### 4. **Prompt Changes**
When modifying prompts:
1. Document what changed and why
2. Show before/after MAYBE rates
3. Include test results on validation set
4. Archive old prompts in `archive/prompts/`

#### 5. **Decision Logic Changes**
When updating `decision_processor.py`:
1. Document the rule change with examples
2. Show impact on test set accuracy
3. Explain edge cases handled
4. Update inline comments

### Required Files for Major Changes

For any significant change (prompt optimization, logic updates, label corrections):

1. **`docs/[CHANGE_NAME].md`** - Comprehensive analysis document
2. **`scripts/validation/investigate_*.py`** - Investigation scripts
3. **`scripts/validation/correct_*.py`** - Correction scripts (if applicable)
4. **Backup files** - With timestamps in filename
5. **Test results** - Before/after comparisons

### Audit Trail Template

Maintain in documentation:
```markdown
## Audit Trail

| Date | Action | By | Files Modified | Rationale |
|------|--------|----|----|-----------|
| 2025-10-24 | Corrected labels | Script | s3above.xlsx | False negatives investigation |
```

### Examples in This Project

See these exemplary documentation practices:
- ✅ `docs/VALIDATION_LABEL_CORRECTIONS.md` - **CONSOLIDATED** label corrections (s3above + s14above, all 5 papers with full details)
- ✅ `docs/CORRECTION_SUMMARY.md` - High-level summary across all validation sets
- ✅ `scripts/validation/investigate_false_negatives.py` - Investigation script
- ✅ `scripts/validation/correct_labels.py` - s3above correction script (2 papers)
- ✅ `scripts/validation/correct_s14_labels.py` - s14above correction script (3 papers)
- ✅ Backups: `s3above_backup_20251024_193751.xlsx`, `s14above_backup_20251024_210147.xlsx`

**Note:** All corrections are documented in **one consolidated file** (`VALIDATION_LABEL_CORRECTIONS.md`) organized by validation set. This makes it easy to see all corrections in one place rather than scattered across multiple files.

### Checklist Before Making Changes

- [ ] Investigated issue thoroughly with scripts
- [ ] Retrieved and analyzed full evidence (abstracts, assessments)
- [ ] Documented analysis in `docs/` folder
- [ ] Created backup of files to be modified
- [ ] Created reproducible script for changes
- [ ] Documented in audit trail
- [ ] Tested changes on validation set
- [ ] Updated relevant README sections

---

Remember: **Explainability, robustness, and conservative decisions** are more important than maximizing automation. It's better to flag papers for human review than to make mistakes. **ALWAYS document your analytical process** - if it's not documented, it didn't happen.


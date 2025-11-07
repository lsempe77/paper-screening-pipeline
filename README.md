# 🤖 Paper Screening Pipeline

**Two Distinct AI-Powered Screening Systems for Systematic Reviews**

A production-ready repository containing **TWO SEPARATE screening pipelines**:
1. **Title & Abstract Screening** - Screens papers based on title and abstract only
2. **Full-Text Screening** - Screens complete research papers from TEI XML files

📝 **IMPORTANT:** See [`docs/PROMPT_TESTING_LOG.md`](docs/PROMPT_TESTING_LOG.md) for complete prompt testing history, results, and current status of all prompt iterations.

🚀 **LATEST STATUS:** See [`docs/CURRENT_PIPELINE_STATUS_NOV_6.md`](docs/CURRENT_PIPELINE_STATUS_NOV_6.md) for the current enhanced full-text screening system status, including citation system, enhanced Stage 1.5, and recent fixes.

---

## 🎯 Critical: Two Independent Pipelines

⚠️ **This repository contains TWO DIFFERENT screening systems. Make sure you're using the correct one!**

| Feature | Title & Abstract Pipeline | Full-Text Pipeline |
|---------|---------------------------|-------------------|
| **Input** | Excel file with titles/abstracts | TEI XML files with full paper text |
| **Main Script** | `integrated_screener.py` | `fulltext/dual_screener.py` |
| **CLI Entry** | `run_screening.py` or `screen_with_logging.py` | `fulltext/run_validation.py` |
| **Config File** | `config/config.yaml` | `config/config_fulltext.yaml` |
| **Prompt File** | `prompts/structured_screening_criteria_optimized.txt` | `prompts/fulltext_interpretation_stage2.txt` |
| **Status** | ✅ Production-ready | 🔄 Active development |
| **Validation** | 118 papers validated | 118 papers validation in progress |

📖 **For detailed architecture documentation**, see [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## 📊 Pipeline 1: Title & Abstract Screening

### **When to Use**
- You have paper titles and abstracts (e.g., from database exports)
- You want fast initial screening before obtaining full texts
- You have Excel/CSV files with bibliographic information

### **Performance**
- **Precision**: 93.3%
- **Recall**: 62.2%
- **F1 Score**: 74.7%
- **Processing**: ~5-10 seconds per paper
- **Status**: ✅ Validated and production-ready

### **Quick Start**

#### 1. **Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key
cp config/config.example.yaml config/config.yaml
# Edit config.yaml and add your OpenRouter API key
```

#### 2. **Run Screening**
```bash
# Test with small batch first (recommended)
python screen_with_logging.py --input data/input/papers.xlsx --limit 10

# Run full screening with logging
python screen_with_logging.py --input data/input/papers.xlsx --output data/output/title_abstract

# Batch processing with dual engines
python batch_dual_screening.py --input data/input/papers.txt --workers 4
```

#### 3. **Export Results**
```bash
# Export to CSV (compact format recommended)
python tools/export_csv_compact.py data/output/results.json

# Verify and mark duplicates
python tools/verify_and_mark_duplicates.py data/output/results_COMPACT.csv
```

### **Input File Format**
Excel file with columns:
- `title` - Paper title (required)
- `abstract` - Paper abstract (required)
- `authors` - Author list
- `year` - Publication year
- `doi` or `url` - Identifier

### **Key Files**
- **Main Engine**: `integrated_screener.py`
- **CLI**: `run_screening.py`, `screen_with_logging.py`
- **Config**: `config/config.yaml`
- **Prompt**: `prompts/structured_screening_criteria_optimized.txt`
- **Decision Logic**: `decision_processor.py`

---

## 📑 Pipeline 2: Full-Text Screening

### **When to Use**
- You have full-text papers in TEI XML format
- You need deeper analysis of intervention components
- You want detailed extraction of program information

### **Performance & Status (Enhanced System)**
- **Previous Validation**: 93.8% precision, 65.2% recall, 76.9% F1
- **Processing**: ~60 seconds per paper (enhanced dual-engine + citations)
- **Current Status**: ✅ **ENHANCED SYSTEM READY FOR FULL VALIDATION**
- **Major Enhancements**: Citation system, enhanced Stage 1.5, AttributeError fixes complete
- **Validation**: Enhanced system tested on 5 papers (0% MAYBE rate, all features working)

### **Architecture (Enhanced)**
Three-stage enhanced dual-engine system with citation tracking and program verification:
1. **Stage 1**: Information Extraction + Citation System - *Dual engines extract info + literal quotes*
2. **Stage 1.5**: Enhanced Program Verification - *SPECIFIC vs GENERIC classification + internet search*  
3. **Stage 2**: Evidence-Based Interpretation - *Dual engines assess criteria using citation evidence*

#### **🔗 NEW: Enhanced Citation System** 
- **Comprehensive literal quotes** extracted for ALL criteria (10+ citation fields)
- **Stage 2 uses citation evidence** in reasoning and assessments
- **Complete audit trail** for all decisions and classifications

#### **🎯 ENHANCED: Stage 1.5 Program Verification**
**Enhanced Classification Logic (100% Test Accuracy):**
- **SPECIFIC programs** ("BRAC TUP Program") → Verify exact program exists
- **GENERIC descriptions** ("Indonesian Social Protection Programs") → Search for graduation programs in country  
- **Eliminates false attribution** when Perplexity finds programs in country searches
- **Shared results** applied to both engines (single verification per paper)

**Benefits:**
- ✅ **100% accurate program classification** (SPECIFIC vs GENERIC)
- ✅ **Eliminates false attribution problems** (major fix)
- ✅ **Enhanced citation-based reasoning** in Stage 2
- ✅ **Complete audit trail** for all assessments  
- ✅ **Fixed AttributeError** causing 96.6% MAYBE rate issue

Each stage runs on TWO independent engines that cross-validate each other, except Stage 1.5 which runs once and shares results.

### **Quick Start**

#### 1. **Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key for full-text
cp config/config.example.yaml config/config_fulltext.yaml
# Edit config_fulltext.yaml and add your OpenRouter API key

# Optional: Configure Perplexity for Stage 1.5 internet search
export PERPLEXITY_API_KEY="your-perplexity-key-here"
```

#### 1.5. **Configure Stage 1.5 (Optional)**
Stage 1.5 program verification is enabled by default but requires Perplexity API for internet search:

```yaml
# In config/config_fulltext.yaml
stage1_5:
  enabled: true                    # Enable/disable Stage 1.5
  use_fuzzy_matching: true         # Match against known programs
  use_perplexity_search: true      # Internet search for unknown programs
  perplexity_model: "llama-3.1-sonar-large-128k-online"
  perplexity_timeout: 60           # Search timeout in seconds
  override_llm_assessment: true    # Apply verification results
  log_verification_details: true   # Detailed logging
```

**Without Perplexity API**: Stage 1.5 still works for known programs via fuzzy matching.

#### 2. **Prepare Data**
Required files:
- `data/input/tei_xml/` - Folder with TEI XML files
- `data/input/all_papers_metadata_with_xml.xlsx` - Metadata with XML paths
- `data/input/human_validation_fulltext.xlsx` - Validation set (optional)

#### 3. **Run Validation**
```bash
# Test on small set first
cd fulltext
python run_validation.py --limit 5 --output ../data/output/fulltext --yes

# Run full validation (118 papers)
python run_validation.py --output ../data/output/fulltext --yes
```

#### 4. **Analyze Results**
```bash
# Results are saved to CSV automatically
# Use provided analysis script
cd ..
python scripts/validation/quick_analysis.py data/output/fulltext/validation_results_*.csv
```

### **Key Files**
- **Main Engine**: `fulltext/dual_screener.py`
- **CLI**: `fulltext/run_validation.py`
- **Config**: `config/config_fulltext.yaml`
- **Prompts**: 
  - Stage 1 (Extraction): `prompts/fulltext_extraction_stage1.txt` ⚠️ **UNDER TESTING**
  - Stage 2 (Interpretation): `prompts/fulltext_interpretation_stage2.txt` ✅ **ACTIVE**
  - **📝 Testing Log**: [`docs/PROMPT_TESTING_LOG.md`](docs/PROMPT_TESTING_LOG.md) - Complete history of all prompt iterations
- **Components** (in `src/fulltext/`):
  - `tei_parser.py` - Parse TEI XML files
  - `extraction_engine.py` - Stage 1: Extract information
  - `program_verifier.py` - **Stage 1.5: Program verification** ✨ **NEW**
  - `interpretation_engine.py` - Stage 2: Assess criteria
  - `agreement_checker.py` - Compare engines
  - `enhanced_decision_processor.py` - Final decision
- **Program Matching**: `program_matcher.py` - Fuzzy matching for known graduation programs

---

## 🔧 Configuration

### **Title & Abstract Config** (`config/config.yaml`)
```yaml
openrouter:
  api_key: "your-api-key-here"

model:
  model_name: "anthropic/claude-3.5-haiku-20241022"
  temperature: 0.1
  max_tokens: 1500

prompts:
  criteria_file: "prompts/structured_screening_criteria_optimized.txt"
```

### **Full-Text Config** (`config/config_fulltext.yaml`)
```yaml
api:
  openrouter_key: "your-api-key-here"

engine1:  # Claude Haiku (fast, thorough)
  model: "anthropic/claude-3.5-haiku-20241022"
  temperature: 0.1
  max_tokens: 2000

engine2:  # GPT-4o (verification)
  model: "openai/gpt-4o-2024-11-20"
  temperature: 0.1
  max_tokens: 2000

paths:
  tei_xml_dir: "data/input/tei_xml"
  metadata_file: "data/input/all_papers_metadata_with_xml.xlsx"
```

---

## 📋 Inclusion Criteria (Both Pipelines)

Papers must meet ALL of the following criteria:

1. **LMIC Country** 🌍 - Study conducted in low- or middle-income country
2. **Cash Support** 💵 - Program provides cash transfers/consumption support (NOT loans)
3. **Productive Assets** 🐄 - Program provides livestock, equipment, or productive materials
4. **Relevant Outcomes** 📊 - Measures economic/livelihood outcomes
5. **Study Design** 🔬 - Uses quantitative impact evaluation methods (NOT reviews)
6. **Publication Year** 📅 - Published 2004 or later
7. **Completed Study** ✅ - Research presents finished findings

### **Special Note: Graduation Programs**
The system has enhanced recognition for graduation programs (TUP, BRAC, etc.) which often use terminology like:
- "stipends", "allowances", "consumption support" instead of "cash transfers"
- "participant support", "interim assistance", "livelihood payments"

---

## 📊 Recent Validation Results

### **Full-Text Pipeline Status (November 2025)**

**Current Results** (Parser fix only):
- Precision: 93.8%
- Recall: 65.2%
- F1: 76.9%
- False Negatives: 16

**🚨 Critical Discovery**: Validation ran with OLD prompt (enhancements not applied)
- Issue: Modified wrong prompt file (`structured_screening_unified.txt` instead of `fulltext_interpretation_stage2.txt`)
- Impact: Results show only parser fix, not combined improvements
- ✅ **Fixed**: Enhancements now properly applied to `fulltext_interpretation_stage2.txt`

**Expected Results** (After re-validation with enhanced prompt):
- Precision: 93%+ (maintained)
- Recall: **75-80%** (+10-15% improvement)
- F1: **83-85%**
- False Negatives: **6-8** (recover 8-10 papers)

For detailed analysis, see [`docs/VALIDATION_RESULTS_ANALYSIS.md`](docs/VALIDATION_RESULTS_ANALYSIS.md)

---

## 🚨 Important: Prompt File Mapping

**To avoid the mistake of modifying the wrong prompt file:**

### Title & Abstract Pipeline
```
integrated_screener.py → prompts/structured_screening_criteria_optimized.txt
```

### Full-Text Pipeline
```
fulltext/dual_screener.py 
  → src/fulltext/interpretation_engine.py
    → prompts/fulltext_interpretation_stage2.txt ⚠️ THIS IS THE ACTIVE FILE
```

**DO NOT modify**:
- ❌ `prompts/structured_screening_unified.txt` - NOT used by any production code
- ❌ Old prompt versions in `prompts/archive/`

**Always verify** after making changes:
```powershell
# Check file timestamp
(Get-Item prompts\fulltext_interpretation_stage2.txt).LastWriteTime

# Verify enhancement is present
Select-String -Path prompts\fulltext_interpretation_stage2.txt -Pattern "GRADUATION PROGRAM"
```

---

## 🛠️ Tools and Utilities

### Export Tools (`tools/`)
- **`export_csv_compact.py`** - Create compact CSV (recommended, prevents corruption)
- **`export_with_u1_fixed.py`** - Export with proper U1 ID mapping
- **`verify_and_mark_duplicates.py`** - Quality checks and duplicate detection
- **`deduplicate_csv.py`** - Remove duplicate entries
- **`fix_csv_escaping.py`** - Fix CSV corruption issues
- **`generate_codebook.py`** - Generate PDF documentation

### Analysis Tools (`tools/`)
- **`analyze_dual_results.py`** - Analyze dual-engine agreement
- **`decision_analysis.py`** - Analyze decision patterns

See [`tools/README.md`](tools/README.md) for detailed documentation.

---

## 📁 Project Structure

```
paper-screening-pipeline/
├── 📄 README.md                           # This file
├── 📄 ARCHITECTURE.md                     # ⚠️ CRITICAL: Detailed system architecture
│
├── 📂 Title & Abstract Pipeline (Root)
│   ├── integrated_screener.py             # Main screening engine
│   ├── decision_processor.py              # Decision logic
│   ├── run_screening.py                   # CLI entry point
│   ├── batch_dual_screening.py            # Batch processing
│   ├── screen_with_logging.py             # Production screening with logs
│   └── program_matcher.py                 # Program matching utilities
│
├── 📂 fulltext/                           # Full-Text Pipeline
│   ├── dual_screener.py                   # 🎯 Main full-text engine
│   ├── run_validation.py                  # 🎯 Validation CLI
│   ├── run_enhanced_validation.py         # Enhanced validation with metrics
│   └── README.md                          # Full-text specific documentation
│
├── 📂 src/fulltext/                       # Full-Text Components
│   ├── tei_parser.py                      # Parse TEI XML files
│   ├── extraction_engine.py               # Stage 1: Extract info
│   ├── interpretation_engine.py           # Stage 2: Assess criteria
│   ├── agreement_checker.py               # Compare engines
│   ├── enhanced_decision_processor.py     # Final decisions
│   └── fulltext_models.py                 # Data models
│
├── 📂 config/                             # Configuration
│   ├── config.yaml                        # 🎯 Title/Abstract config
│   ├── config_fulltext.yaml               # 🎯 Full-text config
│   └── config.example.yaml                # Configuration template
│
├── 📂 prompts/                            # LLM Prompts
│   ├── structured_screening_criteria_optimized.txt  # 🎯 Title/Abstract prompt
│   ├── structured_screening_followup.txt            # Follow-up for MAYBE cases
│   ├── fulltext_extraction_stage1.txt               # 🎯 Full-text Stage 1
│   ├── fulltext_interpretation_stage2.txt           # 🎯 Full-text Stage 2 ⚠️ CRITICAL
│   └── archive/                                     # Old prompt versions
│
├── 📂 tools/                              # Export and Utility Scripts
├── 📂 scripts/                            # Validation and Analysis Scripts
├── 📂 src/                                # Core Modules
├── 📂 data/                               # Data (gitignored)
├── 📂 docs/                               # Documentation
├── 📂 logs/                               # Application Logs
└── 📂 archive/                            # Development History
```

---

## 📚 Documentation

### Quick Reference
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - ⚠️ **READ THIS FIRST** - Complete system architecture and file mapping
- **[tools/README.md](tools/README.md)** - Tools documentation
- **[fulltext/README.md](fulltext/README.md)** - Full-text pipeline specifics

### Validation and Results
- **[docs/VALIDATION_RESULTS_ANALYSIS.md](docs/VALIDATION_RESULTS_ANALYSIS.md)** - Current validation analysis
- **[docs/CORRECTION_SUMMARY.md](docs/CORRECTION_SUMMARY.md)** - Label corrections summary
- **[docs/VALIDATION_LABEL_CORRECTIONS.md](docs/VALIDATION_LABEL_CORRECTIONS.md)** - Detailed corrections

### Data and Deployment
- **[docs/DATA_INVENTORY.md](docs/DATA_INVENTORY.md)** - Data structure documentation
- **[docs/PRODUCTION_DEPLOYMENT_COMPLETE.md](docs/PRODUCTION_DEPLOYMENT_COMPLETE.md)** - Deployment guide

---

## 🔍 Troubleshooting

### "Which pipeline should I use?"
- **Have titles/abstracts only?** → Title & Abstract Pipeline
- **Have full-text XML files?** → Full-Text Pipeline

### "Which prompt file should I modify?"
- **Title/Abstract improvements?** → `prompts/structured_screening_criteria_optimized.txt`
- **Full-text improvements?** → `prompts/fulltext_interpretation_stage2.txt`
- **NOT SURE?** → Read `ARCHITECTURE.md` first!

### "I modified a prompt but nothing changed"
1. Check you modified the correct file (see ARCHITECTURE.md)
2. Verify file timestamp: `(Get-Item prompts\your_file.txt).LastWriteTime`
3. Grep for your changes: `Select-String -Path prompts\your_file.txt -Pattern "your_text"`
4. Test on small set first: `--limit 5`

### "CSV file is corrupted"
```bash
# Fix CSV escaping issues
python tools/fix_csv_escaping.py corrupted_file.csv

# Or export compact version (no abstracts)
python tools/export_csv_compact.py results_file.csv
```

### "Duplicates in results"
```bash
# Verify and mark duplicates
python tools/verify_and_mark_duplicates.py results.csv

# Or remove duplicates
python tools/deduplicate_csv.py results.csv
```

---

## 🎓 Key Lessons Learned

### 1. **Multiple Prompt Files = High Risk**
- System has separate prompts for different components
- **Always check ARCHITECTURE.md before modifying prompts**
- Verify file timestamps after changes
- Test immediately after modifications

### 2. **Specialized Terminology Requires Explicit Guidance**
- Graduation programs use "stipends", "allowances" instead of "cash transfers"
- Domain-specific examples dramatically improve recognition
- Real currency amounts serve as effective triggers

### 3. **Parser Issues Can Masquerade as Prompt Issues**
- Extracting 0 characters looks like poor assessment
- **Fix technical issues before tuning prompts**
- Combined fixes (parser + prompt) often required

### 4. **Conservative Approach Works**
- 2 false positives in 118 papers = excellent precision
- MAYBE/CONFLICT mechanism successfully flags uncertainty
- Better to flag for human review than make wrong decision

---

## 🤝 Contributing

When adding features or fixing bugs:

1. **Identify the correct pipeline** (Title/Abstract OR Full-Text)
2. **Read ARCHITECTURE.md** to understand file relationships
3. **Modify the correct files** (don't assume based on filename)
4. **Test on small set first** (`--limit 5` or `--limit 10`)
5. **Update documentation** (this README + ARCHITECTURE.md)
6. **Verify prompt changes** (check timestamps and grep for content)

---

## 📝 License

[Add your license information here]

---

## 📞 Contact

[Add your contact information here]

---

## ⚠️ Final Reminder

**This repository contains TWO SEPARATE pipelines:**

| When working with... | Use these files... |
|---------------------|-------------------|
| **Titles & Abstracts** | `integrated_screener.py`, `config/config.yaml`, `prompts/structured_screening_criteria_optimized.txt` |
| **Full-Text Papers** | `fulltext/dual_screener.py`, `config/config_fulltext.yaml`, `prompts/fulltext_interpretation_stage2.txt` |

**Always consult [`ARCHITECTURE.md`](ARCHITECTURE.md) before making changes!**

---

*Last Updated*: November 6, 2025  
*Status*: Two active pipelines - Title/Abstract (production), Full-Text (validation in progress)

---

## 📄 Interactive Paper Viewer (Streamlit)

An optional lightweight web UI lets colleagues look up a paper by `paper_id` and inspect:

- Final decision + rule applied
- Engine agreement level
- Per-criterion assessments & reasoning (both engines)
- Stage 1.5 program verification (assessment, verified program name, reasoning)

### Location
`apps/viewer_app.py`

### Install Extra Dependencies
Additions were made to `requirements.txt` (`streamlit`, `pyarrow`). Re-install:

```powershell
pip install -r requirements.txt
```

### Run Locally (Windows PowerShell)
```powershell
streamlit run apps\viewer_app.py
```

Then open the local URL (usually http://localhost:8501). Enter a `paper_id` (folder name under `data/output/fulltext/papers/`) to view its artifacts.

### Deployment Options
- **Streamlit Community Cloud**: Push repo to GitHub; create new app pointing to `apps/viewer_app.py`.
- **Hugging Face Spaces**: Add a `requirements.txt`; select Streamlit as SDK.
- **Internal Server**: Run behind reverse proxy (add `--server.port 8501 --server.headless true`).

### Security & Data Notes
- No write operations; reads JSON artifacts only.
- Ensure `data/output/fulltext/papers/` excludes sensitive unpublished text if sharing externally.

### Future Enhancements
- Autocomplete paper IDs (scan folder list)
- Add aggregated disagreement highlights
- Link literal citation evidence (if stored separately)
- Download per-paper JSON bundle

---

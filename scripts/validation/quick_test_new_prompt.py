"""
Quick test of new streamlined prompt with program context.
Tests on 20 papers (mix of includes and excludes) to verify formatting and parsing.
"""

import sys
from pathlib import Path
import pandas as pd
import time

# Add parent directory to path
script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from integrated_screener import IntegratedStructuredScreener
from src.models import Paper, ModelConfig

def load_sample_papers(n_papers: int = 20):
    """Load a small sample from validation data merged with corpus."""
    
    # Load validation labels
    s3_path = project_dir / "data" / "input" / "s3above.xlsx"
    print(f"Loading validation labels from {s3_path.name}...")
    labels_df = pd.read_excel(s3_path)
    
    # Map string values to binary
    labels_df['include_binary'] = labels_df['include'].apply(lambda x: 1 if 'Include' in str(x) else 0)
    
    # Get mix: 2 includes (all available), 18 excludes
    includes = labels_df[labels_df['include_binary'] == 1]
    excludes = labels_df[labels_df['include_binary'] == 0].head(18)
    sample_df = pd.concat([includes, excludes]).reset_index(drop=True)
    
    print(f"Selected {len(sample_df)} papers: {len(includes)} includes, {len(excludes)} excludes")
    
    # Load corpus to get abstracts
    print(f"Loading corpus from RIS files to get abstracts...")
    from src.parsers import RISParser
    
    # Load all RIS files (.txt files are RIS formatted)
    ris_files = [
        project_dir / "data" / "input" / "Excluded by DEP classifier (n=54,924).txt",
        project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
    ]
    
    parser = RISParser()
    all_corpus_papers = []
    for ris_file in ris_files:
        if ris_file.exists():
            print(f"  Loading {ris_file.name}...")
            papers = parser.parse_file(str(ris_file))
            all_corpus_papers.extend(papers)
            print(f"    Loaded {len(papers)} papers")
    
    # Create lookup by ID using U1 field (numeric ID field in RIS)
    corpus_lookup = {}
    for paper in all_corpus_papers:
        # Extract ID from U1 field
        paper_id = None
        
        if hasattr(paper, 'ris_fields') and paper.ris_fields:
            # U1 field contains the numeric ID
            if 'U1' in paper.ris_fields:
                u1_value = paper.ris_fields['U1']
                # Handle both string and list formats
                paper_id = u1_value[0] if isinstance(u1_value, list) else u1_value
        
        if paper_id:
            corpus_lookup[str(paper_id).strip()] = paper
    
    print(f"Created lookup with {len(corpus_lookup)} papers from corpus")
    
    # Merge validation labels with corpus data
    papers = []
    matched = 0
    for _, row in sample_df.iterrows():
        paper_id = str(row.get('ID', ''))
        
        # Try to find in corpus
        corpus_paper = corpus_lookup.get(paper_id)
        
        if corpus_paper:
            matched += 1
            # Use corpus paper with full abstract
            papers.append({
                'paper': corpus_paper,
                'expected': 'INCLUDE' if row['include_binary'] == 1 else 'EXCLUDE'
            })
        else:
            # Fallback: create paper from validation data (no abstract)
            year_val = row.get('Year')
            year = None
            if pd.notna(year_val):
                try:
                    year_str = str(year_val).strip()
                    if year_str and year_str.isdigit():
                        year = int(year_str)
                except:
                    year = None
            
            paper = Paper(
                paper_id=paper_id,
                title=str(row.get('Title', '')),
                abstract='',  # No abstract available
                authors=[],
                year=year,
                journal='',
                keywords=[]
            )
            papers.append({
                'paper': paper,
                'expected': 'INCLUDE' if row['include_binary'] == 1 else 'EXCLUDE'
            })
    
    print(f"Matched {matched}/{len(sample_df)} papers with corpus (have abstracts)")
    print()
    
    return papers

def test_new_prompt():
    """Test the new prompt on sample papers."""
    
    print("=" * 80)
    print("QUICK TEST: Program Filter Prompt (Auto-Include/Exclude by Program)")
    print("=" * 80)
    print()
    
    # Initialize screener
    config_path = project_dir / "config" / "config.yaml"
    print(f"Initializing screener with config: {config_path}")
    
    # Load config and create ModelConfig
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    model_config = ModelConfig(
        model_name=config['models']['primary']['model_name'],
        api_url="https://openrouter.ai/api/v1",
        api_key=config['openrouter']['api_key'],
        provider="openrouter",
        temperature=0.1,
        max_tokens=1500
    )
    
    screener = IntegratedStructuredScreener(model_config, use_program_filter=True)
    print(f"✓ Screener initialized with PROGRAM FILTER enabled")
    print()
    
    # Load sample
    papers = load_sample_papers(n_papers=20)
    
    # Test each paper
    results = []
    total_time = 0
    
    for i, item in enumerate(papers, 1):
        paper = item['paper']
        expected = item['expected']
        
        print(f"\n[{i}/20] Testing paper: {paper.paper_id}")
        print(f"  Title: {paper.title[:80]}...")
        print(f"  Expected: {expected}")
        
        start_time = time.time()
        try:
            result = screener.screen_paper(paper)
            elapsed = time.time() - start_time
            total_time += elapsed
            
            decision = result.final_decision.value.upper()
            correct = (decision == expected) or (decision == 'MAYBE' and expected == 'INCLUDE')
            
            print(f"  Decision: {decision} ({'✓' if correct else '✗'})")
            print(f"  Time: {elapsed:.1f}s")
            
            # Show program recognition for all papers
            prog_rec = result.program_recognition
            print(f"  Program: {prog_rec.assessment} - {prog_rec.reasoning}")
            
            # Show criteria for first 3 papers
            if i <= 3:
                print(f"  Other Criteria:")
                criteria = result.get_criteria_summary()
                for k, v in criteria.items():
                    if k != 'program_recognition':  # Skip program since we showed it above
                        print(f"    {k}: {v}")
            
            results.append({
                'paper_id': paper.paper_id,
                'expected': expected,
                'decision': decision,
                'correct': correct,
                'time': elapsed,
                'criteria': result.get_criteria_summary()
            })
            
        except Exception as e:
            print(f"  ✗ ERROR: {str(e)}")
            results.append({
                'paper_id': paper.id,
                'expected': expected,
                'decision': 'ERROR',
                'correct': False,
                'time': 0,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    correct = sum(1 for r in results if r['correct'])
    errors = sum(1 for r in results if r['decision'] == 'ERROR')
    
    print(f"\nTotal papers tested: {len(results)}")
    print(f"Correct decisions: {correct}/{len(results)} ({correct/len(results)*100:.1f}%)")
    print(f"Errors: {errors}")
    print(f"Average time: {total_time/len(results):.1f}s")
    print(f"Total time: {total_time:.1f}s")
    
    # Breakdown
    decisions = {}
    for r in results:
        d = r['decision']
        decisions[d] = decisions.get(d, 0) + 1
    
    print(f"\nDecision breakdown:")
    for d, count in sorted(decisions.items()):
        print(f"  {d}: {count}")
    
    # False positives/negatives
    false_positives = sum(1 for r in results if r['expected'] == 'EXCLUDE' and r['decision'] == 'INCLUDE')
    false_negatives = sum(1 for r in results if r['expected'] == 'INCLUDE' and r['decision'] == 'EXCLUDE')
    
    print(f"\nError analysis:")
    print(f"  False positives: {false_positives} (EXCLUDE labeled as INCLUDE)")
    print(f"  False negatives: {false_negatives} (INCLUDE labeled as EXCLUDE)")
    
    # Check if any parsing errors
    print(f"\n✓ Prompt parsing: {'SUCCESS' if errors == 0 else 'FAILED'}")
    
    return results

if __name__ == "__main__":
    results = test_new_prompt()

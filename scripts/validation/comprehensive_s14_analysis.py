"""
Comprehensive analysis of s14above.xlsx validation set
Tests LLM screening on ALL papers to understand performance and identify discrepancies
"""

import sys
from pathlib import Path
import pandas as pd
import time
from collections import defaultdict

# Add parent directory to path
script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from integrated_screener import IntegratedStructuredScreener
from src.models import Paper, ModelConfig
from src.parsers import RISParser

def load_all_papers():
    """Load ALL papers from s14above.xlsx validation file with corpus abstracts"""
    print("\nLoading ALL validation labels from s14above.xlsx...")
    s14_path = project_dir / "data" / "input" / "s14above.xlsx"
    labels_df = pd.read_excel(s14_path)
    
    print(f"Total papers in s14above.xlsx: {len(labels_df)}")
    print("\nLabel distribution:")
    print(labels_df['include'].value_counts())
    
    # Load corpus to get abstracts
    print(f"\nLoading corpus from RIS files to get abstracts...")
    parser = RISParser()
    
    # Load all RIS files (.txt files are RIS formatted)
    ris_files = [
        project_dir / "data" / "input" / "Excluded by DEP classifier (n=54,924).txt",
        project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
    ]
    
    corpus_lookup = {}
    for ris_file in ris_files:
        if ris_file.exists():
            print(f"  Loading {ris_file.name}...")
            papers = parser.parse_file(str(ris_file))
            print(f"    Loaded {len(papers)} papers")
            for paper in papers:
                # U1 field contains the numeric ID
                if hasattr(paper, 'ris_fields') and 'U1' in paper.ris_fields:
                    u1_value = paper.ris_fields['U1']
                    paper_id = u1_value[0] if isinstance(u1_value, list) else u1_value
                    corpus_lookup[str(paper_id).strip()] = paper
    
    print(f"Created lookup with {len(corpus_lookup)} papers from corpus")
    
    # Merge validation labels with corpus data
    papers = []
    matched = 0
    for _, row in labels_df.iterrows():
        paper_id = str(row.get('ID', ''))
        
        # Try to find in corpus
        corpus_paper = corpus_lookup.get(paper_id)
        
        if corpus_paper:
            matched += 1
            # Use corpus paper with full abstract
            papers.append({
                'paper': corpus_paper,
                'expected': row['include'],
                'paper_id': paper_id
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
                doi='',
                source_file='s14above.xlsx'
            )
            papers.append({
                'paper': paper,
                'expected': row['include'],
                'paper_id': paper_id
            })
    
    print(f"Matched {matched}/{len(labels_df)} papers with corpus (have abstracts)")
    return papers, labels_df

def test_all_papers():
    """Test LLM screening on all papers from s14above.xlsx"""
    
    # Initialize screener
    config_path = project_dir / "config" / "config.yaml"
    print(f"\nInitializing screener with config: {config_path}")
    
    # Load config and create ModelConfig
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    model_config = ModelConfig(
        provider="openrouter",
        model_name=config['models']['primary']['model_name'],
        api_url=config['openrouter']['api_url'],
        api_key=config['openrouter']['api_key'],
        temperature=config['models']['primary'].get('temperature', 0.0),
        max_tokens=config['models']['primary'].get('max_tokens', 4000)
    )
    
    screener = IntegratedStructuredScreener(
        model_config=model_config,
        use_program_filter=True  # Using program filter prompt
    )
    print("✓ Screener initialized with PROGRAM FILTER enabled\n")
    
    # Load all papers
    papers_data, labels_df = load_all_papers()
    total = len(papers_data)
    
    # Track results by human label
    results_by_human_label = defaultdict(lambda: {
        'llm_include': [],
        'llm_exclude': [],
        'llm_maybe': []
    })
    
    # Track discrepancies
    discrepancies = {
        'false_positives': [],  # Human: Excluded, LLM: INCLUDE/MAYBE
        'false_negatives': [],  # Human: Included/Maybe, LLM: EXCLUDE
        'maybe_agreements': []  # Both uncertain
    }
    
    print("="*80)
    print(f"TESTING ALL {total} PAPERS FROM s14above.xlsx")
    print("="*80)
    
    start_time = time.time()
    
    for idx, paper_data in enumerate(papers_data, 1):
        paper = paper_data['paper']
        expected = paper_data['expected']
        paper_id = paper_data['paper_id']
        
        # Screen the paper
        result = screener.screen_paper(paper)
        
        # Get decision - convert enum to string
        llm_decision_enum = result.final_decision
        llm_decision = str(llm_decision_enum).split('.')[-1]  # Convert ScreeningDecision.EXCLUDE -> 'EXCLUDE'
        
        # Debug first few papers
        if idx <= 3:
            print(f"\n[DEBUG Paper {idx}]")
            print(f"  Title: {paper.title[:60]}...")
            print(f"  Has abstract: {len(paper.abstract) > 0} ({len(paper.abstract)} chars)")
            print(f"  Decision enum: {llm_decision_enum}")
            print(f"  Decision string: {llm_decision}")
            if hasattr(result, 'program_recognition'):
                print(f"  Program: {result.program_recognition}")
            if hasattr(result, 'decision_reasoning'):
                print(f"  Reasoning: {result.decision_reasoning[:100]}...")
        
        # Track by human label
        human_category = str(expected)
        if llm_decision == 'INCLUDE':
            results_by_human_label[human_category]['llm_include'].append(paper_id)
        elif llm_decision == 'EXCLUDE':
            results_by_human_label[human_category]['llm_exclude'].append(paper_id)
        else:  # MAYBE
            results_by_human_label[human_category]['llm_maybe'].append(paper_id)
        
        # Track discrepancies
        if 'Excluded' in str(expected) and llm_decision in ['INCLUDE', 'MAYBE']:
            discrepancies['false_positives'].append({
                'paper_id': paper_id,
                'title': paper.title[:80],
                'human': expected,
                'llm': llm_decision,
                'program': result.program_recognition if hasattr(result, 'program_recognition') else 'N/A'
            })
        
        if 'Include' in str(expected) and llm_decision == 'EXCLUDE':
            discrepancies['false_negatives'].append({
                'paper_id': paper_id,
                'title': paper.title[:80],
                'human': expected,
                'llm': llm_decision,
                'program': result.program_recognition if hasattr(result, 'program_recognition') else 'N/A'
            })
        
        if 'Maybe' in str(expected) and llm_decision == 'MAYBE':
            discrepancies['maybe_agreements'].append({
                'paper_id': paper_id,
                'title': paper.title[:80]
            })
        
        # Print progress every 10 papers
        if idx % 10 == 0 or idx == total:
            elapsed = time.time() - start_time
            avg_time = elapsed / idx
            print(f"Progress: {idx}/{total} papers ({idx/total*100:.1f}%) | Avg: {avg_time:.1f}s/paper")
    
    total_time = time.time() - start_time
    
    # Print comprehensive results
    print("\n" + "="*80)
    print("COMPREHENSIVE RESULTS")
    print("="*80)
    
    # Summary by human label
    print("\n1. LLM DECISIONS BY HUMAN LABEL")
    print("-"*80)
    for human_label in sorted(results_by_human_label.keys()):
        data = results_by_human_label[human_label]
        total_in_category = len(data['llm_include']) + len(data['llm_exclude']) + len(data['llm_maybe'])
        
        print(f"\nHuman Label: {human_label} ({total_in_category} papers)")
        print(f"  LLM INCLUDE: {len(data['llm_include'])} ({len(data['llm_include'])/total_in_category*100:.1f}%)")
        print(f"  LLM EXCLUDE: {len(data['llm_exclude'])} ({len(data['llm_exclude'])/total_in_category*100:.1f}%)")
        print(f"  LLM MAYBE:   {len(data['llm_maybe'])} ({len(data['llm_maybe'])/total_in_category*100:.1f}%)")
    
    # Discrepancy analysis
    print("\n" + "="*80)
    print("2. DISCREPANCY ANALYSIS")
    print("="*80)
    
    print(f"\nFalse Positives: {len(discrepancies['false_positives'])} (Human: Excluded, LLM: INCLUDE/MAYBE)")
    if discrepancies['false_positives']:
        print("\nDetails:")
        for disc in discrepancies['false_positives'][:10]:  # Show first 10
            print(f"  ID: {disc['paper_id']}")
            print(f"    Title: {disc['title']}...")
            print(f"    Human: {disc['human']} | LLM: {disc['llm']}")
            print(f"    Program: {disc['program']}")
            print()
    
    print(f"\nFalse Negatives: {len(discrepancies['false_negatives'])} (Human: Included/Maybe, LLM: EXCLUDE)")
    if discrepancies['false_negatives']:
        print("\nDetails:")
        for disc in discrepancies['false_negatives']:  # Show all
            print(f"  ID: {disc['paper_id']}")
            print(f"    Title: {disc['title']}...")
            print(f"    Human: {disc['human']} | LLM: {disc['llm']}")
            print(f"    Program: {disc['program']}")
            print()
    
    print(f"\nMaybe Agreements: {len(discrepancies['maybe_agreements'])} (Both Human and LLM uncertain)")
    
    # Overall metrics
    print("\n" + "="*80)
    print("3. OVERALL METRICS")
    print("="*80)
    
    total_llm_include = sum(len(d['llm_include']) for d in results_by_human_label.values())
    total_llm_exclude = sum(len(d['llm_exclude']) for d in results_by_human_label.values())
    total_llm_maybe = sum(len(d['llm_maybe']) for d in results_by_human_label.values())
    
    print(f"\nTotal papers tested: {total}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Average time per paper: {total_time/total:.1f}s")
    print(f"\nLLM Decision Distribution:")
    print(f"  INCLUDE: {total_llm_include} ({total_llm_include/total*100:.1f}%)")
    print(f"  EXCLUDE: {total_llm_exclude} ({total_llm_exclude/total*100:.1f}%)")
    print(f"  MAYBE:   {total_llm_maybe} ({total_llm_maybe/total*100:.1f}%)")
    
    print(f"\nDiscrepancy Summary:")
    print(f"  False Positives: {len(discrepancies['false_positives'])}")
    print(f"  False Negatives: {len(discrepancies['false_negatives'])}")
    print(f"  Maybe Agreements: {len(discrepancies['maybe_agreements'])}")
    
    # Save detailed results
    results_file = project_dir / "scripts" / "validation" / "s14_comprehensive_results.csv"
    print(f"\n✓ Saving detailed results to {results_file.name}")
    
    # Create results dataframe
    results_rows = []
    for paper_data in papers_data:
        paper = paper_data['paper']
        expected = paper_data['expected']
        paper_id = paper_data['paper_id']
        
        # Get LLM decision
        human_category = str(expected)
        if paper_id in results_by_human_label[human_category]['llm_include']:
            llm_decision = 'INCLUDE'
        elif paper_id in results_by_human_label[human_category]['llm_exclude']:
            llm_decision = 'EXCLUDE'
        else:
            llm_decision = 'MAYBE'
        
        results_rows.append({
            'paper_id': paper_id,
            'title': paper.title,
            'human_label': expected,
            'llm_decision': llm_decision,
            'agreement': 'YES' if (('Include' in str(expected) and llm_decision == 'INCLUDE') or 
                                   ('Excluded' in str(expected) and llm_decision == 'EXCLUDE') or
                                   ('Maybe' in str(expected) and llm_decision == 'MAYBE')) else 'NO'
        })
    
    results_df = pd.DataFrame(results_rows)
    results_df.to_csv(results_file, index=False)
    
    return results_by_human_label, discrepancies

if __name__ == "__main__":
    results_by_label, discrepancies = test_all_papers()
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Review false negatives (Human: Include, LLM: Exclude)")
    print("2. Review false positives (Human: Exclude, LLM: Include/Maybe)")
    print("3. Analyze patterns in discrepancies")
    print("4. Check if human labels need correction (like s3above.xlsx)")

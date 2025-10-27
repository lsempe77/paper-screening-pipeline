#!/usr/bin/env python3
"""
Enhanced Dual-Engine Production Screening Script

Features:
1. Parallel processing for faster execution
2. Checkpoint system for reliability and resumability
3. Progress tracking and recovery
4. Robust error handling
5. Performance analytics
"""

import sys
import os
import json
import time
import yaml
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
from collections import defaultdict
import concurrent.futures
import threading
from typing import Dict, List, Tuple, Optional
import hashlib
import pickle

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from integrated_screener import IntegratedStructuredScreener
from src.models import ModelConfig
from src.parsers import RISParser

class CheckpointManager:
    """Manages checkpointing and progress recovery."""
    
    def __init__(self, checkpoint_dir: str = "data/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
    
    def get_checkpoint_path(self, session_id: str) -> Path:
        """Get checkpoint file path for session."""
        return self.checkpoint_dir / f"dual_screening_{session_id}.pkl"
    
    def save_checkpoint(self, session_id: str, data: Dict):
        """Save checkpoint data."""
        with self.lock:
            checkpoint_path = self.get_checkpoint_path(session_id)
            with open(checkpoint_path, 'wb') as f:
                pickle.dump(data, f)
    
    def load_checkpoint(self, session_id: str) -> Optional[Dict]:
        """Load checkpoint data if exists."""
        checkpoint_path = self.get_checkpoint_path(session_id)
        if checkpoint_path.exists():
            try:
                with open(checkpoint_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"⚠️  Failed to load checkpoint: {e}")
        return None
    
    def cleanup_checkpoint(self, session_id: str):
        """Remove checkpoint after successful completion."""
        checkpoint_path = self.get_checkpoint_path(session_id)
        if checkpoint_path.exists():
            checkpoint_path.unlink()

class EnhancedDualEngineScreener:
    """Enhanced screener with parallel processing and checkpointing."""
    
    def __init__(self, config, checkpoint_manager: CheckpointManager):
        self.config = config
        self.checkpoint_manager = checkpoint_manager
        
        # Initialize both screeners (thread-safe)
        self.engine1_config = ModelConfig(
            model_name=config['models']['primary']['model_name'],
            api_url="https://openrouter.ai/api/v1",
            api_key=config['openrouter']['api_key'],
            provider="openrouter",
            temperature=0.1,
            max_tokens=2500
        )
        
        self.engine2_config = ModelConfig(
            model_name=config['models']['secondary']['model_name'],
            api_url="https://openrouter.ai/api/v1",
            api_key=config['openrouter']['api_key'],
            provider="openrouter",
            temperature=0.1,
            max_tokens=2500
        )
        
        # Create thread-local screeners
        self.screeners = threading.local()
        
        print(f"🤖 Engine 1: {self.engine1_config.model_name}")
        print(f"🤖 Engine 2: {self.engine2_config.model_name}")
    
    def get_screeners(self) -> Tuple[IntegratedStructuredScreener, IntegratedStructuredScreener]:
        """Get thread-local screeners."""
        if not hasattr(self.screeners, 'screener1'):
            self.screeners.screener1 = IntegratedStructuredScreener(self.engine1_config)
            self.screeners.screener2 = IntegratedStructuredScreener(self.engine2_config)
        return self.screeners.screener1, self.screeners.screener2
    
    def screen_paper_parallel(self, paper, paper_num, total_papers) -> Dict:
        """Screen a single paper with both engines in parallel."""
        
        print(f"🔍 [{paper_num:3d}/{total_papers}] {paper.title[:60]}...")
        
        screener1, screener2 = self.get_screeners()
        
        def screen_with_engine(screener, engine_name):
            try:
                start_time = time.time()
                result = screener.screen_paper(paper)
                processing_time = time.time() - start_time
                
                return {
                    'decision': result.final_decision.value,
                    'reasoning': result.decision_reasoning,
                    'processing_time': round(processing_time, 2),
                    'criteria': self._extract_criteria(result),
                    'success': True,
                    'error': None
                }
            except Exception as e:
                return {
                    'decision': 'error',
                    'reasoning': f'Processing error: {str(e)}',
                    'processing_time': 0,
                    'success': False,
                    'error': str(e)
                }
        
        # Run both engines in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(screen_with_engine, screener1, "Engine 1")
            future2 = executor.submit(screen_with_engine, screener2, "Engine 2")
            
            # Wait for both to complete
            result1 = future1.result()
            result2 = future2.result()
        
        results = {
            'engine1': result1,
            'engine2': result2
        }
        
        # Print results
        if result1['success']:
            print(f"       🤖1: {result1['decision'].upper()} ({result1['processing_time']:.1f}s)")
        else:
            print(f"       🤖1: ERROR - {result1['error']}")
        
        if result2['success']:
            print(f"       🤖2: {result2['decision'].upper()} ({result2['processing_time']:.1f}s)")
        else:
            print(f"       🤖2: ERROR - {result2['error']}")
        
        # Check for agreement
        if result1['success'] and result2['success']:
            agreement = result1['decision'] == result2['decision']
            if agreement:
                print(f"       ✅ AGREE: {result1['decision'].upper()}")
            else:
                print(f"       ⚠️  DISAGREE: {result1['decision'].upper()} vs {result2['decision'].upper()}")
        
        return results
    
    def _extract_criteria(self, result):
        """Extract criteria assessments from screening result."""
        return {
            "participants_lmic": {
                "assessment": result.participants_lmic.assessment,
                "reasoning": result.participants_lmic.reasoning
            },
            "component_a_cash_support": {
                "assessment": result.component_a_cash_support.assessment,
                "reasoning": result.component_a_cash_support.reasoning
            },
            "component_b_productive_assets": {
                "assessment": result.component_b_productive_assets.assessment,
                "reasoning": result.component_b_productive_assets.reasoning
            },
            "relevant_outcomes": {
                "assessment": result.relevant_outcomes.assessment,
                "reasoning": result.relevant_outcomes.reasoning
            },
            "appropriate_study_design": {
                "assessment": result.appropriate_study_design.assessment,
                "reasoning": result.appropriate_study_design.reasoning
            },
            "publication_year_2004_plus": {
                "assessment": result.publication_year_2004_plus.assessment,
                "reasoning": result.publication_year_2004_plus.reasoning
            },
            "completed_study": {
                "assessment": result.completed_study.assessment,
                "reasoning": result.completed_study.reasoning
            }
        }

def analyze_dual_results(results, engine1_name, engine2_name):
    """Analyze the results from dual-engine screening."""
    
    print("\n📊 DUAL-ENGINE ANALYSIS")
    print("=" * 25)
    
    # Basic statistics
    total_papers = len(results)
    both_success = sum(1 for r in results if r['comparison']['engine1_success'] and r['comparison']['engine2_success'])
    agreements = sum(1 for r in results if r['comparison']['agreement'] and r['comparison']['both_success'])
    disagreements = sum(1 for r in results if not r['comparison']['agreement'] and r['comparison']['both_success'])
    
    print(f"📄 Total papers: {total_papers}")
    print(f"✅ Both engines successful: {both_success} ({both_success/total_papers*100:.1f}%)")
    print(f"🤝 Agreements: {agreements} ({agreements/both_success*100:.1f}% of successful pairs)")
    print(f"⚠️  Disagreements: {disagreements} ({disagreements/both_success*100:.1f}% of successful pairs)")
    
    # Decision distribution by engine
    engine1_decisions = defaultdict(int)
    engine2_decisions = defaultdict(int)
    
    for result in results:
        if result['comparison']['engine1_success']:
            engine1_decisions[result['engine1']['decision']] += 1
        if result['comparison']['engine2_success']:
            engine2_decisions[result['engine2']['decision']] += 1
    
    print(f"\n🤖 {engine1_name} decisions:")
    for decision, count in engine1_decisions.items():
        pct = count / sum(engine1_decisions.values()) * 100
        print(f"   {decision}: {count} ({pct:.1f}%)")
    
    print(f"\n🤖 {engine2_name} decisions:")
    for decision, count in engine2_decisions.items():
        pct = count / sum(engine2_decisions.values()) * 100
        print(f"   {decision}: {count} ({pct:.1f}%)")
    
    # Performance metrics
    engine1_times = [r['engine1']['processing_time'] for r in results if r['comparison']['engine1_success']]
    engine2_times = [r['engine2']['processing_time'] for r in results if r['comparison']['engine2_success']]
    
    print(f"\n⚡ Performance comparison:")
    if engine1_times:
        print(f"   {engine1_name}: avg {sum(engine1_times)/len(engine1_times):.1f}s, total {sum(engine1_times)/60:.1f}min")
    if engine2_times:
        print(f"   {engine2_name}: avg {sum(engine2_times)/len(engine2_times):.1f}s, total {sum(engine2_times)/60:.1f}min")
    
    # Disagreement analysis
    if disagreements > 0:
        print(f"\n🔍 Disagreement patterns:")
        disagreement_types = defaultdict(int)
        
        for result in results:
            if not result['comparison']['agreement'] and result['comparison']['both_success']:
                pattern = f"{result['engine1']['decision']} vs {result['engine2']['decision']}"
                disagreement_types[pattern] += 1
        
        for pattern, count in disagreement_types.items():
            pct = count / disagreements * 100
            print(f"   {pattern}: {count} ({pct:.1f}%)")
    
    return {
        'total_papers': total_papers,
        'both_success': both_success,
        'agreements': agreements,
        'disagreements': disagreements,
        'agreement_rate': agreements / both_success * 100 if both_success > 0 else 0,
        'engine1_decisions': dict(engine1_decisions),
        'engine2_decisions': dict(engine2_decisions),
        'engine1_avg_time': sum(engine1_times) / len(engine1_times) if engine1_times else 0,
        'engine2_avg_time': sum(engine2_times) / len(engine2_times) if engine2_times else 0
    }

def dual_screen_papers(input_file, output_file=None, max_papers=None, verbose=False):
    """Enhanced dual-engine screening with checkpointing and parallel processing."""
    
    print("🚀 ENHANCED DUAL-ENGINE PAPER SCREENING")
    print("=" * 38)
    
    # Load configuration
    config_path = "config/config.yaml"
    if not os.path.exists(config_path):
        print("❌ ERROR: config/config.yaml not found")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize checkpoint manager and dual screener
    checkpoint_manager = CheckpointManager()
    dual_screener = EnhancedDualEngineScreener(config, checkpoint_manager)
    print("✅ Enhanced screening engines initialized with parallel processing")
    
    # Load papers
    print(f"\n📄 Loading papers from: {input_file}")
    parser = RISParser()
    
    try:
        papers = parser.parse_file(input_file)
        print(f"   📊 Loaded {len(papers)} papers")
    except Exception as e:
        print(f"❌ ERROR: Failed to parse input file: {e}")
        sys.exit(1)
    
    # Apply max papers limit
    if max_papers and max_papers < len(papers):
        papers = papers[:max_papers]
        print(f"   🔢 Limited to first {max_papers} papers for testing")
    
    # Prepare output file
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/output/dual_screening_{timestamp}.json"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print(f"\n🎯 Starting dual-engine screening...")
    print(f"   📤 Output will be saved to: {output_file}")
    print(f"   🔍 Processing {len(papers)} papers")
    print()
    
    # Generate session ID for checkpointing
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"📋 Session ID: {session_id}")
    
    # Check for existing checkpoint
    checkpoint_data = checkpoint_manager.load_checkpoint(session_id)
    if checkpoint_data:
        print(f"🔄 Resuming from checkpoint with {len(checkpoint_data['results'])} completed papers")
        results = checkpoint_data['results']
        start_index = len(results)
    else:
        results = []
        start_index = 0
    
    # Process papers with checkpointing
    total_start_time = time.time()
    
    try:
        for i in range(start_index, len(papers)):
            paper = papers[i]
            paper_num = i + 1
            
            # Screen with both engines (parallel)
            dual_result = dual_screener.screen_paper_parallel(paper, paper_num, len(papers))
            
            # Analyze agreement
            both_success = dual_result['engine1']['success'] and dual_result['engine2']['success']
            agreement = False
            if both_success:
                agreement = dual_result['engine1']['decision'] == dual_result['engine2']['decision']
            
            # Create combined result
            result_data = {
                "paper_id": paper.paper_id,
                "title": paper.title,
                "authors": paper.authors or [],
                "journal": paper.journal,
                "year": paper.year,
                "abstract": paper.abstract,
                "doi": paper.doi,
                "engine1": dual_result['engine1'],
                "engine2": dual_result['engine2'],
                "comparison": {
                    "both_success": both_success,
                    "engine1_success": dual_result['engine1']['success'],
                    "engine2_success": dual_result['engine2']['success'],
                    "agreement": agreement,
                    "needs_review": not agreement and both_success
                }
            }
            
            results.append(result_data)
            
            # Save checkpoint every 5 papers or on completion
            if (paper_num % 5 == 0) or (paper_num == len(papers)):
                checkpoint_data = {
                    'results': results,
                    'session_id': session_id,
                    'last_processed': paper_num,
                    'total_papers': len(papers),
                    'timestamp': datetime.now().isoformat()
                }
                checkpoint_manager.save_checkpoint(session_id, checkpoint_data)
                print(f"   💾 Checkpoint saved at paper {paper_num}")
            
            # Progress update
            if paper_num % 5 == 0 or paper_num == len(papers):
                progress = (paper_num / len(papers)) * 100
                elapsed = time.time() - total_start_time
                eta = (elapsed / paper_num) * (len(papers) - paper_num) if paper_num > 0 else 0
                print(f"   📊 Progress: {paper_num}/{len(papers)} ({progress:.1f}%) - ETA: {eta/60:.1f}min")
    
    except KeyboardInterrupt:
        print(f"\n⚠️  Interrupted! Progress saved to checkpoint. Resume with session ID: {session_id}")
        raise
    except Exception as e:
        print(f"\n❌ Error occurred! Progress saved to checkpoint: {e}")
        raise
    
    total_time = time.time() - total_start_time
    
    # Clean up checkpoint on successful completion
    checkpoint_manager.cleanup_checkpoint(session_id)
    print(f"✅ Screening completed successfully, checkpoint cleaned up")
    
    # Analyze results
    analysis = analyze_dual_results(
        results, 
        dual_screener.engine1_config.model_name,
        dual_screener.engine2_config.model_name
    )
    
    # Save results
    print(f"\n💾 Saving results...")
    
    output_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_papers": len(papers),
            "processing_time_seconds": round(total_time, 1),
            "engine1_model": dual_screener.engine1_config.model_name,
            "engine2_model": dual_screener.engine2_config.model_name,
            "prompt_version": "optimized"
        },
        "analysis": analysis,
        "results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Results saved to: {output_file}")
    
    # Create summary CSV for easy analysis
    csv_file = output_file.replace('.json', '_summary.csv')
    summary_data = []
    
    for result in results:
        summary_data.append({
            'paper_id': result['paper_id'],
            'title': result['title'][:100],
            'year': result['year'],
            'engine1_decision': result['engine1']['decision'],
            'engine2_decision': result['engine2']['decision'],
            'agreement': result['comparison']['agreement'],
            'needs_review': result['comparison']['needs_review'],
            'engine1_time': result['engine1']['processing_time'],
            'engine2_time': result['engine2']['processing_time']
        })
    
    df = pd.DataFrame(summary_data)
    df.to_csv(csv_file, index=False)
    print(f"   📊 Summary CSV saved to: {csv_file}")
    
    # Final recommendations
    print(f"\n🎯 RECOMMENDATIONS")
    print("=" * 17)
    
    if analysis['agreement_rate'] >= 90:
        print("✅ High agreement rate - both engines are performing consistently")
    elif analysis['agreement_rate'] >= 75:
        print("⚠️  Moderate agreement - some disagreements to investigate")
    else:
        print("❌ Low agreement - significant differences between engines")
    
    faster_engine = "Engine 1" if analysis['engine1_avg_time'] < analysis['engine2_avg_time'] else "Engine 2"
    print(f"⚡ {faster_engine} is faster on average")
    
    disagreement_count = analysis['disagreements']
    if disagreement_count > 0:
        print(f"🔍 {disagreement_count} papers need human review due to disagreements")
        print(f"📄 Estimated review time: {disagreement_count * 0.5:.1f} hours")
    
    return results

def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description="Dual-engine paper screening comparison",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dual_engine_screening.py --input data/input/papers.txt
  python dual_engine_screening.py --input data/input/papers.txt --max-papers 100
  python dual_engine_screening.py --input data/input/papers.txt --output dual_results.json --verbose
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input RIS file with papers to screen"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output JSON file (default: auto-generated in data/output/)"
    )
    
    parser.add_argument(
        "--max-papers",
        type=int,
        help="Maximum number of papers to process (for testing)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed progress for each paper"
    )
    
    args = parser.parse_args()
    
    # Run dual-engine screening
    try:
        dual_screen_papers(
            input_file=args.input,
            output_file=args.output,
            max_papers=args.max_papers,
            verbose=args.verbose
        )
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
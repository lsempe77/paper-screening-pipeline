#!/usr/bin/env python3
"""
Batch-Parallel Dual-Engine Screening Script

Optimized approach:
1. Split papers into batches
2. Process batches in parallel with multiple workers
3. Each worker handles full dual-engine screening for assigned papers
4. Much higher throughput than per-engine parallelization
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
import queue
import math

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from integrated_screener import IntegratedStructuredScreener
from src.models import ModelConfig
from src.parsers import RISParser

class BatchCheckpointManager:
    """Enhanced checkpoint manager for batch processing."""
    
    def __init__(self, checkpoint_dir: str = "data/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
    
    def get_checkpoint_path(self, session_id: str) -> Path:
        """Get checkpoint file path for session."""
        return self.checkpoint_dir / f"batch_screening_{session_id}.pkl"
    
    def save_checkpoint(self, session_id: str, data: Dict):
        """Thread-safe checkpoint saving."""
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

class BatchDualEngineWorker:
    """Worker class that processes a batch of papers with dual engines."""
    
    def __init__(self, config, worker_id: int):
        self.worker_id = worker_id
        self.config = config
        
        # Initialize both screeners for this worker
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
        
        self.screener1 = IntegratedStructuredScreener(self.engine1_config)
        self.screener2 = IntegratedStructuredScreener(self.engine2_config)
    
    def _get_u1_field(self, paper) -> str:
        """Extract U1 field from paper RIS fields."""
        if hasattr(paper, 'ris_fields') and 'U1' in paper.ris_fields:
            u1_value = paper.ris_fields['U1']
            # U1 field can be a list, take first ID
            return u1_value[0] if isinstance(u1_value, list) else u1_value
        return ""
    
    def screen_paper_dual(self, paper, paper_index: int) -> Dict:
        """Screen a single paper with both engines."""
        
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
        
        # Screen with both engines (can be parallel within worker)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(screen_with_engine, self.screener1, "Engine 1")
            future2 = executor.submit(screen_with_engine, self.screener2, "Engine 2")
            
            result1 = future1.result()
            result2 = future2.result()
        
        # Analyze agreement
        both_success = result1['success'] and result2['success']
        agreement = False
        if both_success:
            agreement = result1['decision'] == result2['decision']
        
        # Create combined result
        result_data = {
            "paper_id": paper.paper_id,
            "title": paper.title,
            "authors": paper.authors or [],
            "journal": paper.journal,
            "year": paper.year,
            "abstract": paper.abstract,
            "doi": paper.doi,
            # Extract U1 field from RIS fields if available
            "u1": self._get_u1_field(paper),
            "engine1": result1,
            "engine2": result2,
            "comparison": {
                "both_success": both_success,
                "engine1_success": result1['success'],
                "engine2_success": result2['success'],
                "agreement": agreement,
                "needs_review": not agreement and both_success
            },
            "worker_id": self.worker_id,
            "processed_at": datetime.now().isoformat()
        }
        
        # Progress output
        status = "✅ AGREE" if agreement and both_success else "⚠️ DISAGREE" if both_success else "❌ ERROR"
        if both_success:
            decisions = f"{result1['decision'].upper()} vs {result2['decision'].upper()}"
            times = f"({result1['processing_time']:.1f}s, {result2['processing_time']:.1f}s)"
        else:
            decisions = "ENGINE ERRORS"
            times = ""
        
        print(f"Worker {self.worker_id}: [{paper_index:3d}] {status} - {decisions} {times}")
        
        return result_data
    
    def process_batch(self, papers: List, start_index: int) -> List[Dict]:
        """Process a batch of papers."""
        results = []
        
        for i, paper in enumerate(papers):
            paper_index = start_index + i + 1
            try:
                result = self.screen_paper_dual(paper, paper_index)
                results.append(result)
            except Exception as e:
                print(f"Worker {self.worker_id}: ERROR processing paper {paper_index}: {e}")
                # Add error result
                error_result = {
                    "paper_id": getattr(paper, 'paper_id', f'unknown_{paper_index}'),
                    "title": getattr(paper, 'title', 'Unknown title'),
                    "decision": "error",
                    "reasoning": f"Worker processing error: {str(e)}",
                    "error": str(e),
                    "worker_id": self.worker_id
                }
                results.append(error_result)
        
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

class BatchDualEngineManager:
    """Manages batch-parallel processing of papers."""
    
    def __init__(self, config, num_workers: int = 4, batch_size: int = 5):
        self.config = config
        self.num_workers = num_workers
        self.batch_size = batch_size
        self.checkpoint_manager = BatchCheckpointManager()
        
        print(f"🚀 Batch Manager initialized:")
        print(f"   👷 Workers: {num_workers}")
        print(f"   📦 Batch size: {batch_size}")
        print(f"   🤖 Engine 1: {config['models']['primary']['model_name']}")
        print(f"   🤖 Engine 2: {config['models']['secondary']['model_name']}")
    
    def process_papers_batch_parallel(self, papers: List, session_id: str) -> List[Dict]:
        """Process papers using batch parallelization."""
        
        # Check for existing checkpoint
        checkpoint_data = self.checkpoint_manager.load_checkpoint(session_id)
        if checkpoint_data:
            print(f"🔄 Resuming from checkpoint: {len(checkpoint_data['results'])} papers completed")
            completed_results = checkpoint_data['results']
            start_index = len(completed_results)
            remaining_papers = papers[start_index:]
        else:
            completed_results = []
            start_index = 0
            remaining_papers = papers
        
        if not remaining_papers:
            print("✅ All papers already processed!")
            return completed_results
        
        # Split remaining papers into batches
        batches = []
        for i in range(0, len(remaining_papers), self.batch_size):
            batch = remaining_papers[i:i + self.batch_size]
            batch_start_index = start_index + i
            batches.append((batch, batch_start_index))
        
        print(f"📦 Processing {len(remaining_papers)} papers in {len(batches)} batches")
        
        all_results = completed_results.copy()
        completed_batches = 0
        
        try:
            # Process batches in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                # Submit all batch jobs
                future_to_batch = {}
                
                for batch_idx, (batch_papers, batch_start_idx) in enumerate(batches):
                    worker = BatchDualEngineWorker(self.config, batch_idx % self.num_workers)
                    future = executor.submit(worker.process_batch, batch_papers, batch_start_idx)
                    future_to_batch[future] = (batch_idx, batch_start_idx, len(batch_papers))
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_batch):
                    batch_idx, batch_start_idx, batch_size = future_to_batch[future]
                    
                    try:
                        batch_results = future.result()
                        all_results.extend(batch_results)
                        completed_batches += 1
                        
                        # Save checkpoint after each batch
                        checkpoint_data = {
                            'results': all_results,
                            'session_id': session_id,
                            'completed_batches': completed_batches,
                            'total_batches': len(batches),
                            'timestamp': datetime.now().isoformat()
                        }
                        self.checkpoint_manager.save_checkpoint(session_id, checkpoint_data)
                        
                        progress = (len(all_results) / len(papers)) * 100
                        print(f"📊 Batch {completed_batches}/{len(batches)} complete - Progress: {len(all_results)}/{len(papers)} ({progress:.1f}%)")
                        
                    except Exception as e:
                        print(f"❌ Batch {batch_idx} failed: {e}")
                        # Continue processing other batches
        
        except KeyboardInterrupt:
            print(f"\n⚠️ Interrupted! Progress saved. Completed: {len(all_results)}/{len(papers)} papers")
            raise
        
        # Clean up checkpoint on success
        if len(all_results) >= len(papers):
            self.checkpoint_manager.cleanup_checkpoint(session_id)
            print("✅ All batches completed, checkpoint cleaned up")
        
        return all_results

def analyze_batch_results(results, engine1_name, engine2_name):
    """Analyze batch processing results."""
    
    print(f"\n📊 BATCH PROCESSING ANALYSIS")
    print("=" * 30)
    
    # Basic statistics
    total_papers = len(results)
    both_success = sum(1 for r in results if r.get('comparison', {}).get('both_success', False))
    agreements = sum(1 for r in results if r.get('comparison', {}).get('agreement', False) and r.get('comparison', {}).get('both_success', False))
    disagreements = sum(1 for r in results if not r.get('comparison', {}).get('agreement', False) and r.get('comparison', {}).get('both_success', False))
    
    print(f"📄 Total papers: {total_papers}")
    print(f"✅ Both engines successful: {both_success} ({both_success/total_papers*100:.1f}%)")
    if both_success > 0:
        print(f"🤝 Agreements: {agreements} ({agreements/both_success*100:.1f}%)")
        print(f"⚠️ Disagreements: {disagreements} ({disagreements/both_success*100:.1f}%)")
    
    # Performance metrics
    engine1_times = []
    engine2_times = []
    
    for result in results:
        if result.get('engine1', {}).get('success'):
            engine1_times.append(result['engine1']['processing_time'])
        if result.get('engine2', {}).get('success'):
            engine2_times.append(result['engine2']['processing_time'])
    
    print(f"\n⚡ Performance:")
    if engine1_times:
        avg_time1 = sum(engine1_times) / len(engine1_times)
        print(f"   {engine1_name}: avg {avg_time1:.1f}s per paper")
    if engine2_times:
        avg_time2 = sum(engine2_times) / len(engine2_times)
        print(f"   {engine2_name}: avg {avg_time2:.1f}s per paper")
    
    return {
        'total_papers': total_papers,
        'both_success': both_success,
        'agreements': agreements,
        'disagreements': disagreements,
        'agreement_rate': agreements / both_success * 100 if both_success > 0 else 0,
        'engine1_avg_time': sum(engine1_times) / len(engine1_times) if engine1_times else 0,
        'engine2_avg_time': sum(engine2_times) / len(engine2_times) if engine2_times else 0
    }

def batch_dual_screen_papers(input_file, output_file=None, max_papers=None, num_workers=4, batch_size=5):
    """Main batch-parallel dual-engine screening function."""
    
    print("🚀 BATCH-PARALLEL DUAL-ENGINE SCREENING")
    print("=" * 42)
    
    # Load configuration
    config_path = "config/config.yaml"
    if not os.path.exists(config_path):
        print("❌ ERROR: config/config.yaml not found")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
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
        output_file = f"data/output/batch_dual_screening_{timestamp}.json"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Initialize batch manager
    batch_manager = BatchDualEngineManager(config, num_workers, batch_size)
    
    # Generate session ID
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\n🎯 Starting batch-parallel screening...")
    print(f"   📤 Output: {output_file}")
    print(f"   📋 Session ID: {session_id}")
    
    # Process papers
    start_time = time.time()
    
    try:
        results = batch_manager.process_papers_batch_parallel(papers, session_id)
    except KeyboardInterrupt:
        print(f"\n⚠️ Process interrupted by user")
        return None
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        return None
    
    total_time = time.time() - start_time
    
    # Analyze results
    analysis = analyze_batch_results(
        results, 
        config['models']['primary']['model_name'],
        config['models']['secondary']['model_name']
    )
    
    # Save results
    print(f"\n💾 Saving results...")
    
    output_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_papers": len(papers),
            "processing_time_seconds": round(total_time, 1),
            "num_workers": num_workers,
            "batch_size": batch_size,
            "engine1_model": config['models']['primary']['model_name'],
            "engine2_model": config['models']['secondary']['model_name'],
            "prompt_version": "optimized",
            "session_id": session_id
        },
        "analysis": analysis,
        "results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Results saved to: {output_file}")
    
    # Performance summary
    papers_per_minute = len(papers) / (total_time / 60) if total_time > 0 else 0
    print(f"\n🏆 PERFORMANCE SUMMARY")
    print("=" * 22)
    print(f"⏱️  Total time: {total_time/60:.1f} minutes")
    print(f"⚡ Throughput: {papers_per_minute:.1f} papers/minute")
    print(f"📊 Agreement rate: {analysis['agreement_rate']:.1f}%")
    
    if analysis['disagreements'] > 0:
        print(f"🔍 {analysis['disagreements']} papers need human review")
    
    return results

def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description="Batch-parallel dual-engine paper screening",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_dual_screening.py --input data/input/papers.txt --max-papers 50
  python batch_dual_screening.py --input data/input/papers.txt --workers 8 --batch-size 10
  python batch_dual_screening.py --input data/input/papers.txt --output results.json
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
        "--workers", "-w",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=5,
        help="Papers per batch (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Run batch-parallel screening
    try:
        batch_dual_screen_papers(
            input_file=args.input,
            output_file=args.output,
            max_papers=args.max_papers,
            num_workers=args.workers,
            batch_size=args.batch_size
        )
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
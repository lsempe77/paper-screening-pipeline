#!/usr/bin/env python3
"""
Phase 1 Validation: Test LLM screening on manually labeled papers.

This script validates the integrated screening approach on:
- 600 manually screened papers (s3above, s14above, s20above)
- 160 full-text screened papers (gold standard)
- 73 program-tagged papers

Measures accuracy, false positive/negative rates, and MAYBE rates.
"""

import sys
import json
import yaml
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models import ModelConfig, Paper, ScreeningDecision
from src.parsers import RISParser
from integrated_screener import IntegratedStructuredScreener

class Phase1Validator:
    """Validate LLM screening on manually labeled papers."""
    
    def __init__(self, use_followup_agent: bool = True):
        """Initialize validator."""
        self.use_followup_agent = use_followup_agent
        self.setup_logging()
        self.load_config()
        self.initialize_screener()
        
    def setup_logging(self):
        """Setup logging."""
        print("=" * 70)
        print("🔬 PHASE 1 VALIDATION: Manual Screening Comparison")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
    def load_config(self):
        """Load configuration."""
        config_path = project_root / "config" / "config.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        self.model_config = ModelConfig(
            model_name=self.config['models']['primary']['model_name'],
            api_url="https://openrouter.ai/api/v1",
            api_key=self.config['openrouter']['api_key'],
            provider="openrouter",
            temperature=0.1,
            max_tokens=1500
        )
        print("✅ Configuration loaded")
        print(f"   Model: {self.model_config.model_name}")
        print(f"   Temperature: {self.model_config.temperature}")
        
    def initialize_screener(self):
        """Initialize the integrated screener."""
        self.screener = IntegratedStructuredScreener(
            self.model_config,
            use_followup_agent=self.use_followup_agent
        )
        print("✅ Integrated screener initialized")
        print(f"   Follow-up agent: {'Enabled' if self.use_followup_agent else 'Disabled'}")
        print()
        
    def load_manual_screening_data(self) -> Dict[str, pd.DataFrame]:
        """Load manually screened Excel files."""
        print("📂 Loading manually screened data...")
        
        input_dir = project_root / "data" / "input"
        datasets = {}
        
        files = {
            's3above': 's3above.xlsx',
            's14above': 's14above.xlsx',
            's20above': 's20above.xlsx'
        }
        
        for name, filename in files.items():
            file_path = input_dir / filename
            if file_path.exists():
                df = pd.read_excel(file_path)
                datasets[name] = df
                
                # Count decisions
                if 'include' in df.columns:
                    counts = df['include'].value_counts()
                    print(f"   • {name}: {len(df)} papers")
                    print(f"     {counts.to_dict()}")
                else:
                    print(f"   • {name}: {len(df)} papers (no include column)")
            else:
                print(f"   ⚠️  {name}: Not found")
        
        total = sum(len(df) for df in datasets.values())
        print(f"   📊 Total: {total} manually screened papers")
        print()
        
        return datasets
    
    def load_fulltext_data(self) -> Dict[str, pd.DataFrame]:
        """Load full-text screened papers."""
        print("📂 Loading full-text screened data...")
        
        input_dir = project_root / "data" / "input"
        datasets = {}
        
        files = {
            'ft_included': 'full_text_marl_constanza_included.xlsx',
            'ft_excluded': 'full_text_marl_constanza_excluded.xlsx',
            'ft_maybe': 'full_text_marl_constanza_maybe.xlsx'
        }
        
        for name, filename in files.items():
            file_path = input_dir / filename
            if file_path.exists():
                df = pd.read_excel(file_path)
                datasets[name] = df
                print(f"   • {name}: {len(df)} papers")
        
        total = sum(len(df) for df in datasets.values())
        print(f"   📊 Total: {total} full-text screened papers")
        print()
        
        return datasets
    
    def load_program_tags(self) -> Dict[str, pd.DataFrame]:
        """Load program-tagged papers."""
        print("📂 Loading program-tagged data...")
        
        input_dir = project_root / "data" / "input"
        datasets = {}
        
        files = {
            'programs_included': 'program_tags_included.xlsx',
            'programs_excluded': 'program_tags_excluded.xlsx'
        }
        
        for name, filename in files.items():
            file_path = input_dir / filename
            if file_path.exists():
                df = pd.read_excel(file_path)
                datasets[name] = df
                print(f"   • {name}: {len(df)} papers")
        
        total = sum(len(df) for df in datasets.values())
        print(f"   📊 Total: {total} program-tagged papers")
        print()
        
        return datasets
    
    def excel_row_to_paper(self, row: pd.Series, source: str) -> Paper:
        """Convert Excel row to Paper object."""
        return Paper(
            paper_id=str(row.get('ID', row.get('Item ID', 'unknown'))),
            title=str(row.get('Title', row.get('ShortTitle', ''))),
            year=int(row.get('Year', 0)) if pd.notna(row.get('Year')) else None,
            abstract="",  # Excel files don't have abstracts - will need to match to RIS
            source_file=source
        )
    
    def normalize_decision(self, decision: str) -> str:
        """Normalize human decision labels."""
        decision_lower = str(decision).lower()
        
        if 'include' in decision_lower:
            return 'include'
        elif 'exclude' in decision_lower:
            return 'exclude'
        elif 'maybe' in decision_lower:
            return 'maybe'
        else:
            return 'unknown'
    
    def screen_dataset(self, df: pd.DataFrame, dataset_name: str, 
                      human_decision_col: str = 'include') -> List[Dict[str, Any]]:
        """Screen papers from a DataFrame."""
        print(f"🔍 Screening {dataset_name} ({len(df)} papers)...")
        print(f"   Human decisions in column: '{human_decision_col}'")
        
        results = []
        errors = 0
        
        for idx, row in df.iterrows():
            paper = self.excel_row_to_paper(row, dataset_name)
            
            # Get human decision if available
            human_decision = None
            if human_decision_col in df.columns:
                human_decision = self.normalize_decision(row[human_decision_col])
            
            print(f"   📄 {idx+1}/{len(df)}: {paper.title[:60]}...")
            print(f"      Human: {human_decision if human_decision else 'N/A'}", end=" ")
            
            try:
                start_time = time.time()
                result = self.screener.screen_paper(paper)
                processing_time = time.time() - start_time
                
                ai_decision = result.final_decision.value
                
                # Check agreement
                agreement = "N/A"
                if human_decision and human_decision != 'unknown':
                    agreement = "✅" if ai_decision == human_decision else "❌"
                
                print(f"→ AI: {ai_decision.upper()} {agreement} ({processing_time:.2f}s)")
                
                result_data = {
                    "paper_id": paper.paper_id,
                    "title": paper.title,
                    "year": paper.year,
                    "dataset": dataset_name,
                    "human_decision": human_decision,
                    "ai_decision": ai_decision,
                    "agreement": agreement != "❌" if agreement != "N/A" else None,
                    "decision_reasoning": result.decision_reasoning,
                    "processing_time": processing_time,
                    "criteria_counts": {
                        "YES": sum(1 for attr in ['participants_lmic', 'component_a_cash_support',
                                                   'component_b_productive_assets', 'relevant_outcomes',
                                                   'appropriate_study_design', 'publication_year_2004_plus',
                                                   'completed_study']
                                   if hasattr(result, attr) and getattr(result, attr).assessment == "YES"),
                        "NO": sum(1 for attr in ['participants_lmic', 'component_a_cash_support',
                                                  'component_b_productive_assets', 'relevant_outcomes',
                                                  'appropriate_study_design', 'publication_year_2004_plus',
                                                  'completed_study']
                                  if hasattr(result, attr) and getattr(result, attr).assessment == "NO"),
                        "UNCLEAR": sum(1 for attr in ['participants_lmic', 'component_a_cash_support',
                                                       'component_b_productive_assets', 'relevant_outcomes',
                                                       'appropriate_study_design', 'publication_year_2004_plus',
                                                       'completed_study']
                                       if hasattr(result, attr) and getattr(result, attr).assessment == "UNCLEAR")
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                results.append(result_data)
                
            except Exception as e:
                errors += 1
                print(f"❌ Error: {e}")
                results.append({
                    "paper_id": paper.paper_id,
                    "title": paper.title,
                    "dataset": dataset_name,
                    "human_decision": human_decision,
                    "ai_decision": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        print(f"   ✅ Completed with {errors} errors")
        print()
        
        return results
    
    def analyze_results(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze screening results and calculate metrics."""
        print("=" * 70)
        print("📊 ANALYSIS RESULTS")
        print("=" * 70)
        print()
        
        analysis = {
            "summary": {},
            "accuracy_metrics": {},
            "decision_distribution": {},
            "confusion_matrix": {},
            "performance": {}
        }
        
        # Filter results with human labels
        labeled_results = [r for r in all_results if r.get("human_decision") and r["human_decision"] != "unknown"]
        
        # Summary
        total_papers = len(all_results)
        labeled_papers = len(labeled_results)
        errors = len([r for r in all_results if r.get("ai_decision") == "error"])
        
        analysis["summary"] = {
            "total_papers": total_papers,
            "labeled_papers": labeled_papers,
            "unlabeled_papers": total_papers - labeled_papers,
            "errors": errors,
            "success_rate": (total_papers - errors) / total_papers if total_papers > 0 else 0
        }
        
        print(f"📋 Summary:")
        print(f"   Total papers screened: {total_papers}")
        print(f"   Papers with human labels: {labeled_papers}")
        print(f"   Errors: {errors}")
        print()
        
        # Accuracy metrics (only for labeled data)
        if labeled_results:
            agreements = [r for r in labeled_results if r.get("agreement") == True]
            accuracy = len(agreements) / len(labeled_results)
            
            # False positives: AI says include, human says exclude
            false_positives = [r for r in labeled_results 
                              if r["ai_decision"] == "include" and r["human_decision"] == "exclude"]
            
            # False negatives: AI says exclude, human says include
            false_negatives = [r for r in labeled_results 
                              if r["ai_decision"] == "exclude" and r["human_decision"] == "include"]
            
            # Calculate rates
            fp_rate = len(false_positives) / len(labeled_results) if labeled_results else 0
            fn_rate = len(false_negatives) / len(labeled_results) if labeled_results else 0
            
            analysis["accuracy_metrics"] = {
                "accuracy": accuracy,
                "agreement_count": len(agreements),
                "disagreement_count": len(labeled_results) - len(agreements),
                "false_positives": len(false_positives),
                "false_negatives": len(false_negatives),
                "false_positive_rate": fp_rate,
                "false_negative_rate": fn_rate
            }
            
            print(f"🎯 Accuracy Metrics:")
            print(f"   Overall Accuracy: {accuracy:.1%}")
            print(f"   Agreements: {len(agreements)}/{len(labeled_results)}")
            print(f"   False Positives: {len(false_positives)} ({fp_rate:.2%})")
            print(f"   False Negatives: {len(false_negatives)} ({fn_rate:.2%})")
            
            if false_negatives:
                print(f"\n   ⚠️  FALSE NEGATIVES (Critical!):")
                for fn in false_negatives:
                    print(f"      • {fn['paper_id']}: {fn['title'][:60]}")
            print()
        
        # Decision distribution
        ai_decisions = defaultdict(int)
        human_decisions = defaultdict(int)
        
        for r in all_results:
            ai_decisions[r.get("ai_decision", "unknown")] += 1
            if r.get("human_decision"):
                human_decisions[r["human_decision"]] += 1
        
        analysis["decision_distribution"] = {
            "ai_decisions": dict(ai_decisions),
            "human_decisions": dict(human_decisions)
        }
        
        print(f"📊 Decision Distribution:")
        print(f"   AI Decisions:")
        for decision, count in ai_decisions.items():
            pct = count / total_papers * 100 if total_papers > 0 else 0
            print(f"      {decision.upper()}: {count} ({pct:.1f}%)")
        
        if human_decisions:
            print(f"   Human Decisions:")
            for decision, count in human_decisions.items():
                pct = count / labeled_papers * 100 if labeled_papers > 0 else 0
                print(f"      {decision.upper()}: {count} ({pct:.1f}%)")
        print()
        
        # Confusion matrix (for labeled data)
        if labeled_results:
            confusion = defaultdict(lambda: defaultdict(int))
            for r in labeled_results:
                confusion[r["human_decision"]][r["ai_decision"]] += 1
            
            analysis["confusion_matrix"] = {k: dict(v) for k, v in confusion.items()}
            
            print(f"🔲 Confusion Matrix:")
            print(f"                  AI→")
            print(f"   Human ↓     Include  Exclude  Maybe")
            for human_dec in ['include', 'exclude', 'maybe']:
                if human_dec in confusion:
                    inc = confusion[human_dec].get('include', 0)
                    exc = confusion[human_dec].get('exclude', 0)
                    may = confusion[human_dec].get('maybe', 0)
                    print(f"   {human_dec.capitalize():10s}  {inc:7d}  {exc:7d}  {may:5d}")
            print()
        
        # Performance metrics
        total_time = sum(r.get("processing_time", 0) for r in all_results)
        avg_time = total_time / total_papers if total_papers > 0 else 0
        
        analysis["performance"] = {
            "total_time_seconds": total_time,
            "average_time_per_paper": avg_time,
            "papers_per_minute": 60 / avg_time if avg_time > 0 else 0
        }
        
        print(f"⏱️  Performance:")
        print(f"   Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
        print(f"   Average per paper: {avg_time:.2f}s")
        print(f"   Throughput: {60/avg_time:.1f} papers/minute")
        print()
        
        return analysis
    
    def save_results(self, results: List[Dict[str, Any]], analysis: Dict[str, Any]):
        """Save results to JSON files."""
        output_dir = project_root / "data" / "output"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = output_dir / f"phase1_validation_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"✅ Results saved: {results_file}")
        
        # Save analysis
        analysis_file = output_dir / f"phase1_validation_analysis_{timestamp}.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"✅ Analysis saved: {analysis_file}")
        
        # Save summary report
        report_file = output_dir / f"phase1_validation_report_{timestamp}.md"
        self.save_markdown_report(report_file, analysis)
        print(f"✅ Report saved: {report_file}")
        print()
    
    def save_markdown_report(self, filepath: Path, analysis: Dict[str, Any]):
        """Save markdown report."""
        with open(filepath, 'w') as f:
            f.write("# Phase 1 Validation Report\n\n")
            f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Summary\n\n")
            summary = analysis["summary"]
            f.write(f"- Total papers: {summary['total_papers']}\n")
            f.write(f"- Labeled papers: {summary['labeled_papers']}\n")
            f.write(f"- Errors: {summary['errors']}\n")
            f.write(f"- Success rate: {summary['success_rate']:.1%}\n\n")
            
            if "accuracy_metrics" in analysis:
                f.write("## Accuracy\n\n")
                acc = analysis["accuracy_metrics"]
                f.write(f"- **Overall Accuracy**: {acc['accuracy']:.1%}\n")
                f.write(f"- Agreements: {acc['agreement_count']}\n")
                f.write(f"- False Positives: {acc['false_positives']} ({acc['false_positive_rate']:.2%})\n")
                f.write(f"- False Negatives: {acc['false_negatives']} ({acc['false_negative_rate']:.2%})\n\n")
            
            f.write("## Performance\n\n")
            perf = analysis["performance"]
            f.write(f"- Average time: {perf['average_time_per_paper']:.2f}s per paper\n")
            f.write(f"- Throughput: {perf['papers_per_minute']:.1f} papers/minute\n\n")
    
    def run_validation(self):
        """Run complete validation."""
        all_results = []
        
        # Load and screen manual data
        manual_data = self.load_manual_screening_data()
        for name, df in manual_data.items():
            results = self.screen_dataset(df, name, human_decision_col='include')
            all_results.extend(results)
        
        # Load and screen full-text data  
        fulltext_data = self.load_fulltext_data()
        for name, df in fulltext_data.items():
            # Determine expected decision from filename
            expected = 'include' if 'included' in name else 'exclude' if 'excluded' in name else 'maybe'
            
            # Add expected decision to DataFrame for comparison
            df['include'] = expected
            
            results = self.screen_dataset(df, name, human_decision_col='include')
            all_results.extend(results)
        
        # Analyze results
        analysis = self.analyze_results(all_results)
        
        # Save results
        self.save_results(all_results, analysis)
        
        print("=" * 70)
        print("✅ PHASE 1 VALIDATION COMPLETE")
        print("=" * 70)
        
        return all_results, analysis


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 1 Validation")
    parser.add_argument('--no-followup', action='store_true', 
                       help='Disable follow-up agent')
    parser.add_argument('--max-papers', type=int,
                       help='Limit number of papers to test')
    
    args = parser.parse_args()
    
    validator = Phase1Validator(use_followup_agent=not args.no_followup)
    results, analysis = validator.run_validation()
    
    # Print final summary
    if "accuracy_metrics" in analysis:
        acc = analysis["accuracy_metrics"]
        print(f"\n🎯 Final Accuracy: {acc['accuracy']:.1%}")
        print(f"❌ False Negatives: {acc['false_negatives']}")
        print(f"⚠️  False Positives: {acc['false_positives']}")


if __name__ == "__main__":
    main()

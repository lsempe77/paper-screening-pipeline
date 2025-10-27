#!/usr/bin/env python3
"""
Paper Screening Pipeline - Main Entry Point

A robust system for automated screening of academic papers using AI models
via OpenRouter API for systematic reviews and meta-analyses.

Usage:
    python main.py --config config/config.yaml --input data/input --output data/output
    python main.py --help
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models import ModelConfig, ScreeningBatch, Paper, ScreeningDecision
from src.parsers import RISParser, parse_multiple_files
from src.screeners import OpenRouterScreener, PromptManager
from src.evaluators import ScreeningEvaluator, QualityChecker
from src.utils import (
from integrated_screener import IntegratedStructuredScreener
from integrated_screener import IntegratedStructuredScreener
    setup_logging, load_config, save_json, generate_batch_id,
    estimate_cost, ProgressTracker, format_duration
)


class PaperScreeningPipeline:
    """Main pipeline for automated paper screening."""
    
    def __init__(self, config_path: str):
        """Initialize pipeline with configuration."""
        self.config = load_config(config_path)
        self.logger = setup_logging(
            log_dir=self.config['paths']['logs_dir'],
            log_level=self.config['logging']['level']
        )
        
        # Initialize components
        self.parser = RISParser()
        self.evaluator = ScreeningEvaluator()
        self.quality_checker = QualityChecker()
        
        self.logger.info("Pipeline initialized successfully")
    
    def run_screening(self, input_dir: str, output_dir: str, 
                     model_name: str = "primary", prompt_file: Optional[str] = None):
        """Run complete screening pipeline."""
        
        self.logger.info(f"Starting screening pipeline")
        self.logger.info(f"Input directory: {input_dir}")
        self.logger.info(f"Output directory: {output_dir}")
        
        start_time = datetime.now()
        
        try:
            # 1. Load gold standard examples (included/excluded papers)
            training_examples = self._load_training_examples(input_dir)
            
            # 2. Parse RIS files to be screened
            papers = self._parse_input_files(input_dir, exclude_training=True)
            if not papers:
                self.logger.error("No papers found to screen")
                return
            
            # 3. Load and enhance prompt template with examples
            prompt_template = self._load_prompt_template(prompt_file, training_examples)
            
            # 4. Set up model
            model_config = self._get_model_config(model_name)
            screener = OpenRouterScreener(model_config)
            
            # 5. Estimate costs
            cost_estimate = self._estimate_and_check_costs(papers, model_config.model_name)
            
            # 6. Create batch
            batch_id = generate_batch_id()
            batch = ScreeningBatch(
                batch_id=batch_id,
                papers=papers,
                model_config=model_config.__dict__,
                prompt_version=prompt_file or "default"
            )
            
            # 6. Run screening
            self.logger.info(f"Starting screening of {len(papers)} papers")
            results = self._run_screening_batch(screener, papers, prompt_template)
            
            # 7. Add results to batch
            for result in results:
                batch.add_result(result)
            
            # 8. Evaluate and save results
            self._save_results(batch, output_dir)
            
            # 9. Generate summary
            self._generate_summary(batch, cost_estimate, start_time)
            
            self.logger.info("Screening pipeline completed successfully")
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            raise
    
    def run_validation(self, input_dir: str, model_name: str = "primary", prompt_file: Optional[str] = None):
        """Run validation mode using holdout included/excluded papers."""
        
        self.logger.info("Starting validation mode")
        start_time = datetime.now()
        
        try:
            # 1. Load all included/excluded papers
            input_path = Path(input_dir)
            
            # Load included papers
            included_file = input_path / 'included.txt'
            excluded_file = input_path / 'excluded.txt'
            
            if not included_file.exists() or not excluded_file.exists():
                raise FileNotFoundError("included.txt or excluded.txt not found for validation")
            
            all_included = parse_multiple_files([str(included_file)])
            all_excluded = parse_multiple_files([str(excluded_file)])
            
            self.logger.info(f"Loaded {len(all_included)} included and {len(all_excluded)} excluded papers")
            
            # 2. Split into training (first 3) and test (remaining)
            training_included = all_included[:3]  # Only 3 positive examples
            training_excluded = []  # No negative examples
            test_included = all_included[3:]
            test_excluded = all_excluded  # Test on all excluded papers
            
            test_papers = test_included + test_excluded
            
            if not test_papers:
                print("No test papers available for validation (need more than 3 included papers)")
                return
            
            print(f"\nValidation Setup:")
            print(f"Training examples: {len(training_included)} included (positive examples only)")
            print(f"Test papers: {len(test_included)} included, {len(test_excluded)} excluded")
            print(f"Total test papers: {len(test_papers)}")
            
            # 3. Create training examples dict
            training_examples = {
                'included': training_included,
                'excluded': training_excluded  # Empty list
            }
            
            # 4. Load prompt with training examples
            prompt_template = self._load_prompt_template(prompt_file, training_examples)
            
            # 5. Set up model
            model_config = self._get_model_config(model_name)
            screener = OpenRouterScreener(model_config)
            
            # 6. Estimate cost
            cost_estimate = estimate_cost(len(test_papers), model_config.model_name)
            print(f"\nEstimated cost for validation: ${cost_estimate['estimated_cost_usd']:.2f}")
            
            proceed = input("Proceed with validation? (y/n): ")
            if proceed.lower() != 'y':
                print("Validation cancelled")
                return
            
            # 7. Screen test papers
            print(f"\nScreening {len(test_papers)} test papers...")
            results = screener.screen_batch(test_papers, prompt_template)
            
            # 8. Create gold standard for comparison
            gold_standard = {}
            for paper in test_included:
                gold_standard[paper.paper_id] = ScreeningDecision.INCLUDE
            for paper in test_excluded:
                gold_standard[paper.paper_id] = ScreeningDecision.EXCLUDE
            
            # 9. Evaluate results
            evaluator = ScreeningEvaluator()
            comparison = evaluator.compare_with_gold_standard(results, gold_standard)
            
            # 10. Display results
            self._display_validation_results(comparison, results, test_included, test_excluded)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Validation completed in {format_duration(elapsed)}")
            
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            raise
    
    def _display_validation_results(self, comparison: Dict, results: List, 
                                  test_included_papers: List[Paper], test_excluded_papers: List[Paper]):
        """Display validation results with proper confusion matrix and error analysis."""
        
        print(f"\n" + "="*80)
        print("VALIDATION RESULTS")
        print("="*80)
        
        true_included = len(test_included_papers)
        true_excluded = len(test_excluded_papers)
        
        print(f"\nTest Set:")
        print(f"  True Included: {true_included}")
        print(f"  True Excluded: {true_excluded}")
        print(f"  Total: {comparison['total_compared']}")
        
        print(f"\nOverall Performance:")
        print(f"  Accuracy: {comparison['accuracy']:.1%}")
        print(f"  Precision: {comparison['precision']:.1%}")
        print(f"  Recall: {comparison['recall']:.1%}")
        print(f"  F1-Score: {comparison['f1_score']:.1%}")
        
        cm = comparison['confusion_matrix']
        print(f"\nConfusion Matrix:")
        print(f"  True Positives (Correctly Included): {cm['true_positive']}")
        print(f"  False Positives (Incorrectly Included): {cm['false_positive']}")
        print(f"  True Negatives (Correctly Excluded): {cm['true_negative']}")
        print(f"  False Negatives (Incorrectly Excluded): {cm['false_negative']}")
        
        # Create paper lookup dictionaries
        included_papers_dict = {p.paper_id: p for p in test_included_papers}
        excluded_papers_dict = {p.paper_id: p for p in test_excluded_papers}
        
        # Find misclassified papers
        false_positives = []  # Should be excluded but AI said include
        false_negatives = []  # Should be included but AI said exclude
        
        for result in results:
            if result.paper_id in excluded_papers_dict and result.decision == ScreeningDecision.INCLUDE:
                false_positives.append((result, excluded_papers_dict[result.paper_id]))
            elif result.paper_id in included_papers_dict and result.decision == ScreeningDecision.EXCLUDE:
                false_negatives.append((result, included_papers_dict[result.paper_id]))
        
        # Error Analysis
        print(f"\nDetailed Error Analysis:")
        
        if false_positives:
            print(f"\n❌ FALSE POSITIVES ({len(false_positives)} papers incorrectly INCLUDED):")
            print("   These should have been EXCLUDED but AI said INCLUDE:")
            for i, (result, paper) in enumerate(false_positives[:5], 1):  # Show max 5
                print(f"\n   {i}. Paper: {paper.title[:80]}...")
                print(f"      Authors: {'; '.join(paper.authors[:3])}...")
                print(f"      Year: {paper.year}, Journal: {paper.journal}")
                print(f"      AI Reasoning: {result.reasoning[:150]}...")
                print(f"      Abstract: {paper.abstract[:200]}...")
        else:
            print(f"\n✅ No False Positives - AI didn't incorrectly include any papers!")
        
        if false_negatives:
            print(f"\n❌ FALSE NEGATIVES ({len(false_negatives)} papers incorrectly EXCLUDED):")
            print("   These should have been INCLUDED but AI said EXCLUDE:")
            for i, (result, paper) in enumerate(false_negatives[:5], 1):  # Show max 5
                print(f"\n   {i}. Paper: {paper.title[:80]}...")
                print(f"      Authors: {'; '.join(paper.authors[:3])}...")
                print(f"      Year: {paper.year}, Journal: {paper.journal}")
                print(f"      AI Reasoning: {result.reasoning[:150]}...")
                print(f"      Abstract: {paper.abstract[:200]}...")
        else:
            print(f"\n✅ No False Negatives - AI didn't miss any papers that should be included!")
        
        # Summary insights
        print(f"\n" + "="*80)
        print("KEY INSIGHTS:")
        
        if not false_positives and not false_negatives:
            print("🎯 PERFECT SCREENING: AI made no classification errors!")
        else:
            if false_positives:
                print(f"⚠️  {len(false_positives)} papers need manual review (AI was too inclusive)")
            if false_negatives:
                print(f"⚠️  {len(false_negatives)} papers were missed (AI was too restrictive)")
        
        total_errors = len(false_positives) + len(false_negatives)
        print(f"📊 Error rate: {total_errors}/{true_included + true_excluded} = {total_errors/(true_included + true_excluded)*100:.1f}%")
        
        print("="*80)
    
    def _parse_input_files(self, input_dir: str, exclude_training: bool = False) -> list:
        """Parse all RIS files in input directory."""
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Find all .txt files (RIS files)
        ris_files = list(input_path.glob("*.txt"))
        
        if exclude_training:
            # Exclude training files
            training_files = {'included.txt', 'excluded.txt'}
            ris_files = [f for f in ris_files if f.name not in training_files]
        
        if not ris_files:
            raise FileNotFoundError(f"No .txt files found in {input_dir}")
        
        self.logger.info(f"Found {len(ris_files)} RIS files to parse")
        
        # Parse all files
        papers = parse_multiple_files([str(f) for f in ris_files])
        
        self.logger.info(f"Parsed {len(papers)} papers from RIS files")
        
        return papers
    
    def _load_training_examples(self, input_dir: str) -> Dict[str, List[Paper]]:
        """Load gold standard included papers as training examples (exclude excluded papers)."""
        input_path = Path(input_dir)
        training_examples = {'included': [], 'excluded': []}
        
        # Load included papers only
        included_file = input_path / 'included.txt'
        if included_file.exists():
            try:
                included_papers = parse_multiple_files([str(included_file)])
                training_examples['included'] = included_papers[:3]  # Use first 3 as examples
                self.logger.info(f"Loaded {len(included_papers)} included papers ({len(training_examples['included'])} as positive examples)")
            except Exception as e:
                self.logger.warning(f"Could not load included papers: {e}")
        
        # Don't load excluded papers for training
        self.logger.info("Using only positive (included) examples for training")
        
        return training_examples
    
    def _load_prompt_template(self, prompt_file: Optional[str] = None, training_examples: Optional[Dict[str, List[Paper]]] = None) -> str:
        """Load prompt template from file or use default, enhanced with training examples."""
        if prompt_file:
            prompt_path = Path(self.config['paths']['prompts_dir']) / prompt_file
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    template = f.read()
                self.logger.info(f"Loaded prompt template: {prompt_file}")
            else:
                self.logger.warning(f"Prompt file not found: {prompt_path}")
                template = PromptManager.get_basic_screening_prompt()
        else:
            # Use default impact evaluation prompt
            prompt_path = Path(self.config['paths']['prompts_dir']) / "impact_evaluation_screening.txt"
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    template = f.read()
                self.logger.info("Using default impact evaluation screening prompt")
            else:
                template = PromptManager.get_basic_screening_prompt()
                self.logger.info("Using basic fallback prompt")
        
        # Add training examples if available
        if training_examples and (training_examples['included'] or training_examples['excluded']):
            template = self._enhance_prompt_with_examples(template, training_examples)
            self.logger.info(f"Enhanced prompt with {len(training_examples['included'])} included and {len(training_examples['excluded'])} excluded examples")
        
        return template
    
    def _enhance_prompt_with_examples(self, template: str, training_examples: Dict[str, List[Paper]]) -> str:
        """Add few-shot examples to the prompt template (only positive examples)."""
        examples_section = "\n\n## TRAINING EXAMPLES:\n\nHere are examples of papers that should be INCLUDED:\n\n"
        
        # Add included examples only
        if training_examples['included']:
            examples_section += "### INCLUDED PAPERS (Good Examples):\n\n"
            for i, paper in enumerate(training_examples['included'], 1):
                examples_section += f"**Example {i} - INCLUDE:**\n"
                examples_section += f"- Title: {paper.title}\n"
                examples_section += f"- Abstract: {paper.abstract[:300]}{'...' if len(paper.abstract) > 300 else ''}\n"
                examples_section += f"- Decision: INCLUDE\n"
                examples_section += f"- Why: This paper describes a graduation program with both required components\n\n"
        
        examples_section += "These examples show papers that clearly meet the graduation program criteria. Use these as your reference for what TO INCLUDE.\n\n"
        
        # Insert examples before the "RESPONSE FORMAT" section
        if "## RESPONSE FORMAT:" in template:
            parts = template.split("## RESPONSE FORMAT:")
            enhanced_template = parts[0] + examples_section + "## RESPONSE FORMAT:" + parts[1]
        else:
            # Fallback: add at the end before instructions
            enhanced_template = template + "\n" + examples_section
        
        return enhanced_template
    
    def _get_model_config(self, model_name: str) -> ModelConfig:
        """Get model configuration."""
        if model_name not in self.config['models']:
            raise ValueError(f"Model '{model_name}' not found in configuration")
        
        model_conf = self.config['models'][model_name]
        
        return ModelConfig(
            provider=model_conf['provider'],
            model_name=model_conf['model_name'],
            temperature=model_conf['temperature'],
            max_tokens=model_conf['max_tokens'],
            api_key=self.config['openrouter']['api_key'],
            api_url=self.config['openrouter']['api_url'],
            max_retries=model_conf['max_retries'],
            retry_delay=model_conf['retry_delay']
        )
    
    def _estimate_and_check_costs(self, papers: list, model_name: str) -> dict:
        """Estimate costs and check against limits."""
        cost_estimate = estimate_cost(len(papers), model_name)
        
        if self.config['cost_control']['enable_cost_estimation']:
            max_cost = self.config['cost_control']['max_estimated_cost_usd']
            warn_cost = self.config['cost_control']['warn_at_cost_usd']
            
            if cost_estimate['estimated_cost_usd'] > max_cost:
                raise ValueError(
                    f"Estimated cost ${cost_estimate['estimated_cost_usd']:.2f} "
                    f"exceeds maximum ${max_cost:.2f}"
                )
            elif cost_estimate['estimated_cost_usd'] > warn_cost:
                self.logger.warning(
                    f"Estimated cost ${cost_estimate['estimated_cost_usd']:.2f} "
                    f"exceeds warning threshold ${warn_cost:.2f}"
                )
        
        self.logger.info(f"Estimated cost: ${cost_estimate['estimated_cost_usd']:.2f}")
        return cost_estimate
    
    def _run_screening_batch(self, screener, papers, prompt_template) -> list:
        """Run screening on batch of papers with progress tracking."""
        
        def progress_callback(current, total, result):
            self.logger.debug(
                f"Screened paper {current}/{total}: "
                f"{result.paper_id} -> {result.decision.value} "
                f"(confidence: {result.confidence_score:.2f})"
            )
        
        # Set up progress tracker
        tracker = ProgressTracker(len(papers), "Screening papers")
        
        def enhanced_callback(current, total, result):
            progress_callback(current, total, result)
            tracker.update()
        
        return screener.screen_batch(papers, prompt_template, enhanced_callback)
    
    def _save_results(self, batch, output_dir: str):
        """Save screening results in multiple formats."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"screening_results_{batch.batch_id}_{timestamp}"
        
        # Save JSON results
        json_path = output_path / f"{base_filename}.json"
        save_json({
            "batch_info": {
                "batch_id": batch.batch_id,
                "created_at": batch.created_at.isoformat(),
                "total_papers": batch.total_papers,
                "completed_papers": batch.completed_papers,
                "model_config": batch.model_config,
                "prompt_version": batch.prompt_version
            },
            "results": [
                {
                    "paper_id": r.paper_id,
                    "decision": r.decision.value,
                    "confidence_score": r.confidence_score,
                    "reasoning": r.reasoning,
                    "model_used": r.model_used,
                    "timestamp": r.timestamp.isoformat(),
                    "processing_time": r.processing_time
                }
                for r in batch.results
            ]
        }, str(json_path))
        
        # Save CSV for review
        csv_path = output_path / f"{base_filename}.csv"
        self.evaluator.export_results_to_csv(
            batch.results, batch.papers, str(csv_path)
        )
        
        self.logger.info(f"Results saved to {json_path} and {csv_path}")
    
    def _generate_summary(self, batch, cost_estimate, start_time):
        """Generate and log summary of screening run."""
        duration = (datetime.now() - start_time).total_seconds()
        
        metrics = self.evaluator.calculate_metrics(batch.results)
        quality = self.quality_checker.check_consistency(batch.results)
        
        self.logger.info("=== SCREENING SUMMARY ===")
        self.logger.info(f"Batch ID: {batch.batch_id}")
        self.logger.info(f"Duration: {format_duration(duration)}")
        self.logger.info(f"Total papers: {metrics['total_papers']}")
        self.logger.info(f"Included: {metrics['included']} ({metrics['inclusion_rate']:.1f}%)")
        self.logger.info(f"Excluded: {metrics['excluded']} ({metrics['exclusion_rate']:.1f}%)")
        self.logger.info(f"Uncertain: {metrics['uncertain']} ({metrics['uncertainty_rate']:.1f}%)")
        self.logger.info(f"Average confidence: {metrics['average_confidence']:.2f}")
        self.logger.info(f"Low confidence papers: {metrics['low_confidence_count']}")
        self.logger.info(f"Quality score: {quality['quality_score']}/100")
        self.logger.info(f"Estimated cost: ${cost_estimate['estimated_cost_usd']:.2f}")
        
        if quality['issues']:
            self.logger.warning("Quality issues detected:")
            for issue in quality['issues']:
                self.logger.warning(f"  - {issue}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Paper Screening Pipeline for Systematic Reviews"
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config/config.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--input', '-i',
        default='data/input',
        help='Input directory containing RIS files'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='data/output',
        help='Output directory for results'
    )
    
    parser.add_argument(
        '--model', '-m',
        default='primary',
        help='Model configuration to use (primary, secondary, premium)'
    )
    
    parser.add_argument(
        '--prompt', '-p',
        help='Prompt template file to use'
    )
    
    parser.add_argument(
        '--validate', 
        action='store_true',
        help='Run validation mode using remaining included/excluded papers as test set'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Parse files and estimate costs without running screening'
    )
    
    args = parser.parse_args()
    
    try:
        pipeline = PaperScreeningPipeline(args.config)
        
        if args.validate:
            # Run validation mode
            pipeline.run_validation(args.input, args.model, args.prompt)
        elif args.dry_run:
            # Load training examples and papers to be screened (excluding training)
            training_examples = pipeline._load_training_examples(args.input)
            papers = pipeline._parse_input_files(args.input, exclude_training=True)
            model_config = pipeline._get_model_config(args.model)
            cost_estimate = estimate_cost(len(papers), model_config.model_name)
            
            print(f"Dry run results:")
            print(f"Training examples loaded: {len(training_examples['included'])} included, {len(training_examples['excluded'])} excluded")
            print(f"Papers to be screened: {len(papers)}")
            print(f"Model: {model_config.model_name}")
            print(f"Estimated cost: ${cost_estimate['estimated_cost_usd']:.2f}")
            print(f"Estimated tokens: {cost_estimate['estimated_tokens']:,}")
        else:
            pipeline.run_screening(
                input_dir=args.input,
                output_dir=args.output,
                model_name=args.model,
                prompt_file=args.prompt
            )
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Production deployment script for paper screening pipeline.
Simple interface for running the optimized screening system.
"""

import sys
import os
import json
import time
import yaml
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from integrated_screener import IntegratedStructuredScreener
from src.models import ModelConfig
from src.parsers import RISParser

def load_config():
    """Load configuration from config.yaml."""
    
    config_path = "config/config.yaml"
    
    if not os.path.exists(config_path):
        print("❌ ERROR: config/config.yaml not found")
        print("   📝 Please copy config/config.example.yaml to config/config.yaml")
        print("   🔑 And add your OpenRouter API key")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate API key
    if not config.get('openrouter', {}).get('api_key'):
        print("❌ ERROR: OpenRouter API key not found in config")
        print("   🔑 Please add your API key to config/config.yaml")
        sys.exit(1)
    
    return config

def screen_papers(input_file, output_file=None, max_papers=None, verbose=False):
    """Screen papers from RIS file."""
    
    print("🚀 PAPER SCREENING PIPELINE - PRODUCTION")
    print("=" * 41)
    
    # Load configuration
    config = load_config()
    print("✅ Configuration loaded")
    
    # Create model config
    model_config = ModelConfig(
        model_name=config['models']['primary']['model_name'],
        api_url="https://openrouter.ai/api/v1",
        api_key=config['openrouter']['api_key'],
        provider="openrouter",
        temperature=0.1,
        max_tokens=1500
    )
    print(f"✅ Using model: {model_config.model_name}")
    
    # Initialize screener with optimized prompt
    screener = IntegratedStructuredScreener(model_config)
    print("✅ Screener initialized with optimized prompt")
    
    # Load papers
    print(f"\n📄 Loading papers from: {input_file}")
    parser = RISParser()
    
    try:
        papers = parser.parse_file(input_file)
        print(f"   📊 Loaded {len(papers)} papers")
    except FileNotFoundError:
        print(f"❌ ERROR: Input file not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: Failed to parse input file: {e}")
        sys.exit(1)
    
    # Apply max papers limit if specified
    if max_papers and max_papers < len(papers):
        papers = papers[:max_papers]
        print(f"   🔢 Limited to first {max_papers} papers for testing")
    
    # Prepare output file
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"data/output/screening_results_{timestamp}.json"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    print(f"\n🎯 Starting screening process...")
    print(f"   📤 Output will be saved to: {output_file}")
    print(f"   🔍 Processing {len(papers)} papers")
    print()
    
    # Process papers
    results = []
    include_count = 0
    exclude_count = 0
    maybe_count = 0
    error_count = 0
    
    start_time = time.time()
    
    for i, paper in enumerate(papers, 1):
        if verbose:
            print(f"🔍 [{i:3d}/{len(papers)}] {paper.title[:60]}...")
        else:
            # Progress indicator
            if i % 10 == 0 or i == len(papers):
                progress = (i / len(papers)) * 100
                print(f"   📊 Progress: {i}/{len(papers)} ({progress:.1f}%)")
        
        try:
            # Screen the paper
            paper_start = time.time()
            result = screener.screen_paper(paper)
            processing_time = time.time() - paper_start
            
            # Convert result to JSON-serializable format
            result_data = {
                "paper_id": paper.paper_id,
                "title": paper.title,
                "authors": paper.authors or [],
                "journal": paper.journal,
                "year": paper.year,
                "abstract": paper.abstract,
                "doi": paper.doi,
                "decision": result.final_decision.value,
                "reasoning": result.decision_reasoning,
                "processing_time": round(processing_time, 2),
                "criteria": {
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
            }
            
            results.append(result_data)
            
            # Count decisions
            decision = result.final_decision.value
            if decision == "include":
                include_count += 1
            elif decision == "exclude":
                exclude_count += 1
            elif decision == "maybe":
                maybe_count += 1
            
            if verbose:
                print(f"       → {decision.upper()} ({processing_time:.1f}s)")
            
        except Exception as e:
            error_count += 1
            if verbose:
                print(f"       → ERROR: {e}")
            
            # Add error result
            error_result = {
                "paper_id": paper.paper_id,
                "title": paper.title,
                "decision": "error",
                "reasoning": f"Processing error: {str(e)}",
                "error": str(e)
            }
            results.append(error_result)
    
    total_time = time.time() - start_time
    
    # Save results
    print(f"\n💾 Saving results...")
    
    output_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_papers": len(papers),
            "processing_time_seconds": round(total_time, 1),
            "average_time_per_paper": round(total_time / len(papers), 2),
            "model_used": model_config.model_name,
            "prompt_version": "optimized"
        },
        "summary": {
            "include": include_count,
            "exclude": exclude_count,
            "maybe": maybe_count,
            "errors": error_count,
            "maybe_rate": round((maybe_count / len(papers)) * 100, 1) if papers else 0
        },
        "results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Results saved to: {output_file}")
    
    # Print summary
    print(f"\n📊 SCREENING COMPLETE")
    print("=" * 20)
    print(f"📄 Total papers processed: {len(papers)}")
    print(f"✅ Include decisions: {include_count} ({include_count/len(papers)*100:.1f}%)")
    print(f"❌ Exclude decisions: {exclude_count} ({exclude_count/len(papers)*100:.1f}%)")
    print(f"❓ Maybe decisions: {maybe_count} ({maybe_count/len(papers)*100:.1f}%)")
    if error_count > 0:
        print(f"⚠️  Processing errors: {error_count}")
    print(f"⏱️  Total time: {total_time/60:.1f} minutes")
    print(f"⚡ Average per paper: {total_time/len(papers):.1f} seconds")
    
    if maybe_count > 0:
        print(f"\n📋 NEXT STEPS:")
        print(f"   🔍 {maybe_count} papers require human review")
        print(f"   📄 Review criteria marked as 'UNCLEAR' in results")
        print(f"   🎯 Estimated review time: {maybe_count * 0.5:.1f} hours")
    
    return results

def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description="Production paper screening pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_screening.py --input data/input/papers.txt
  python run_screening.py --input data/input/papers.txt --output results.json
  python run_screening.py --input data/input/papers.txt --max-papers 100 --verbose
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
    
    # Run screening
    try:
        screen_papers(
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
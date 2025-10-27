#!/usr/bin/env python3
"""
Test the streamlined 7-criteria approach on validation dataset.
"""

import sys
import os
import json
import time
import openai
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any
import argparse

# Add the src directory to the path
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

# Import models directly
from src.models import ModelConfig, Paper, ScreeningDecision, StructuredScreeningResult, CriteriaAssessment
from src.parsers import RISParser


class StreamlinedPaperScreener:
    """Streamlined paper screener using 7 criteria (no redundant dual component)."""
    
    def __init__(self, model_config):
        self.model_config = model_config
        openai.api_key = model_config.api_key
        
        # Load the streamlined prompt
        prompt_path = Path("prompts/structured_screening_streamlined.txt")
        if not prompt_path.exists():
            raise FileNotFoundError("Streamlined prompt file not found")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.system_prompt = f.read()
    
    def screen_paper(self, abstract: str, paper_id: str = None) -> StructuredScreeningResult:
        """Screen a single paper using streamlined 7-criteria approach."""
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model_config.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Evaluate this research paper abstract:\n\n{abstract}"}
                ],
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse the JSON response
            try:
                # Handle smart quotes and common JSON issues
                cleaned_response = response_text.replace('"', '"').replace('"', '"').replace("'", "'")
                
                # Extract JSON from response if wrapped in code blocks
                if "```json" in cleaned_response:
                    start = cleaned_response.find("```json") + 7
                    end = cleaned_response.find("```", start)
                    cleaned_response = cleaned_response[start:end].strip()
                elif "```" in cleaned_response:
                    start = cleaned_response.find("```") + 3
                    end = cleaned_response.find("```", start)
                    cleaned_response = cleaned_response[start:end].strip()
                
                result_data = json.loads(cleaned_response)
                
                # Extract criteria evaluations (7 criteria now)
                criteria_eval = result_data.get('criteria_evaluation', {})
                criteria_assessments = []
                
                criteria_mapping = {
                    'participants_lmic': 'participants_lmic',
                    'component_a_cash_support': 'component_a_cash',
                    'component_b_productive_assets': 'component_b_assets',
                    'relevant_outcomes': 'outcomes',
                    'appropriate_study_design': 'study_design',
                    'publication_year_2004_plus': 'year_2004_plus',
                    'completed_study': 'completed'
                }
                
                for criterion_key, short_name in criteria_mapping.items():
                    criterion_data = criteria_eval.get(criterion_key, {})
                    assessment = criterion_data.get('assessment', 'UNCLEAR')
                    reasoning = criterion_data.get('reasoning', 'No reasoning provided')
                    
                    criteria_assessments.append(CriteriaAssessment(
                        criterion=short_name,
                        assessment=assessment,
                        justification=reasoning
                    ))
                
                # Auto-derive dual component status
                comp_a_assessment = next((c.assessment for c in criteria_assessments if c.criterion == 'component_a_cash'), 'UNCLEAR')
                comp_b_assessment = next((c.assessment for c in criteria_assessments if c.criterion == 'component_b_assets'), 'UNCLEAR')
                
                if comp_a_assessment == 'YES' and comp_b_assessment == 'YES':
                    dual_status = 'YES'
                elif comp_a_assessment == 'NO' or comp_b_assessment == 'NO':
                    dual_status = 'NO'
                else:
                    dual_status = 'UNCLEAR'
                
                # Get final decision
                final_decision = result_data.get('final_decision', 'MAYBE')
                decision_reasoning = result_data.get('decision_reasoning', 'No reasoning provided')
                
                return StructuredScreeningResult(
                    paper_id=paper_id or "unknown",
                    overall_decision=final_decision,
                    overall_justification=decision_reasoning,
                    criteria_assessments=criteria_assessments,
                    dual_component_status=dual_status,
                    processing_metadata={
                        'model': self.model_config.model_name,
                        'approach': 'streamlined_7_criteria',
                        'auto_derived_dual': dual_status
                    }
                )
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error for paper {paper_id}: {e}")
                print(f"Response text: {response_text[:500]}...")
                
                # Return default result for parsing failures
                default_assessments = []
                for short_name in criteria_mapping.values():
                    default_assessments.append(CriteriaAssessment(
                        criterion=short_name,
                        assessment='UNCLEAR',
                        justification=f'Failed to parse AI response: {str(e)}'
                    ))
                
                return StructuredScreeningResult(
                    paper_id=paper_id or "unknown",
                    overall_decision='UNCERTAIN',
                    overall_justification=f'Failed to parse AI response: {str(e)}',
                    criteria_assessments=default_assessments,
                    dual_component_status='UNCLEAR',
                    processing_metadata={
                        'model': self.model_config.model_name,
                        'approach': 'streamlined_7_criteria',
                        'parsing_error': str(e)
                    }
                )
                
        except Exception as e:
            print(f"Error screening paper {paper_id}: {e}")
            raise


def run_streamlined_validation():
    """Run validation using streamlined 7-criteria approach."""
    
    print("STREAMLINED VALIDATION: 7-CRITERIA APPROACH")
    print("=" * 55)
    print()
    
    # Load configuration
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ Configuration file not found. Please ensure config/config.yaml exists.")
        return
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    model_config = ModelConfig(
        api_key=config['openai']['api_key'],
        model_name=config['openai']['model'],
        temperature=config['openai']['temperature'],
        max_tokens=config['openai']['max_tokens']
    )
    
    # Initialize screener
    screener = StreamlinedPaperScreener(model_config)
    
    # Load gold standard dataset
    data_dir = Path("data/input")
    all_papers = []
    
    for file_path in [data_dir / "included.txt", data_dir / "excluded.txt"]:
        if not file_path.exists():
            print(f"❌ Required file not found: {file_path}")
            return
        
        expected_decision = "INCLUDE" if "included" in file_path.name else "EXCLUDE"
        parser = RISParser()
        papers = parser.parse_file(str(file_path))
        
        for paper in papers:
            paper.expected_decision = expected_decision
            all_papers.append(paper)
    
    print(f"📊 Loaded {len(all_papers)} papers for validation")
    print(f"   • {len([p for p in all_papers if p.expected_decision == 'INCLUDE'])} expected INCLUDE")
    print(f"   • {len([p for p in all_papers if p.expected_decision == 'EXCLUDE'])} expected EXCLUDE")
    print()
    
    # Run validation
    results = []
    start_time = time.time()
    
    for i, paper in enumerate(all_papers, 1):
        print(f"Processing paper {i}/{len(all_papers)}: {paper.id}")
        
        try:
            paper_start = time.time()
            result = screener.screen_paper(paper.abstract, paper.id)
            processing_time = time.time() - paper_start
            
            # Create result summary
            criteria_summary = {}
            for assessment in result.criteria_assessments:
                criteria_summary[assessment.criterion] = assessment.assessment
            
            result_summary = {
                'paper_id': paper.id,
                'title': paper.title,
                'expected_decision': paper.expected_decision,
                'ai_decision': result.overall_decision,
                'decision_reasoning': result.overall_justification,
                'criteria_summary': criteria_summary,
                'dual_component_status': result.dual_component_status,
                'criteria_counts': {
                    'YES': sum(1 for a in result.criteria_assessments if a.assessment == 'YES'),
                    'NO': sum(1 for a in result.criteria_assessments if a.assessment == 'NO'),
                    'UNCLEAR': sum(1 for a in result.criteria_assessments if a.assessment == 'UNCLEAR')
                },
                'processing_time': processing_time,
                'approach': 'streamlined_7_criteria'
            }
            
            results.append(result_summary)
            
            # Brief progress update
            yes_count = result_summary['criteria_counts']['YES']
            no_count = result_summary['criteria_counts']['NO']
            unclear_count = result_summary['criteria_counts']['UNCLEAR']
            dual_status = result_summary['dual_component_status']
            
            print(f"   → {result.overall_decision} ({yes_count}Y, {no_count}N, {unclear_count}U, Dual:{dual_status})")
            
        except Exception as e:
            print(f"❌ Error processing paper {paper.id}: {e}")
            continue
    
    total_time = time.time() - start_time
    
    # Save results
    output_file = Path("data/output/streamlined_validation_results.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print()
    print("✅ STREAMLINED VALIDATION COMPLETE")
    print(f"   • {len(results)} papers processed")
    print(f"   • Total time: {total_time:.1f} seconds")
    print(f"   • Average time per paper: {total_time/len(results):.1f} seconds")
    print(f"   • Results saved: {output_file}")
    print()
    
    # Quick analysis
    print("📊 QUICK ANALYSIS:")
    
    # Decision accuracy
    correct_decisions = sum(1 for r in results if r['ai_decision'] == r['expected_decision'])
    accuracy = correct_decisions / len(results) * 100 if results else 0
    print(f"   • Decision accuracy: {accuracy:.1f}% ({correct_decisions}/{len(results)})")
    
    # UNCLEAR rates
    total_criteria = len(results) * 7  # 7 criteria now
    total_unclear = sum(r['criteria_counts']['UNCLEAR'] for r in results)
    unclear_rate = total_unclear / total_criteria * 100 if total_criteria else 0
    print(f"   • Overall UNCLEAR rate: {unclear_rate:.1f}% ({total_unclear}/{total_criteria})")
    
    # Decision distribution
    decision_counts = {}
    for r in results:
        decision = r['ai_decision']
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
    
    print("   • Decision distribution:")
    for decision, count in sorted(decision_counts.items()):
        print(f"     - {decision}: {count} papers")
    
    # JSON parsing success
    parsing_failures = sum(1 for r in results if r['ai_decision'] == 'UNCERTAIN')
    parsing_success = (len(results) - parsing_failures) / len(results) * 100 if results else 0
    print(f"   • JSON parsing success: {parsing_success:.1f}% ({len(results) - parsing_failures}/{len(results)})")
    
    print()
    print("🔍 Compare with previous 8-criteria results to see improvements!")


if __name__ == "__main__":
    run_streamlined_validation()
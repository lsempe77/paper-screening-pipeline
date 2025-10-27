#!/usr/bin/env python3
"""
Run structured validation on the full gold standard dataset.
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


class StructuredPaperScreener:
    """Structured paper screener using criteria-based evaluation."""
    
    def __init__(self, model_config):
        self.model_config = model_config
        self.client = openai.OpenAI(
            base_url=model_config.api_url,
            api_key=model_config.api_key
        )
        
    def screen_paper(self, paper, prompt_template: Optional[str] = None, training_examples: str = "") -> StructuredScreeningResult:
        """Screen a paper using structured criteria evaluation."""
        
        if prompt_template is None:
            prompt_template = self._load_structured_prompt()
        
        # Format prompt with paper details
        formatted_prompt = prompt_template.format(
            title=paper.title,
            authors=', '.join(paper.authors),
            journal=paper.journal,
            year=paper.year or 'Unknown',
            abstract=paper.abstract,
            keywords=', '.join(paper.keywords),
            doi=paper.doi or 'No DOI',
            publication_type=paper.publication_type or 'Unknown'
        )
        
        # Add training examples if provided
        if training_examples:
            formatted_prompt = f"{formatted_prompt}\n\n## TRAINING EXAMPLES:\n{training_examples}"
        
        start_time = time.time()
        
        try:
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model_config.model_name,
                messages=[{"role": "user", "content": formatted_prompt}],
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens
            )
            
            processing_time = time.time() - start_time
            raw_response = response.choices[0].message.content or ""
            
            # Parse structured response
            result = self._parse_structured_response(
                paper.paper_id, 
                raw_response, 
                processing_time
            )
            
            return result
            
        except Exception as e:
            print(f"Error screening paper {paper.paper_id}: {e}")
            # Return error result
            error_assessment = CriteriaAssessment("UNCLEAR", f"Error during screening: {str(e)}")
            
            return StructuredScreeningResult(
                paper_id=paper.paper_id,
                final_decision=ScreeningDecision.UNCERTAIN,
                decision_reasoning=f"Screening failed due to error: {str(e)}",
                participants_lmic=error_assessment,
                component_a_cash_support=error_assessment,
                component_b_productive_assets=error_assessment,
                dual_component_overall=error_assessment,
                relevant_outcomes=error_assessment,
                appropriate_study_design=error_assessment,
                publication_year_2004_plus=error_assessment,
                completed_study=error_assessment,
                model_used=self.model_config.model_name,
                raw_response=str(e),
                processing_time=time.time() - start_time
            )
    
    def _load_structured_prompt(self) -> str:
        """Load the structured screening prompt."""
        prompt_path = script_dir / "prompts" / "structured_screening.txt"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Structured prompt file not found at {prompt_path}")
    
    def _parse_structured_response(self, paper_id: str, response: str, processing_time: float) -> StructuredScreeningResult:
        """Parse structured JSON response into StructuredScreeningResult."""
        
        try:
            # Clean response and extract JSON
            response_clean = response.strip()
            
            # Find JSON block
            json_start = response_clean.find('{')
            json_end = response_clean.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_clean[json_start:json_end]
            
            # Fix smart quotes that break JSON parsing
            import re
            # Replace various quote types
            json_str = re.sub(r'[\u201c\u201d]', '"', json_str)  # Left and right double quotes
            json_str = re.sub(r'[\u2018\u2019]', "'", json_str)  # Left and right single quotes
            # Fix instances where quotes inside strings break JSON
            lines = json_str.split('\n')
            fixed_lines = []
            for line in lines:
                if '"reasoning":' in line:
                    # Find the reasoning value and escape quotes inside it
                    match = re.search(r'"reasoning":\s*"([^"]*(?:"[^"]*)*)"', line)
                    if match:
                        reasoning_text = match.group(1)
                        # Escape internal quotes
                        reasoning_text = reasoning_text.replace('"', '\\"')
                        line = re.sub(r'"reasoning":\s*"([^"]*(?:"[^"]*)*)"', f'"reasoning": "{reasoning_text}"', line)
                fixed_lines.append(line)
            json_str = '\n'.join(fixed_lines)
            
            data = json.loads(json_str)
            
            # Extract criteria evaluations
            criteria = data.get('criteria_evaluation', {})
            
            # Map decision to enum
            decision_str = data.get('final_decision', 'UNCERTAIN').upper()
            if decision_str == "INCLUDE":
                final_decision = ScreeningDecision.INCLUDE
            elif decision_str == "EXCLUDE":
                final_decision = ScreeningDecision.EXCLUDE  
            elif decision_str == "MAYBE":
                final_decision = ScreeningDecision.MAYBE
            else:
                final_decision = ScreeningDecision.UNCERTAIN
            
            # Create criteria assessment objects
            def make_assessment(criterion_data):
                if isinstance(criterion_data, dict):
                    return CriteriaAssessment(
                        assessment=criterion_data.get('assessment', 'UNCLEAR'),
                        reasoning=criterion_data.get('reasoning', 'No reasoning provided')
                    )
                else:
                    return CriteriaAssessment('UNCLEAR', 'Invalid criterion data')
            
            return StructuredScreeningResult(
                paper_id=paper_id,
                final_decision=final_decision,
                decision_reasoning=data.get('decision_reasoning', 'No reasoning provided'),
                participants_lmic=make_assessment(criteria.get('participants_lmic', {})),
                component_a_cash_support=make_assessment(criteria.get('component_a_cash_support', {})),
                component_b_productive_assets=make_assessment(criteria.get('component_b_productive_assets', {})),
                dual_component_overall=make_assessment(criteria.get('dual_component_overall', {})),
                relevant_outcomes=make_assessment(criteria.get('relevant_outcomes', {})),
                appropriate_study_design=make_assessment(criteria.get('appropriate_study_design', {})),
                publication_year_2004_plus=make_assessment(criteria.get('publication_year_2004_plus', {})),
                completed_study=make_assessment(criteria.get('completed_study', {})),
                model_used=self.model_config.model_name,
                raw_response=response,
                processing_time=processing_time
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error parsing structured response: {e}")
            print(f"Full Response: {response}")
            
            # Return uncertain result with error info
            error_assessment = CriteriaAssessment("UNCLEAR", f"Parsing error: {str(e)}")
            
            return StructuredScreeningResult(
                paper_id=paper_id,
                final_decision=ScreeningDecision.UNCERTAIN,
                decision_reasoning=f"Failed to parse AI response: {str(e)}",
                participants_lmic=error_assessment,
                component_a_cash_support=error_assessment,
                component_b_productive_assets=error_assessment,
                dual_component_overall=error_assessment,
                relevant_outcomes=error_assessment,
                appropriate_study_design=error_assessment,
                publication_year_2004_plus=error_assessment,
                completed_study=error_assessment,
                model_used=self.model_config.model_name,
                raw_response=response,
                processing_time=processing_time
            )


def load_training_examples() -> str:
    """Load training examples from included papers (positive examples only)."""
    included_file = script_dir / "data" / "input" / "included.txt"
    
    if not included_file.exists():
        print(f"Training file not found: {included_file}")
        return ""
    
    try:
        parser = RISParser()
        included_papers = parser.parse_file(str(included_file))
        
        # Use first 3 papers as examples
        example_papers = included_papers[:3]
        examples_text = "These are examples of papers that should be INCLUDED:\n\n"
        
        for i, paper in enumerate(example_papers, 1):
            examples_text += f"Example {i}:\n"
            examples_text += f"Title: {paper.title}\n"
            examples_text += f"Abstract: {paper.abstract[:300]}...\n"
            examples_text += f"Decision: INCLUDE\n\n"
        
        return examples_text
        
    except Exception as e:
        print(f"Error loading training examples: {e}")
        return ""


def run_structured_validation():
    """Run structured validation on the gold standard dataset."""
    
    # Load configuration
    config_path = script_dir / "config" / "config.yaml"
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Create model config
    model_data = config_data['models']['primary']
    model_config = ModelConfig(
        provider=model_data['provider'],
        model_name=model_data['model_name'],
        temperature=model_data['temperature'],
        max_tokens=model_data['max_tokens'],
        api_key=config_data['openrouter']['api_key'],
        api_url=config_data['openrouter']['api_url'],
        max_retries=model_data['max_retries']
    )
    
    # Create screener
    screener = StructuredPaperScreener(model_config)
    
    # Load training examples
    training_examples = load_training_examples()
    
    # Load gold standard papers
    parser = RISParser()
    
    included_papers = parser.parse_file(str(script_dir / "data" / "input" / "included.txt"))
    excluded_papers = parser.parse_file(str(script_dir / "data" / "input" / "excluded.txt"))
    
    # Prepare validation dataset (skip training examples)
    validation_papers = []
    expected_decisions = {}
    
    # Add remaining included papers (skip first 3 used for training)
    for paper in included_papers[3:]:
        expected_decisions[paper.paper_id] = "INCLUDE"
        validation_papers.append(paper)
    
    # Add excluded papers
    for paper in excluded_papers:
        expected_decisions[paper.paper_id] = "EXCLUDE"
        validation_papers.append(paper)
    
    print(f"\nStructured Validation Starting...")
    print(f"Total papers to validate: {len(validation_papers)}")
    print(f"Expected INCLUDE: {len(included_papers) - 3}")
    print(f"Expected EXCLUDE: {len(excluded_papers)}")
    print(f"Training examples loaded: {len(training_examples) > 0}")
    print("=" * 60)
    
    results = []
    total_cost = 0.0
    
    for i, paper in enumerate(validation_papers, 1):
        print(f"\nProcessing {i}/{len(validation_papers)}: {paper.paper_id}")
        
        # Screen the paper
        result = screener.screen_paper(paper, training_examples=training_examples)
        results.append((paper, result))
        
        # Calculate approximate cost (Claude-3-Haiku pricing)
        tokens_estimate = len(result.raw_response.split()) * 1.3  # Rough token estimation
        cost_estimate = (tokens_estimate / 1000) * 0.00025  # $0.25 per 1k tokens
        total_cost += cost_estimate
        
        # Print brief result
        expected = expected_decisions[paper.paper_id]
        print(f"  Decision: {result.final_decision.value.upper()}")
        print(f"  Expected: {expected}")
        print(f"  Match: {'✓' if result.final_decision.value.upper() == expected else '✗'}")
        
        # Show criteria summary
        criteria_summary = result.get_criteria_summary()
        counts = result.count_criteria_by_status()
        print(f"  Criteria: {counts['YES']} YES, {counts['NO']} NO, {counts['UNCLEAR']} UNCLEAR")
        
        # Brief pause to avoid rate limits
        if i % 10 == 0:
            print(f"\n--- Processed {i} papers, estimated cost so far: ${total_cost:.2f} ---")
            time.sleep(2)
    
    # Analyze results
    print(f"\n{'='*80}")
    print("STRUCTURED VALIDATION RESULTS")
    print(f"{'='*80}")
    
    # Classification analysis
    correct = 0
    include_decisions = {"INCLUDE": 0, "EXCLUDE": 0, "MAYBE": 0, "UNCERTAIN": 0}
    exclude_decisions = {"INCLUDE": 0, "EXCLUDE": 0, "MAYBE": 0, "UNCERTAIN": 0}
    
    # Decision mapping for analysis
    decision_mapping = {
        "INCLUDE": ScreeningDecision.INCLUDE,
        "EXCLUDE": ScreeningDecision.EXCLUDE,
        "MAYBE": ScreeningDecision.MAYBE,
        "UNCERTAIN": ScreeningDecision.UNCERTAIN
    }
    
    for paper, result in results:
        actual_decision = result.final_decision.value.upper()
        expected = expected_decisions[paper.paper_id]
        
        if expected == "INCLUDE":
            include_decisions[actual_decision] += 1
            if actual_decision in ["INCLUDE", "MAYBE"]:  # MAYBE is acceptable for included papers
                correct += 1
        else:  # EXCLUDE
            exclude_decisions[actual_decision] += 1
            if actual_decision == "EXCLUDE":
                correct += 1
    
    # Print confusion matrix
    print(f"\nConfusion Matrix:")
    print(f"                  Predicted")
    print(f"                  INCL  EXCL  MAYBE UNCERT")
    print(f"Expected INCLUDE  {include_decisions['INCLUDE']:4d}  {include_decisions['EXCLUDE']:4d}  {include_decisions['MAYBE']:5d} {include_decisions['UNCERTAIN']:5d}")
    print(f"Expected EXCLUDE  {exclude_decisions['INCLUDE']:4d}  {exclude_decisions['EXCLUDE']:4d}  {exclude_decisions['MAYBE']:5d} {exclude_decisions['UNCERTAIN']:5d}")
    
    # Calculate metrics
    total_papers = len(validation_papers)
    accuracy = (correct / total_papers) * 100
    
    print(f"\nOverall Performance:")
    print(f"Total papers validated: {total_papers}")
    print(f"Correct decisions: {correct}")
    print(f"Accuracy: {accuracy:.1f}%")
    print(f"Estimated total cost: ${total_cost:.2f}")
    
    # Analyze MAYBE decisions
    maybe_papers = [result for paper, result in results if result.final_decision == ScreeningDecision.MAYBE]
    print(f"\nMAYBE Decisions ({len(maybe_papers)} papers):")
    if maybe_papers:
        for result in maybe_papers[:5]:  # Show first 5
            paper_obj = next(p for p, r in results if r.paper_id == result.paper_id)
            expected = expected_decisions[paper_obj.paper_id]
            print(f"  {result.paper_id} (Expected: {expected})")
            print(f"    Reasoning: {result.decision_reasoning[:100]}...")
    
    # Analyze common unclear criteria
    unclear_criteria = {
        'participants_lmic': 0,
        'component_a_cash': 0,
        'component_b_assets': 0,
        'dual_component': 0,
        'outcomes': 0,
        'study_design': 0,
        'year_2004_plus': 0,
        'completed': 0
    }
    
    for paper, result in results:
        criteria_summary = result.get_criteria_summary()
        for criterion, assessment in criteria_summary.items():
            if assessment == "UNCLEAR":
                unclear_criteria[criterion] += 1
    
    print(f"\nMost Common UNCLEAR Criteria:")
    sorted_unclear = sorted(unclear_criteria.items(), key=lambda x: x[1], reverse=True)
    for criterion, count in sorted_unclear:
        if count > 0:
            print(f"  {criterion}: {count} papers ({count/total_papers*100:.1f}%)")
    
    # Save detailed results
    results_file = script_dir / "data" / "output" / "structured_validation_results.json"
    detailed_results = []
    
    for paper, result in results:
        detailed_results.append({
            'paper_id': paper.paper_id,
            'title': paper.title,
            'expected_decision': expected_decisions[paper.paper_id],
            'ai_decision': result.final_decision.value.upper(),
            'decision_reasoning': result.decision_reasoning,
            'criteria_summary': result.get_criteria_summary(),
            'criteria_counts': result.count_criteria_by_status(),
            'processing_time': result.processing_time
        })
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: {results_file}")


if __name__ == "__main__":
    run_structured_validation()
#!/usr/bin/env python3
"""
Test script for structured screening approach.
"""

import sys
import os
import json
import time
import openai
import yaml
from pathlib import Path
from typing import Optional

# Add the src directory to the path
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

# Import models directly
from src.models import ModelConfig, Paper, ScreeningDecision, StructuredScreeningResult, CriteriaAssessment


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
            # Replace various quote types
            import re
            # Replace smart quotes with regular quotes, but be careful not to break JSON structure
            json_str = re.sub(r'[\u201c\u201d]', '"', json_str)  # Left and right double quotes
            json_str = re.sub(r'[\u2018\u2019]', "'", json_str)  # Left and right single quotes
            # Fix instances where quotes inside strings break JSON
            # This is a more complex fix - let's just escape internal quotes
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


def test_structured_screening():
    """Test the structured screening approach on the Bauchet paper."""
    
    # Load configuration
    config_path = script_dir / "config" / "config.yaml"
    
    import yaml
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
    
    # Test papers
    test_papers = [
        # 1. Bauchet paper (borderline case)
        Paper(
            paper_id="bauchet_2015",
            title="Failure Vs. Displacement: Why An Innovative Anti-Poverty Program Showed No Net Impact In South India",
            authors=["Bauchet Jonathan", "Morduch Jonathan", "Ravi Shamika"],
            journal="Journal of Development Economics",
            year=2015,
            abstract="""We analyze a randomized trial of an innovative anti-poverty program in South India, part of a series of pilot programs that provide "ultra-poor" households with inputs to create new, sustainable livelihoods (often tending livestock). In contrast with results from other pilots, we find no lasting net impact on income or asset accumulation in South India. We explore concerns with program implementation, data errors, and the existence of compelling employment alternatives. The baseline consumption data contain systematic errors, and income and consumption contain large outliers. Steps to address the problems leave the central findings largely intact: Wages for unskilled labor rose sharply in the area while the study was implemented, blunting the net impact of the intervention and highlighting one way that treatment effects depend on factors external to the intervention itself, such as broader employment opportunities.""",
            keywords=["Graduation Programme", "Sustainable Livelihood", "Resilience", "Health Consults", "Asset Transfer", "Ultra-Poor", "Household Consumption", "Food systems and nutrition"],
            doi="10.1016/j.jdeveco.2015.03.005",
            publication_type="JOUR"
        ),
        
        # 2. Clear INCLUDE case - Banerjee 2015 (6-country study)
        Paper(
            paper_id="banerjee_2015",
            title="A Multifaceted Program Causes Lasting Progress For The Very Poor: Evidence From Six Countries",
            authors=["Banerjee Abhijit", "Duflo Esther", "Goldberg Nathanael"],
            journal="Science",
            year=2015,
            abstract="""We present results from six randomized control trials of an integrated approach to improve livelihoods among the very poor. The approach combines the transfer of a productive asset with consumption support, training, and coaching plus savings encouragement and health education and/or services. Results from the implementation of the same basic program, adapted to a wide variety of geographic and institutional contexts and with multiple implementing partners, show statistically significant cost-effective impacts on consumption (fueled mostly by increases in self-employment income) and psychosocial status of the targeted households. The impact on the poor households lasted at least a year after all implementation ended. It is possible to make sustainable improvements in the economic status of the poor with a relatively short-term intervention.""",
            keywords=["Livelihoods", "Consumption Support", "Training", "Coaching", "Asset Transfer", "Savings", "Self-Employment", "Income"],
            doi="10.1126/science.1260799",
            publication_type="JOUR"
        ),
        
        # 3. Clear EXCLUDE case - Only cash transfers (hypothetical)
        Paper(
            paper_id="cash_only_2020",
            title="Impact of Unconditional Cash Transfers on Poverty Reduction in Rural Kenya",
            authors=["Smith Jane", "Johnson Peter"],
            journal="Development Economics Review",
            year=2020,
            abstract="""This study evaluates the impact of unconditional cash transfers on poverty outcomes in rural Kenya. Using a randomized controlled trial with 2,000 households, we examine how monthly cash transfers of $20 affect household consumption, savings, and welfare over 24 months. We find significant improvements in consumption and food security, with households investing in education and healthcare. However, no productive assets were provided as part of the intervention. Results show that cash transfers alone can provide temporary relief but may not lead to sustainable livelihood improvements without complementary interventions.""",
            keywords=["Cash transfers", "Poverty", "Kenya", "RCT", "Consumption"],
            doi="10.1234/example.2020.001",
            publication_type="JOUR"
        )
    ]
    
    # Test case: A paper that should be EXCLUDE (has NO criteria)
    test_paper = Paper(
        paper_id="test_exclude",
        title="Microfinance and Diversification", 
        authors=["Author A"],
        journal="Test Journal",
        year=2022,
        abstract="""This study examines the impact of microfinance on income diversification strategies in rural Uganda. We use household survey data to analyze how access to microcredit affects the number and types of income-generating activities. The study does not provide any cash transfers or productive assets to participants, but rather examines existing microfinance services. Results show that microfinance access increases income diversification among rural households.""",
        keywords=["microfinance", "diversification"],
        doi="10.1234/test",
        publication_type="JOUR"
    )
    
    print(f"\n{'='*80}")
    print(f"TESTING CORRECTED DECISION LOGIC")
    print(f"Expected: This should be EXCLUDE (no cash support, no productive assets)")
    print(f"{'='*80}")
    
    # Screen the paper
    result = screener.screen_paper(test_paper)
    
    # Print results
    print(f"\nPaper ID: {result.paper_id}")
    print(f"Final Decision: {result.final_decision.value.upper()}")
    print(f"Decision Reasoning: {result.decision_reasoning}")
    print("\nCriteria Assessment:")
    print("-" * 40)
    
    criteria_summary = result.get_criteria_summary()
    for criterion, assessment in criteria_summary.items():
        print(f"{criterion:20}: {assessment}")
    
    # Show detailed assessments 
    print(f"\nDetailed Criteria Evaluations:")
    print("-" * 40)
    
    evaluations = [
        ("LMIC Focus", result.participants_lmic),
        ("Cash Support", result.component_a_cash_support),
        ("Productive Assets", result.component_b_productive_assets),
        ("Dual Component", result.dual_component_overall),
        ("Relevant Outcomes", result.relevant_outcomes),
        ("Study Design", result.appropriate_study_design),
        ("Year ≥2004", result.publication_year_2004_plus),
        ("Completed Study", result.completed_study)
    ]
    
    for name, evaluation in evaluations:
        print(f"\n{name}:")
        print(f"  Assessment: {evaluation.assessment}")
        print(f"  Reasoning: {evaluation.reasoning}")
    
    # Summary statistics
    counts = result.count_criteria_by_status()
    print(f"\nCriteria Summary:")
    print(f"  YES: {counts['YES']}")
    print(f"  NO: {counts['NO']}")
    print(f"  UNCLEAR: {counts['UNCLEAR']}")
    
    print(f"\nModel Used: {result.model_used}")
    print(f"Processing Time: {result.processing_time:.2f}s")


if __name__ == "__main__":
    test_structured_screening()
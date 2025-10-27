#!/usr/bin/env python3
"""
Integrated structured paper screener using criteria-only LLM assessment + Python decision logic.
"""

import sys
import json
import time
import openai
from pathlib import Path
from typing import Optional

# Add the src directory to the path
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

from src.models import StructuredScreeningResult, CriteriaAssessment, ScreeningDecision
from decision_processor import ScreeningDecisionProcessor, FinalDecision
from program_matcher import match_program

class IntegratedStructuredScreener:
    """Integrated structured screener using LLM for criteria + Python for decisions."""
    
    CRITERION_LABELS = {
        "participants_lmic": "LMIC participants",
        "component_a_cash_support": "Cash support",
        "component_b_productive_assets": "Productive assets",
        "relevant_outcomes": "Relevant outcomes",
        "appropriate_study_design": "Study design",
        "publication_year_2004_plus": "Year 2004+",
        "completed_study": "Completed study"
    }

    def __init__(self, model_config, use_followup_agent: bool = True, use_program_filter: bool = True):
        self.model_config = model_config
        self.client = openai.OpenAI(
            base_url=model_config.api_url,
            api_key=model_config.api_key
        )
        self.decision_processor = ScreeningDecisionProcessor(use_program_filter=use_program_filter)
        self.use_followup_agent = use_followup_agent
        self.use_program_filter = use_program_filter
        
    def screen_paper(self, paper, prompt_template: Optional[str] = None, training_examples: str = "") -> StructuredScreeningResult:
        """Screen a paper using integrated approach: LLM criteria + Python decision logic."""
        
        if prompt_template is None:
            prompt_template = self._load_criteria_only_prompt()
        
        paper_info = self._format_paper_info(paper)
        
        formatted_prompt = f"{prompt_template}\n\n## PAPER TO EVALUATE:\n{paper_info}"
        
        # Add training examples if provided
        if training_examples:
            formatted_prompt = f"{formatted_prompt}\n\n## TRAINING EXAMPLES:\n{training_examples}"
        
        start_time = time.time()
        
        try:
            # Step 1: Get LLM criteria assessment
            response = self.client.chat.completions.create(
                model=self.model_config.model_name,
                messages=[
                    {"role": "system", "content": "You are a systematic review expert evaluating research papers."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens
            )
            
            processing_time = time.time() - start_time
            raw_response = response.choices[0].message.content or ""
            
            # Step 1.5: Override program recognition with Python matching (if enabled)
            if self.use_program_filter:
                raw_response = self._apply_python_program_matching(raw_response, paper)
            
            # Step 2: Apply Python decision logic
            decision_result = self.decision_processor.process_llm_response(raw_response)
            
            # Step 3: Convert to StructuredScreeningResult format
            result = self._convert_to_structured_result(
                paper.paper_id,
                decision_result,
                raw_response,
                processing_time
            )

            if self.use_followup_agent and result.final_decision == ScreeningDecision.MAYBE:
                try:
                    followup_result = self._run_followup_sequence(
                        paper,
                        paper_info,
                        raw_response,
                        decision_result,
                        processing_time,
                        training_examples,
                        result.final_decision
                    )
                    if followup_result is not None:
                        result = followup_result
                except Exception as followup_error:
                    result.decision_reasoning += f" | Follow-up agent error: {followup_error}"
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            # Return error result
            error_assessment = CriteriaAssessment("UNCLEAR", f"Error during screening: {str(e)}")
            
            return StructuredScreeningResult(
                paper_id=paper.paper_id,
                final_decision=ScreeningDecision.UNCERTAIN,
                decision_reasoning=f"Screening failed due to error: {str(e)}",
                program_recognition=CriteriaAssessment("UNCLEAR", "Not assessed due to error"),
                participants_lmic=error_assessment,
                component_a_cash_support=error_assessment,
                component_b_productive_assets=error_assessment,
                relevant_outcomes=error_assessment,
                appropriate_study_design=error_assessment,
                publication_year_2004_plus=error_assessment,
                completed_study=error_assessment,
                model_used=self.model_config.model_name,
                raw_response=str(e),
                processing_time=processing_time
            )
    
    def _load_criteria_only_prompt(self) -> str:
        """Load the unified screening criteria prompt."""
        # Use the unified prompt file (includes program recognition if use_program_filter=True)
        unified_path = script_dir / "prompts" / "structured_screening_unified.txt"
        try:
            with open(unified_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback to old optimized version for backwards compatibility
            optimized_path = script_dir / "prompts" / "structured_screening_criteria_optimized.txt"
            try:
                with open(optimized_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                # Final fallback
                return self._get_fallback_criteria_prompt()
    
    def _get_fallback_criteria_prompt(self) -> str:
        """Fallback criteria prompt if file not found."""
        return """
You are evaluating a research paper against inclusion criteria. Assess each criterion as YES/NO/UNCLEAR.

Evaluate these 7 criteria:
1. LMIC participants
2. Cash/in-kind support component 
3. Productive assets component
4. Economic/livelihood outcomes
5. Quantitative impact evaluation design
6. Published 2004 or later
7. Completed study

Respond with JSON only:
{
    "criteria_evaluation": {
        "participants_lmic": {"assessment": "YES/NO/UNCLEAR", "reasoning": "explanation"},
        "component_a_cash_support": {"assessment": "YES/NO/UNCLEAR", "reasoning": "explanation"},
        "component_b_productive_assets": {"assessment": "YES/NO/UNCLEAR", "reasoning": "explanation"},
        "relevant_outcomes": {"assessment": "YES/NO/UNCLEAR", "reasoning": "explanation"},
        "appropriate_study_design": {"assessment": "YES/NO/UNCLEAR", "reasoning": "explanation"},
        "publication_year_2004_plus": {"assessment": "YES/NO/UNCLEAR", "reasoning": "explanation"},
        "completed_study": {"assessment": "YES/NO/UNCLEAR", "reasoning": "explanation"}
    }
}
        """
    
    def _format_paper_info(self, paper) -> str:
        return f"""
**Title:** {paper.title}
**Authors:** {', '.join(paper.authors) if paper.authors else 'Unknown'}
**Journal:** {paper.journal or 'Unknown'}
**Year:** {paper.year or 'Unknown'}
**Abstract:** {paper.abstract or 'No abstract available'}
**Keywords:** {', '.join(paper.keywords) if paper.keywords else 'None'}
**DOI:** {paper.doi or 'No DOI'}
**Publication Type:** {paper.publication_type or 'Unknown'}
"""

    def _load_followup_prompt(self) -> str:
        prompt_path = script_dir / "prompts" / "structured_screening_followup.txt"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return (
                "You are reviewing a paper again to resolve criteria that remained UNCLEAR. "
                "Use the prior JSON assessment and the paper details to make a final call. "
                "Only output JSON with the same schema."
            )

    def _run_followup_sequence(
        self,
        paper,
        paper_info: str,
        initial_raw: str,
        initial_decision_result,
        base_processing_time: float,
        training_examples: str,
        initial_screening_decision: ScreeningDecision
    ) -> Optional[StructuredScreeningResult]:
        unclear_targets = [
            name for name, assessment in initial_decision_result.criteria_assessments.items()
            if assessment.value == "UNCLEAR"
        ]

        if not unclear_targets:
            return None

        prompt_template = self._load_followup_prompt()
        target_lines = []
        for target in unclear_targets:
            label = self.CRITERION_LABELS.get(target) or target
            reasoning = initial_decision_result.criteria_reasoning.get(target, "")
            target_lines.append(f"- {label}: {reasoning}")
        unclear_section = "\n".join(target_lines) if target_lines else "- None"

        followup_prompt = prompt_template.format(
            paper_info=paper_info,
            initial_json=initial_raw,
            unclear_targets=unclear_section
        )

        if training_examples:
            followup_prompt = f"{followup_prompt}\n\n## TRAINING EXAMPLES:\n{training_examples}"

        followup_start = time.time()
        response = self.client.chat.completions.create(
            model=self.model_config.model_name,
            messages=[
                {"role": "system", "content": "You are a systematic review expert resolving remaining uncertainties."},
                {"role": "user", "content": followup_prompt}
            ],
            temperature=self.model_config.temperature,
            max_tokens=self.model_config.max_tokens
        )
        followup_time = time.time() - followup_start
        followup_raw = response.choices[0].message.content or ""

        # Apply the same program matching override to follow-up responses
        if self.use_program_filter:
            followup_raw = self._apply_python_program_matching(followup_raw, paper)

        followup_decision_result = self.decision_processor.process_llm_response(followup_raw)
        total_processing_time = base_processing_time + followup_time

        followup_structured = self._convert_to_structured_result(
            paper.paper_id,
            followup_decision_result,
            followup_raw,
            total_processing_time
        )

        combined_raw = json.dumps({
            "first_pass": initial_raw,
            "followup_pass": followup_raw
        })
        followup_structured.raw_response = combined_raw

        targeted_labels = [self.CRITERION_LABELS.get(name) or name for name in unclear_targets]
        followup_structured.decision_reasoning += f" | Follow-up targeted: {', '.join(targeted_labels)}"

        if followup_structured.final_decision != initial_screening_decision:
            followup_structured.decision_reasoning += (
                f" | Follow-up updated decision from {initial_screening_decision.value} "
                f"to {followup_structured.final_decision.value}"
            )
        elif followup_structured.final_decision == ScreeningDecision.MAYBE:
            followup_structured.decision_reasoning += " | Follow-up could not resolve uncertainty"

        return followup_structured
    
    def _apply_python_program_matching(self, raw_response: str, paper) -> str:
        """
        Override LLM's program recognition with Python-based exact matching.
        Extracts program name from LLM response, uses Python to match against lists.
        Handles both simple and followup (nested) JSON structures.
        """
        try:
            # Check for empty response first
            if not raw_response or not raw_response.strip():
                raise json.JSONDecodeError("Empty response", "", 0)
            
            # Parse LLM response to extract program name
            cleaned_response = raw_response.replace('"', '"').replace('"', '"')
            
            if "```json" in cleaned_response:
                start = cleaned_response.find("```json") + 7
                end = cleaned_response.find("```", start)
                if end != -1:
                    cleaned_response = cleaned_response[start:end].strip()
                else:
                    cleaned_response = cleaned_response[start:].strip()
            elif "```" in cleaned_response:
                # Handle plain code fences without 'json' marker
                start = cleaned_response.find("```") + 3
                end = cleaned_response.find("```", start)
                if end != -1:
                    cleaned_response = cleaned_response[start:end].strip()
            
            # Check if cleaned response is empty after processing
            if not cleaned_response.strip():
                raise json.JSONDecodeError("Empty JSON after cleaning", "", 0)
            
            data = json.loads(cleaned_response)
            
            # Handle followup structure: {"first_pass": {...}, "followup": {...}}
            # vs simple structure: {"criteria_evaluation": {...}}
            first_pass_data = None
            if 'first_pass' in data:
                # This is a followup response with nested structure
                # We need to parse the first_pass JSON string
                first_pass_str = data['first_pass']
                # Remove markdown code fences if present
                if "```json" in first_pass_str:
                    start = first_pass_str.find("```json") + 7
                    end = first_pass_str.find("```", start)
                    if end != -1:
                        first_pass_str = first_pass_str[start:end].strip()
                
                first_pass_data = json.loads(first_pass_str)
                criteria_eval = first_pass_data.get('criteria_evaluation', {})
            else:
                # Simple structure
                criteria_eval = data.get('criteria_evaluation', {})
            
            prog_recog = criteria_eval.get('program_recognition', {})
            
            # Extract program name from LLM reasoning
            llm_program_name = prog_recog.get('reasoning', 'No specific program identified')
            
            # Use Python matching against known lists
            python_assessment, python_reasoning = match_program(
                llm_program_name,
                paper.title,
                paper.abstract
            )
            
            # Override the LLM's assessment with Python's exact matching
            prog_recog['assessment'] = python_assessment
            prog_recog['reasoning'] = f"[Python matched] {python_reasoning}"
            
            # Update the response
            criteria_eval['program_recognition'] = prog_recog
            
            # Put it back in the right structure
            if first_pass_data is not None:
                first_pass_data['criteria_evaluation'] = criteria_eval
                data['first_pass'] = json.dumps(first_pass_data)
            else:
                data['criteria_evaluation'] = criteria_eval
            
            # Return updated JSON
            return json.dumps(data)
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, try multiple recovery strategies
            print(f"Warning: JSON parsing failed in Python matching: {e}")
            print(f"Raw response length: {len(raw_response)}")
            print(f"Raw response preview: {raw_response[:200]}...")
            
            try:
                # Do Python matching first
                python_assessment, python_reasoning = match_program(
                    "Unknown program",
                    paper.title,
                    paper.abstract
                )
                print(f"Python matching result: {python_assessment} - {python_reasoning}")
                
                # Strategy 1: Try regex-based fallback if there's valid JSON structure
                import re
                
                # Look for program_recognition block in the response
                pattern = r'"program_recognition"\s*:\s*\{[^}]*"assessment"\s*:\s*"[^"]*"[^}]*"reasoning"\s*:\s*"[^"]*"[^}]*\}'
                
                if re.search(pattern, raw_response):
                    # Build replacement text with Python's assessment
                    escaped_reasoning = python_reasoning.replace('"', '\\"')
                    replacement = f'"program_recognition": {{"assessment": "{python_assessment}", "reasoning": "[Python matched] {escaped_reasoning}"}}'
                    
                    # Apply regex substitution
                    modified_response = re.sub(pattern, replacement, raw_response, count=1)
                    print(f"✓ Successfully injected Python matching via regex")
                    return modified_response
                
                # Strategy 2: If no valid JSON structure found, try to construct minimal valid response
                print(f"No valid JSON structure found, constructing minimal response...")
                
                # Create a minimal valid response structure
                minimal_response = {
                    "criteria_evaluation": {
                        "program_recognition": {
                            "assessment": python_assessment,
                            "reasoning": f"[Python matched - JSON recovery] {python_reasoning}"
                        },
                        "participants_lmic": {
                            "assessment": "UNCLEAR",
                            "reasoning": "LLM response was malformed - assessment recovered as UNCLEAR"
                        },
                        "component_a_cash_support": {
                            "assessment": "UNCLEAR", 
                            "reasoning": "LLM response was malformed - assessment recovered as UNCLEAR"
                        },
                        "component_b_productive_assets": {
                            "assessment": "UNCLEAR",
                            "reasoning": "LLM response was malformed - assessment recovered as UNCLEAR"
                        },
                        "relevant_outcomes": {
                            "assessment": "UNCLEAR",
                            "reasoning": "LLM response was malformed - assessment recovered as UNCLEAR"
                        },
                        "appropriate_study_design": {
                            "assessment": "UNCLEAR",
                            "reasoning": "LLM response was malformed - assessment recovered as UNCLEAR"
                        },
                        "publication_year_2004_plus": {
                            "assessment": "UNCLEAR", 
                            "reasoning": "LLM response was malformed - assessment recovered as UNCLEAR"
                        },
                        "completed_study": {
                            "assessment": "UNCLEAR",
                            "reasoning": "LLM response was malformed - assessment recovered as UNCLEAR"
                        }
                    }
                }
                
                constructed_response = json.dumps(minimal_response)
                print(f"✓ Successfully constructed minimal valid JSON response")
                return constructed_response
                    
            except Exception as inner_e:
                print(f"All fallback strategies failed: {inner_e}")
                print(f"Returning original malformed response - this may cause downstream errors")
                return raw_response
        except Exception as e:
            # If other errors occur, return original response
            print(f"Warning: Python program matching failed: {e}")
            return raw_response

    def _convert_to_structured_result(self, paper_id: str, decision_result, raw_response: str, processing_time: float) -> StructuredScreeningResult:
        """Convert decision processor result to StructuredScreeningResult."""
        
        # Map decision processor results to StructuredScreeningResult format
        def make_criteria_assessment(criterion_name: str) -> CriteriaAssessment:
            if criterion_name in decision_result.criteria_assessments:
                assessment = decision_result.criteria_assessments[criterion_name]
                reasoning = decision_result.criteria_reasoning[criterion_name]
                return CriteriaAssessment(assessment.value, reasoning)
            else:
                return CriteriaAssessment("UNCLEAR", "Criterion not found in response")
        
        # Map FinalDecision to ScreeningDecision
        final_decision_map = {
            FinalDecision.INCLUDE: ScreeningDecision.INCLUDE,
            FinalDecision.EXCLUDE: ScreeningDecision.EXCLUDE,
            FinalDecision.MAYBE: ScreeningDecision.MAYBE
        }
        
        final_decision = final_decision_map.get(decision_result.final_decision, ScreeningDecision.UNCERTAIN)
        
        return StructuredScreeningResult(
            paper_id=paper_id,
            final_decision=final_decision,
            decision_reasoning=f"{decision_result.decision_reasoning} | Logic: {decision_result.logic_rule_applied}",
            program_recognition=make_criteria_assessment("program_recognition"),
            participants_lmic=make_criteria_assessment("participants_lmic"),
            component_a_cash_support=make_criteria_assessment("component_a_cash_support"),
            component_b_productive_assets=make_criteria_assessment("component_b_productive_assets"),
            relevant_outcomes=make_criteria_assessment("relevant_outcomes"),
            appropriate_study_design=make_criteria_assessment("appropriate_study_design"),
            publication_year_2004_plus=make_criteria_assessment("publication_year_2004_plus"),
            completed_study=make_criteria_assessment("completed_study"),
            model_used=self.model_config.model_name,
            raw_response=raw_response,
            processing_time=processing_time
        )

def test_integrated_screener():
    """Test the integrated screener."""
    import yaml
    from src.models import ModelConfig, Paper
    
    print("🧪 TESTING INTEGRATED SCREENER")
    print("=" * 35)
    
    # Load config
    config_path = Path("config/config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    model_config = ModelConfig(
        model_name=config['models']['primary']['model_name'],
        api_url="https://openrouter.ai/api/v1",
        api_key=config['openrouter']['api_key'],
        provider="openrouter",
        temperature=config['models']['primary']['temperature'],
        max_tokens=config['models']['primary']['max_tokens']
    )
    
    screener = IntegratedStructuredScreener(model_config)
    
    # Test paper
    test_paper = Paper(
        paper_id="test_001",
        title="Test Economic Inclusion Program",
        authors=["Test Author"],
        abstract="We evaluate a graduation program in Bangladesh providing monthly cash stipends and productive asset transfers (livestock, equipment) to ultra-poor households. Using a randomized controlled trial with 1,200 households, we measure impacts on income, assets, and expenditure over 24 months. Results show significant improvements. Published in 2020.",
        year=2020,
        journal="Test Journal"
    )
    
    print("📄 Test Paper:")
    print(f"   Title: {test_paper.title}")
    print(f"   Abstract: {test_paper.abstract}")
    print()
    
    print("🚀 Screening paper...")
    result = screener.screen_paper(test_paper)
    
    print("✅ Screening complete!")
    print()
    print("📊 RESULTS:")
    print(f"   Final Decision: {result.final_decision.value}")
    print(f"   Decision Reasoning: {result.decision_reasoning}")
    print(f"   Processing Time: {result.processing_time:.2f}s")
    print()
    
    print("📋 CRITERIA ASSESSMENTS:")
    criteria_attrs = [
        ('participants_lmic', 'LMIC Participants'),
        ('component_a_cash_support', 'Cash Support'),
        ('component_b_productive_assets', 'Productive Assets'),
        ('relevant_outcomes', 'Relevant Outcomes'),
        ('appropriate_study_design', 'Study Design'),
        ('publication_year_2004_plus', 'Year 2004+'),
        ('completed_study', 'Completed Study')
    ]
    
    for attr_name, display_name in criteria_attrs:
        if hasattr(result, attr_name):
            criterion = getattr(result, attr_name)
            print(f"   • {display_name}: {criterion.assessment}")
            print(f"     {criterion.reasoning[:80]}...")
    
    print()
    print("🎉 Integrated screener test complete!")

if __name__ == "__main__":
    test_integrated_screener()
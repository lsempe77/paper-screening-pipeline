#!/usr/bin/env python3
"""
Decision logic processor for structured screening.
Takes LLM criteria assessments and applies deterministic decision rules.
"""

import json
from typing import Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class CriteriaAssessment(Enum):
    YES = "YES"
    NO = "NO"
    UNCLEAR = "UNCLEAR"

class FinalDecision(Enum):
    INCLUDE = "INCLUDE"
    EXCLUDE = "EXCLUDE"
    MAYBE = "MAYBE"

@dataclass
class ScreeningResult:
    """Result from screening with deterministic decision logic."""
    criteria_assessments: Dict[str, CriteriaAssessment]
    criteria_reasoning: Dict[str, str]
    counts: Dict[str, int]
    final_decision: FinalDecision
    decision_reasoning: str
    logic_rule_applied: str

class ScreeningDecisionProcessor:
    """Processes LLM criteria assessments and applies deterministic decision logic."""
    
    def __init__(self, use_program_filter: bool = True):
        self.use_program_filter = use_program_filter
        
        # Standard 7 criteria
        self.standard_criteria = [
            "participants_lmic",
            "component_a_cash_support", 
            "component_b_productive_assets",
            "relevant_outcomes",
            "appropriate_study_design",
            "publication_year_2004_plus",
            "completed_study"
        ]
        
        # With program filter, we have 8 criteria
        if use_program_filter:
            self.criteria_names = ["program_recognition"] + self.standard_criteria
        else:
            self.criteria_names = self.standard_criteria
    
    def process_llm_response(self, llm_response: str) -> ScreeningResult:
        """Process LLM response and apply decision logic."""
        
        # Parse JSON response
        try:
            # Clean and extract JSON
            cleaned_response = llm_response.replace('"', '"').replace('"', '"').replace("'", "'")
            
            if "```json" in cleaned_response:
                start = cleaned_response.find("```json") + 7
                end = cleaned_response.find("```", start)
                if end == -1:
                    cleaned_response = cleaned_response[start:].strip()
                else:
                    cleaned_response = cleaned_response[start:end].strip()
            elif "```" in cleaned_response:
                start = cleaned_response.find("```") + 3
                end = cleaned_response.find("```", start)
                if end == -1:
                    cleaned_response = cleaned_response[start:].strip()
                else:
                    cleaned_response = cleaned_response[start:end].strip()
            
            data = json.loads(cleaned_response)
            
        except json.JSONDecodeError as e:
            # Return error result if JSON parsing fails
            return self._create_error_result(f"JSON parsing failed: {e}")
        
        # Extract criteria evaluations
        criteria_eval = data.get('criteria_evaluation', {})
        
        # Validate all required criteria are present (program_recognition is optional)
        required_criteria = [c for c in self.criteria_names if c != 'program_recognition']
        
        # Map publication_year from LLM response to publication_year_2004_plus internally
        if 'publication_year' in criteria_eval and 'publication_year_2004_plus' not in criteria_eval:
            criteria_eval['publication_year_2004_plus'] = criteria_eval['publication_year']
        
        missing_criteria = [name for name in required_criteria if name not in criteria_eval]
        if missing_criteria:
            return self._create_error_result(f"Missing criteria: {missing_criteria}")
        
        # Parse assessments and reasoning
        criteria_assessments = {}
        criteria_reasoning = {}
        
        for criterion_name in self.criteria_names:
            criterion_data = criteria_eval.get(criterion_name, {})
            
            # If program_recognition is missing, default to UNCLEAR
            if criterion_name == 'program_recognition' and not criterion_data:
                criteria_assessments[criterion_name] = CriteriaAssessment.UNCLEAR
                criteria_reasoning[criterion_name] = "Program not identified in abstract"
                continue
            
            if not isinstance(criterion_data, dict):
                return self._create_error_result(f"Invalid criterion data for {criterion_name}")
            
            # Special handling for publication_year (extract and assess in Python)
            if criterion_name == 'publication_year_2004_plus':
                # Check if we have the new format with year_extracted
                if 'year_extracted' in criterion_data:
                    year_str = criterion_data.get('year_extracted', 'Year not provided')
                    reasoning = criterion_data.get('reasoning', 'No reasoning provided')
                    
                    # Python assessment of year >= 2004
                    if year_str == 'Year not provided' or not year_str.strip().isdigit():
                        criteria_assessments[criterion_name] = CriteriaAssessment.UNCLEAR
                        criteria_reasoning[criterion_name] = f"Year extraction: {reasoning}"
                    else:
                        year = int(year_str.strip())
                        if year >= 2004:
                            criteria_assessments[criterion_name] = CriteriaAssessment.YES
                            criteria_reasoning[criterion_name] = f"Year {year} >= 2004 (extracted, assessed in Python)"
                        else:
                            criteria_assessments[criterion_name] = CriteriaAssessment.NO
                            criteria_reasoning[criterion_name] = f"Year {year} < 2004 (extracted, assessed in Python)"
                    continue
                # Fall back to old format if year_extracted not present
            
            assessment_str = criterion_data.get('assessment', 'UNCLEAR').upper()
            reasoning = criterion_data.get('reasoning', 'No reasoning provided')
            
            # Validate assessment
            try:
                assessment = CriteriaAssessment(assessment_str)
                criteria_assessments[criterion_name] = assessment
                criteria_reasoning[criterion_name] = reasoning
            except ValueError:
                return self._create_error_result(f"Invalid assessment '{assessment_str}' for {criterion_name}")
        
        # POST-PROCESSING CORRECTION: Pure cash transfer programs
        self._apply_cash_transfer_correction(criteria_assessments, criteria_reasoning)
        
        # Count assessments (EXCLUDING program_recognition from counts)
        criteria_for_counting = {k: v for k, v in criteria_assessments.items() 
                                if k != 'program_recognition'}
        
        counts = {
            'YES': sum(1 for a in criteria_for_counting.values() if a == CriteriaAssessment.YES),
            'NO': sum(1 for a in criteria_for_counting.values() if a == CriteriaAssessment.NO),
            'UNCLEAR': sum(1 for a in criteria_for_counting.values() if a == CriteriaAssessment.UNCLEAR)
        }
        
        # Apply deterministic decision logic
        final_decision, decision_reasoning, logic_rule = self._apply_decision_logic(
            criteria_assessments, counts
        )
        
        return ScreeningResult(
            criteria_assessments=criteria_assessments,
            criteria_reasoning=criteria_reasoning,
            counts=counts,
            final_decision=final_decision,
            decision_reasoning=decision_reasoning,
            logic_rule_applied=logic_rule
        )
    
    def _apply_decision_logic(self, 
                            criteria_assessments: Dict[str, CriteriaAssessment], 
                            counts: Dict[str, int]) -> Tuple[FinalDecision, str, str]:
        """Apply deterministic decision logic based on criteria counts."""
        
        yes_count = counts['YES']
        no_count = counts['NO'] 
        unclear_count = counts['UNCLEAR']
        
        # PRIORITY RULE: Check program_recognition if using program filter
        if self.use_program_filter and 'program_recognition' in criteria_assessments:
            prog_assessment = criteria_assessments['program_recognition']
            prog_reasoning = criteria_assessments.get('program_recognition', '')
            
            # Rule 0a: Program recognized as RELEVANT (YES) → INCLUDE
            # BUT STILL RESPECT STUDY DESIGN NO (must be primary impact evaluation)
            if prog_assessment == CriteriaAssessment.YES:
                # Check if study design is NO (e.g., synthesis, policy analysis, comparative study)
                study_design_assessment = criteria_assessments.get('appropriate_study_design')
                if study_design_assessment == CriteriaAssessment.NO:
                    decision_reasoning = f"EXCLUDE: Known relevant program BUT inappropriate study design (synthesis/review/policy analysis)"
                    logic_rule = "Rule 0a-override: Program Recognition YES but Study Design NO → EXCLUDE"
                    return FinalDecision.EXCLUDE, decision_reasoning, logic_rule
                
                # Otherwise, include based on program recognition
                decision_reasoning = f"INCLUDE: Known relevant program identified"
                logic_rule = "Rule 0a: Program Recognition YES → INCLUDE"
                return FinalDecision.INCLUDE, decision_reasoning, logic_rule
            
            # Rule 0b: Program recognized as IRRELEVANT (NO) → EXCLUDE  
            if prog_assessment == CriteriaAssessment.NO:
                decision_reasoning = f"EXCLUDE: Known irrelevant program identified"
                logic_rule = "Rule 0b: Program Recognition NO → EXCLUDE"
                return FinalDecision.EXCLUDE, decision_reasoning, logic_rule
            
            # If UNCLEAR, continue with standard rules below
        
        # Rule 1: ANY NO → EXCLUDE (excluding program_recognition which was checked above)
        if no_count > 0:
            no_criteria = [name for name, assessment in criteria_assessments.items() 
                          if assessment == CriteriaAssessment.NO and name != 'program_recognition']
            if no_criteria:  # Only apply if there are actual NO criteria (not just program_recognition)
                decision_reasoning = f"EXCLUDE: {len(no_criteria)} criteria marked as NO ({', '.join(no_criteria)})"
                logic_rule = "Rule 1: ANY NO → EXCLUDE"
                return FinalDecision.EXCLUDE, decision_reasoning, logic_rule
        
        # Rule 2: ALL YES → INCLUDE (7 standard criteria, excluding program_recognition)
        if yes_count == 7 and no_count == 0 and unclear_count == 0:
            decision_reasoning = f"INCLUDE: All 7 criteria marked as YES"
            logic_rule = "Rule 2: ALL YES → INCLUDE"
            return FinalDecision.INCLUDE, decision_reasoning, logic_rule
        
        # Rule 3: NO NO criteria AND some UNCLEAR → MAYBE
        if no_count == 0 and unclear_count > 0:
            unclear_criteria = [name for name, assessment in criteria_assessments.items() 
                              if assessment == CriteriaAssessment.UNCLEAR]
            decision_reasoning = f"MAYBE: 0 NO criteria, {unclear_count} unclear ({', '.join(unclear_criteria)})"
            logic_rule = "Rule 3: 0 NO + some UNCLEAR → MAYBE"
            return FinalDecision.MAYBE, decision_reasoning, logic_rule
        
        # This should never happen if logic is correct
        decision_reasoning = f"ERROR: Unexpected criteria pattern {yes_count}Y/{no_count}N/{unclear_count}U"
        logic_rule = "ERROR: No rule matched"
        return FinalDecision.MAYBE, decision_reasoning, logic_rule
    
    def _apply_cash_transfer_correction(self, 
                                      criteria_assessments: Dict[str, CriteriaAssessment],
                                      criteria_reasoning: Dict[str, str]) -> None:
        """
        Post-processing correction for pure cash transfer programs.
        If program provides only cash support but LLM incorrectly marked productive assets as YES
        due to measuring impacts on asset ownership, correct it to NO.
        """
        # Only apply if both criteria exist
        if ('component_a_cash_support' not in criteria_assessments or 
            'component_b_productive_assets' not in criteria_assessments):
            return
            
        cash_support = criteria_assessments['component_a_cash_support']
        assets = criteria_assessments['component_b_productive_assets'] 
        assets_reasoning = criteria_reasoning.get('component_b_productive_assets', '')
        
        # Pattern: Cash=YES, Assets=YES, but reasoning mentions "impacts on ownership" (not direct provision)
        if (cash_support == CriteriaAssessment.YES and 
            assets == CriteriaAssessment.YES and
            self._is_impact_measurement_reasoning(assets_reasoning)):
            
            # Override to NO - this is likely a pure cash transfer program
            criteria_assessments['component_b_productive_assets'] = CriteriaAssessment.NO
            criteria_reasoning['component_b_productive_assets'] = (
                f"CORRECTED: Original reasoning indicated impact measurement, not direct provision. "
                f"Pure cash transfer programs don't provide productive assets. "
                f"Original: {assets_reasoning[:100]}..."
            )
    
    def _is_impact_measurement_reasoning(self, reasoning: str) -> bool:
        """
        Detect if reasoning describes impact measurement rather than program provision.
        """
        reasoning_lower = reasoning.lower()
        
        # Phrases that indicate impact measurement (not program provision)
        impact_phrases = [
            'impacts on',
            'impact on', 
            'effects on',
            'noticeable impacts',
            'program has',
            'ownership of',
            'asset ownership',
            'asset accumulation',
            'increased ownership',
            'improved ownership'
        ]
        
        # Phrases that indicate direct provision (legitimate YES)
        provision_phrases = [
            'program provides',
            'program gives',
            'program transfers',
            'beneficiaries receive',
            'participants receive',
            'direct transfer',
            'livestock grants',
            'asset transfers'
        ]
        
        # If it contains impact measurement language and no provision language
        has_impact_language = any(phrase in reasoning_lower for phrase in impact_phrases)
        has_provision_language = any(phrase in reasoning_lower for phrase in provision_phrases)
        
        return has_impact_language and not has_provision_language
    
    def _create_error_result(self, error_message: str) -> ScreeningResult:
        """Create error result when processing fails."""
        error_assessments = {name: CriteriaAssessment.UNCLEAR for name in self.criteria_names}
        error_reasoning = {name: f"Error: {error_message}" for name in self.criteria_names}
        error_counts = {'YES': 0, 'NO': 0, 'UNCLEAR': len(self.criteria_names)}
        
        return ScreeningResult(
            criteria_assessments=error_assessments,
            criteria_reasoning=error_reasoning,
            counts=error_counts,
            final_decision=FinalDecision.MAYBE,
            decision_reasoning=f"Processing error: {error_message}",
            logic_rule_applied="ERROR: Processing failed"
        )
    
    def format_result_summary(self, result: ScreeningResult) -> str:
        """Format result for display."""
        counts = result.counts
        summary = f"📊 {counts['YES']}Y/{counts['NO']}N/{counts['UNCLEAR']}U → {result.final_decision.value}"
        summary += f"\n🎯 {result.decision_reasoning}"
        summary += f"\n📋 Logic: {result.logic_rule_applied}"
        return summary

def test_decision_processor():
    """Test the decision processor with sample data."""
    processor = ScreeningDecisionProcessor()
    
    # Test case 1: All YES → INCLUDE
    test_response_1 = '''
    {
        "criteria_evaluation": {
            "participants_lmic": {"assessment": "YES", "reasoning": "Bangladesh is LMIC"},
            "component_a_cash_support": {"assessment": "YES", "reasoning": "Monthly cash stipends mentioned"},
            "component_b_productive_assets": {"assessment": "YES", "reasoning": "Livestock transfers mentioned"},
            "relevant_outcomes": {"assessment": "YES", "reasoning": "Income and assets measured"},
            "appropriate_study_design": {"assessment": "YES", "reasoning": "RCT methodology"},
            "publication_year_2004_plus": {"assessment": "YES", "reasoning": "Published 2020"},
            "completed_study": {"assessment": "YES", "reasoning": "Results presented"}
        }
    }
    '''
    
    result_1 = processor.process_llm_response(test_response_1)
    print("Test 1 - All YES:")
    print(processor.format_result_summary(result_1))
    print()
    
    # Test case 2: Has NO → EXCLUDE
    test_response_2 = '''
    {
        "criteria_evaluation": {
            "participants_lmic": {"assessment": "YES", "reasoning": "India is LMIC"},
            "component_a_cash_support": {"assessment": "YES", "reasoning": "Cash transfers mentioned"},
            "component_b_productive_assets": {"assessment": "NO", "reasoning": "No productive assets provided"},
            "relevant_outcomes": {"assessment": "YES", "reasoning": "Income measured"},
            "appropriate_study_design": {"assessment": "YES", "reasoning": "RCT methodology"},
            "publication_year_2004_plus": {"assessment": "YES", "reasoning": "Published 2019"},
            "completed_study": {"assessment": "YES", "reasoning": "Study completed"}
        }
    }
    '''
    
    result_2 = processor.process_llm_response(test_response_2)
    print("Test 2 - Has NO:")
    print(processor.format_result_summary(result_2))
    print()
    
    # Test case 3: Some UNCLEAR → MAYBE
    test_response_3 = '''
    {
        "criteria_evaluation": {
            "participants_lmic": {"assessment": "YES", "reasoning": "Kenya is LMIC"},
            "component_a_cash_support": {"assessment": "UNCLEAR", "reasoning": "Support type not specified"},
            "component_b_productive_assets": {"assessment": "UNCLEAR", "reasoning": "Asset component unclear"},
            "relevant_outcomes": {"assessment": "UNCLEAR", "reasoning": "Outcomes not clearly specified"},
            "appropriate_study_design": {"assessment": "YES", "reasoning": "Survey methodology mentioned"},
            "publication_year_2004_plus": {"assessment": "UNCLEAR", "reasoning": "Year not provided"},
            "completed_study": {"assessment": "YES", "reasoning": "Past tense used"}
        }
    }
    '''
    
    result_3 = processor.process_llm_response(test_response_3)
    print("Test 3 - Some UNCLEAR:")
    print(processor.format_result_summary(result_3))
    print()

if __name__ == "__main__":
    test_decision_processor()
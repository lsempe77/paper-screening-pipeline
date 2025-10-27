"""
Test how the updated prompt handles papers with missing abstracts.
Tests Paper 121340461 - Poverty eradication Nigeria (no abstract available).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pandas as pd
import rispy
from integrated_screener import IntegratedStructuredScreener
from decision_processor import ScreeningDecisionProcessor
import yaml

# Load config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize screener
screener = IntegratedStructuredScreener(config)
processor = ScreeningDecisionProcessor()

# Load validation data
validation_df = pd.read_excel('data/input/s14above.xlsx')

# Get Paper 121340461
paper = validation_df[validation_df['ID'] == 121340461].iloc[0]
print(f"\n{'='*80}")
print(f"Testing Paper: {paper['ID']}")
print(f"Title: {paper['Title']}")
print(f"Human Label: {paper.get('decision', 'N/A')}")
print(f"{'='*80}\n")

# Load abstract from corpus
corpus_path = 'data/input/Not excluded.txt'
with open(corpus_path, 'r', encoding='utf-8') as f:
    entries = list(rispy.load(f))

# Find matching entry
abstract = None
for entry in entries:
    if str(entry.get('id')) == str(paper['ID']):
        abstract = entry.get('abstract', '')
        break

print(f"Abstract found: {'YES' if abstract else 'NO'}")
if abstract:
    print(f"Abstract length: {len(abstract)} chars")
    print(f"Abstract preview: {abstract[:200]}...")
else:
    print("Abstract: [MISSING - Will evaluate from title only]")

print(f"\n{'='*80}")
print("LLM EVALUATION (with updated prompt for missing abstracts)")
print(f"{'='*80}\n")

# Prepare paper dict for screener
paper_dict = {
    'title': paper['Title'],
    'abstract': abstract if abstract else ""
}

# Read the program filter prompt
with open('prompts/structured_screening_with_program_filter.txt', 'r', encoding='utf-8') as f:
    prompt_template = f.read()

# Screen the paper
result = screener.screen_paper(
    paper=paper_dict,
    prompt_template=prompt_template
)

print("\nCRITERIA ASSESSMENT:")
print(f"Program Recognition: {result.program_recognition.assessment} - {result.program_recognition.reasoning}")
print(f"LMIC: {result.participants_lmic.assessment} - {result.participants_lmic.reasoning}")
print(f"Cash Support: {result.component_a_cash_support.assessment} - {result.component_a_cash_support.reasoning}")
print(f"Productive Assets: {result.component_b_productive_assets.assessment} - {result.component_b_productive_assets.reasoning}")
print(f"Outcomes: {result.relevant_outcomes.assessment} - {result.relevant_outcomes.reasoning}")
print(f"Study Design: {result.appropriate_study_design.assessment} - {result.appropriate_study_design.reasoning}")
print(f"Year 2004+: {result.publication_year_2004_plus.assessment} - {result.publication_year_2004_plus.reasoning}")
print(f"Completed: {result.completed_study.assessment} - {result.completed_study.reasoning}")

# Get the final decision from the result
print(f"\n{'='*80}")
print(f"FINAL DECISION: {result.final_decision}")
print(f"Decision Reasoning: {result.decision_reasoning}")
print(f"{'='*80}\n")

# Count YES/NO/UNCLEAR
counts = result.count_criteria_by_status()
print(f"Summary (all 8 criteria including program_recognition):")
print(f"  YES: {counts['YES']}/8")
print(f"  NO: {counts['NO']}/8")
print(f"  UNCLEAR: {counts['UNCLEAR']}/8")

print(f"\nExpected: With missing abstract, should have mostly UNCLEAR (not NO)")
print(f"Expected: Should result in MAYBE decision (pass to full-text screening)")

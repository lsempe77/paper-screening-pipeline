#!/usr/bin/env python3
"""
Test enhanced prompts with real API calls on problematic papers.
"""

import sys
import os
import json
import time
import openai
import yaml
from pathlib import Path

# Add the src directory to the path
script_dir = Path(__file__).parent
src_dir = script_dir / "src"
sys.path.insert(0, str(src_dir))

from src.models import ModelConfig
from src.parsers import RISParser


def load_test_papers():
    """Load some problematic papers from original validation."""
    
    # Load original validation results to find problematic papers
    results_file = Path("data/output/structured_validation_results.json")
    if not results_file.exists():
        print("❌ Original validation results not found")
        return []
    
    with open(results_file, 'r', encoding='utf-8') as f:
        original_results = json.load(f)
    
    # Find papers with different types of issues
    test_cases = []
    
    # 1. Papers with 8/8 UNCLEAR (parsing failures)
    parsing_failures = [r for r in original_results if 
                       'criteria_summary' in r and 
                       sum(1 for v in r['criteria_summary'].values() if v == 'UNCLEAR') == 8]
    
    # 2. Papers with high UNCLEAR rates but not complete failures
    high_unclear = [r for r in original_results if 
                   'criteria_summary' in r and 
                   4 <= sum(1 for v in r['criteria_summary'].values() if v == 'UNCLEAR') <= 6]
    
    # 3. Papers that worked well (for comparison)
    good_papers = [r for r in original_results if 
                  'criteria_summary' in r and 
                  sum(1 for v in r['criteria_summary'].values() if v == 'UNCLEAR') <= 1]
    
    # Select test cases
    test_cases.extend(parsing_failures[:2])  # 2 parsing failures
    test_cases.extend(high_unclear[:2])      # 2 high unclear
    test_cases.extend(good_papers[:1])       # 1 good paper for comparison
    
    return test_cases


def get_paper_abstract(paper_id):
    """Get the abstract for a specific paper from the input files."""
    
    # Search in both included and excluded files
    for filename in ['included.txt', 'excluded.txt']:
        file_path = Path(f"data/input/{filename}")
        if file_path.exists():
            parser = RISParser()
            papers = parser.parse_file(str(file_path))
            
            for paper in papers:
                if paper.paper_id == paper_id:
                    return paper.abstract
    
    return None


def test_enhanced_prompt():
    """Test the enhanced prompt on selected papers."""
    
    print("🧪 TESTING ENHANCED PROMPT WITH REAL API CALLS")
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
        provider="openrouter",
        api_key=config['openrouter']['api_key'],
        model_name=config['models']['primary']['model_name'],
        temperature=config['models']['primary']['temperature'],
        max_tokens=config['models']['primary']['max_tokens']
    )
    
    # Setup OpenAI client
    openai.api_key = model_config.api_key
    openai.api_base = "https://openrouter.ai/api/v1"
    
    print("✅ Configuration loaded")
    print(f"Model: {model_config.model_name}")
    print()
    
    # Load test papers
    test_papers = load_test_papers()
    if not test_papers:
        print("❌ No test papers found")
        return
    
    print(f"📋 Selected {len(test_papers)} test papers:")
    for paper in test_papers:
        unclear_count = sum(1 for v in paper['criteria_summary'].values() if v == 'UNCLEAR')
        decision = paper.get('ai_decision', 'UNKNOWN')
        print(f"• {paper['paper_id']}: {decision} ({unclear_count}/8 UNCLEAR)")
    print()
    
    # Load the enhanced prompt
    enhanced_prompt_path = Path("prompts/structured_screening_enhanced.txt")
    if not enhanced_prompt_path.exists():
        print("❌ Enhanced prompt file not found")
        return
    
    with open(enhanced_prompt_path, 'r', encoding='utf-8') as f:
        enhanced_prompt = f.read()
    
    print(f"📝 Using enhanced prompt: {enhanced_prompt_path}")
    print()
    
    results = []
    
    for i, paper_data in enumerate(test_papers, 1):
        paper_id = paper_data['paper_id']
        title = paper_data.get('title', 'No title')
        expected = paper_data.get('expected_decision', 'UNKNOWN')
        
        # Get original results for comparison
        original_unclear_count = sum(1 for v in paper_data['criteria_summary'].values() if v == 'UNCLEAR')
        original_decision = paper_data.get('ai_decision', 'UNKNOWN')
        
        print(f"🔬 Test {i}/{len(test_papers)}: {paper_id}")
        print(f"   Title: {title[:80]}...")
        print(f"   Original: {original_decision} ({original_unclear_count}/8 UNCLEAR)")
        print(f"   Expected: {expected}")
        
        # Load the actual abstract for this paper
        abstract = get_paper_abstract(paper_id)
        if not abstract:
            print(f"   ❌ Could not find abstract for {paper_id}")
            continue
        
        try:
            # Make API call with enhanced prompt
            print(f"   🚀 Making API call...")
            response = openai.ChatCompletion.create(
                model=model_config.model_name,
                messages=[
                    {"role": "system", "content": enhanced_prompt},
                    {"role": "user", "content": f"Evaluate this research paper abstract:\n\n{abstract}"}
                ],
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            parsing_success = False
            enhanced_criteria = {}
            enhanced_decision = "UNCERTAIN"
            enhanced_reasoning = ""
            
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
                parsing_success = True
                
                # Extract criteria
                criteria_eval = result_data.get('criteria_evaluation', {})
                for criterion_key, criterion_data in criteria_eval.items():
                    if isinstance(criterion_data, dict):
                        assessment = criterion_data.get('assessment', 'UNCLEAR')
                        enhanced_criteria[criterion_key] = assessment
                
                enhanced_decision = result_data.get('final_decision', 'UNCERTAIN')
                enhanced_reasoning = result_data.get('decision_reasoning', 'No reasoning')
                
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON parsing still failed: {e}")
                parsing_success = False
                
                # Default all criteria to UNCLEAR if parsing fails
                enhanced_criteria = {
                    'participants_lmic': 'UNCLEAR',
                    'component_a_cash_support': 'UNCLEAR',
                    'component_b_productive_assets': 'UNCLEAR',
                    'dual_component_overall': 'UNCLEAR',
                    'relevant_outcomes': 'UNCLEAR',
                    'appropriate_study_design': 'UNCLEAR',
                    'publication_year_2004_plus': 'UNCLEAR',
                    'completed_study': 'UNCLEAR'
                }
                enhanced_decision = "UNCERTAIN"
                enhanced_reasoning = f"JSON parsing failed: {str(e)}"
            
            # Count UNCLEAR criteria
            enhanced_unclear_count = sum(1 for v in enhanced_criteria.values() if v == 'UNCLEAR')
            
            print(f"   📊 Enhanced result: {enhanced_decision} ({enhanced_unclear_count}/8 UNCLEAR)")
            print(f"   🔧 Parsing success: {'✅' if parsing_success else '❌'}")
            
            # Show improvement
            unclear_improvement = original_unclear_count - enhanced_unclear_count
            if unclear_improvement > 0:
                print(f"   🎉 UNCLEAR reduction: -{unclear_improvement} criteria")
            elif unclear_improvement < 0:
                print(f"   ⚠️  UNCLEAR increase: +{abs(unclear_improvement)} criteria")
            else:
                print(f"   ➡️  UNCLEAR unchanged: {enhanced_unclear_count} criteria")
            
            if original_decision != enhanced_decision:
                print(f"   📝 Decision changed: {original_decision} → {enhanced_decision}")
            
            print(f"   💭 Reasoning: {enhanced_reasoning[:100]}...")
            print()
            
            # Store results
            results.append({
                'paper_id': paper_id,
                'title': title,
                'expected_decision': expected,
                'original_decision': original_decision,
                'original_unclear_count': original_unclear_count,
                'enhanced_decision': enhanced_decision,
                'enhanced_unclear_count': enhanced_unclear_count,
                'enhanced_criteria': enhanced_criteria,
                'parsing_success': parsing_success,
                'unclear_improvement': unclear_improvement,
                'enhanced_reasoning': enhanced_reasoning,
                'raw_response': response_text[:500]  # First 500 chars
            })
            
            # Small delay to avoid rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Error testing paper {paper_id}: {e}")
            continue
    
    # Summary analysis
    print("📊 ENHANCED PROMPT TEST SUMMARY")
    print("=" * 35)
    
    if results:
        # Calculate improvements
        total_unclear_reduction = sum(r['unclear_improvement'] for r in results)
        parsing_success_rate = sum(1 for r in results if r['parsing_success']) / len(results) * 100
        papers_improved = sum(1 for r in results if r['unclear_improvement'] > 0)
        
        print(f"✅ Papers tested: {len(results)}")
        print(f"🔧 JSON parsing success rate: {parsing_success_rate:.1f}%")
        print(f"📉 Total UNCLEAR criteria reduced: {total_unclear_reduction}")
        print(f"📈 Papers with reduced UNCLEAR: {papers_improved}/{len(results)}")
        print()
        
        # Show individual improvements
        print("📋 Individual paper improvements:")
        for result in results:
            improvement = result['unclear_improvement']
            status = "🎉 IMPROVED" if improvement > 0 else "➡️ SAME" if improvement == 0 else "⚠️ WORSE"
            parsing = "✅" if result['parsing_success'] else "❌"
            print(f"   • {result['paper_id']}: {improvement:+d} UNCLEAR | Parsing: {parsing} | {status}")
        
        # Save results
        output_file = Path("data/output/enhanced_prompt_test_results.json")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved: {output_file}")
        
        # Quick comparison with original problems
        print()
        print("🔍 KEY FINDINGS:")
        if parsing_success_rate > 80:
            print("✅ JSON parsing greatly improved!")
        elif parsing_success_rate > 50:
            print("🟡 JSON parsing partially improved")
        else:
            print("❌ JSON parsing still problematic")
            
        if total_unclear_reduction > 0:
            print(f"✅ Overall UNCLEAR reduction achieved: -{total_unclear_reduction}")
        else:
            print("❌ No overall UNCLEAR reduction")
        
        return results
    
    else:
        print("❌ No results to analyze")
        return []


if __name__ == "__main__":
    test_enhanced_prompt()
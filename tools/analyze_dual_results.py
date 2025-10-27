#!/usr/bin/env python3
"""
Dual-Engine Analysis Tool

Analyzes the results from dual-engine screening to provide insights
on model performance, agreement patterns, and recommendations.
"""

import json
import pandas as pd
import argparse
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter

def load_dual_results(filepath):
    """Load dual-engine screening results."""
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Results file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def analyze_agreement_patterns(results):
    """Analyze patterns in agreement/disagreement between engines."""
    
    print("🔍 AGREEMENT PATTERN ANALYSIS")
    print("=" * 30)
    
    agreements = []
    disagreements = []
    
    for result in results:
        if result['comparison']['both_success']:
            if result['comparison']['agreement']:
                agreements.append(result)
            else:
                disagreements.append(result)
    
    print(f"✅ Agreements: {len(agreements)}")
    print(f"⚠️  Disagreements: {len(disagreements)}")
    
    if len(disagreements) > 0:
        print(f"\n📊 Disagreement breakdown:")
        
        # Analyze disagreement types
        disagreement_types = Counter()
        for result in disagreements:
            pattern = f"{result['engine1']['decision']} → {result['engine2']['decision']}"
            disagreement_types[pattern] += 1
        
        for pattern, count in disagreement_types.most_common():
            pct = count / len(disagreements) * 100
            print(f"   {pattern}: {count} ({pct:.1f}%)")
        
        # Sample some disagreements for manual review
        print(f"\n📄 Sample disagreements for review:")
        for i, result in enumerate(disagreements[:5]):
            print(f"\n{i+1}. {result['title'][:80]}...")
            print(f"   Engine 1: {result['engine1']['decision'].upper()}")
            print(f"   Engine 2: {result['engine2']['decision'].upper()}")
            print(f"   Year: {result['year']}")
    
    return agreements, disagreements

def analyze_criteria_differences(results):
    """Analyze differences at the criteria level."""
    
    print("\n🎯 CRITERIA-LEVEL ANALYSIS")
    print("=" * 26)
    
    criteria_names = [
        'participants_lmic',
        'component_a_cash_support',
        'component_b_productive_assets',
        'relevant_outcomes',
        'appropriate_study_design',
        'publication_year_2004_plus',
        'completed_study'
    ]
    
    criteria_disagreements = defaultdict(int)
    total_comparisons = 0
    
    for result in results:
        if result['comparison']['both_success']:
            total_comparisons += 1
            
            # Check each criterion
            for criterion in criteria_names:
                if (criterion in result['engine1'].get('criteria', {}) and 
                    criterion in result['engine2'].get('criteria', {})):
                    
                    assessment1 = result['engine1']['criteria'][criterion]['assessment']
                    assessment2 = result['engine2']['criteria'][criterion]['assessment']
                    
                    if assessment1 != assessment2:
                        criteria_disagreements[criterion] += 1
    
    print("Criterion disagreement rates:")
    for criterion in criteria_names:
        if total_comparisons > 0:
            rate = criteria_disagreements[criterion] / total_comparisons * 100
            print(f"   {criterion}: {criteria_disagreements[criterion]}/{total_comparisons} ({rate:.1f}%)")
    
    return criteria_disagreements

def create_comparison_report(data, output_dir="data/output"):
    """Create a comprehensive comparison report."""
    
    print("\n📝 GENERATING COMPARISON REPORT")
    print("=" * 33)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Basic statistics
    metadata = data['metadata']
    analysis = data['analysis']
    results = data['results']
    
    # Create detailed analysis
    agreements, disagreements = analyze_agreement_patterns(results)
    criteria_disagreements = analyze_criteria_differences(results)
    
    # Performance analysis
    print(f"\n⚡ PERFORMANCE METRICS")
    print("=" * 20)
    
    engine1_name = metadata['engine1_model']
    engine2_name = metadata['engine2_model']
    
    print(f"🤖 {engine1_name}:")
    print(f"   Average time: {analysis['engine1_avg_time']:.1f}s")
    print(f"   Decisions: {analysis['engine1_decisions']}")
    
    print(f"\n🤖 {engine2_name}:")
    print(f"   Average time: {analysis['engine2_avg_time']:.1f}s")
    print(f"   Decisions: {analysis['engine2_decisions']}")
    
    # Generate recommendations
    recommendations = generate_recommendations(analysis, agreements, disagreements)
    
    # Create report file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(output_dir, f"dual_engine_report_{timestamp}.md")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# Dual-Engine Screening Comparison Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"## Models Compared\n\n")
        f.write(f"- **Engine 1:** {engine1_name}\n")
        f.write(f"- **Engine 2:** {engine2_name}\n\n")
        
        f.write(f"## Summary Statistics\n\n")
        f.write(f"- **Total papers:** {analysis['total_papers']}\n")
        f.write(f"- **Both engines successful:** {analysis['both_success']} ({analysis['both_success']/analysis['total_papers']*100:.1f}%)\n")
        f.write(f"- **Agreement rate:** {analysis['agreement_rate']:.1f}%\n")
        f.write(f"- **Disagreements:** {analysis['disagreements']}\n\n")
        
        f.write(f"## Performance Comparison\n\n")
        f.write(f"| Metric | {engine1_name} | {engine2_name} |\n")
        f.write(f"|--------|------------|------------|\n")
        f.write(f"| Average time (s) | {analysis['engine1_avg_time']:.1f} | {analysis['engine2_avg_time']:.1f} |\n")
        f.write(f"| Include decisions | {analysis['engine1_decisions'].get('include', 0)} | {analysis['engine2_decisions'].get('include', 0)} |\n")
        f.write(f"| Exclude decisions | {analysis['engine1_decisions'].get('exclude', 0)} | {analysis['engine2_decisions'].get('exclude', 0)} |\n")
        f.write(f"| Maybe decisions | {analysis['engine1_decisions'].get('maybe', 0)} | {analysis['engine2_decisions'].get('maybe', 0)} |\n\n")
        
        f.write(f"## Recommendations\n\n")
        for rec in recommendations:
            f.write(f"- {rec}\n")
        
        f.write(f"\n## Papers Requiring Human Review\n\n")
        if disagreements:
            f.write(f"The following {len(disagreements)} papers had disagreements between engines:\n\n")
            for i, result in enumerate(disagreements[:20]):  # Limit to first 20
                f.write(f"{i+1}. **{result['title']}** ({result['year']})\n")
                f.write(f"   - Engine 1: {result['engine1']['decision'].upper()}\n")
                f.write(f"   - Engine 2: {result['engine2']['decision'].upper()}\n")
                f.write(f"   - Paper ID: {result['paper_id']}\n\n")
        else:
            f.write("No disagreements found - all papers had consistent decisions.\n")
    
    print(f"   📄 Report saved to: {report_file}")
    
    # Create CSV with disagreements for easy review
    if disagreements:
        disagreement_file = os.path.join(output_dir, f"disagreements_{timestamp}.csv")
        disagreement_data = []
        
        for result in disagreements:
            disagreement_data.append({
                'paper_id': result['paper_id'],
                'title': result['title'],
                'year': result['year'],
                'journal': result['journal'],
                'engine1_decision': result['engine1']['decision'],
                'engine2_decision': result['engine2']['decision'],
                'engine1_reasoning': result['engine1']['reasoning'][:200] + '...' if len(result['engine1']['reasoning']) > 200 else result['engine1']['reasoning'],
                'engine2_reasoning': result['engine2']['reasoning'][:200] + '...' if len(result['engine2']['reasoning']) > 200 else result['engine2']['reasoning']
            })
        
        df = pd.DataFrame(disagreement_data)
        df.to_csv(disagreement_file, index=False)
        print(f"   📊 Disagreements CSV saved to: {disagreement_file}")
    
    return report_file

def generate_recommendations(analysis, agreements, disagreements):
    """Generate actionable recommendations based on analysis."""
    
    recommendations = []
    
    # Agreement rate recommendations
    if analysis['agreement_rate'] >= 90:
        recommendations.append("✅ **High Agreement:** Both engines show excellent consistency. Either could be used for production.")
    elif analysis['agreement_rate'] >= 75:
        recommendations.append("⚠️ **Moderate Agreement:** Engines show reasonable consistency but disagreements should be reviewed.")
    else:
        recommendations.append("❌ **Low Agreement:** Significant differences between engines. Consider using both in production with human review for disagreements.")
    
    # Performance recommendations
    if analysis['engine1_avg_time'] < analysis['engine2_avg_time']:
        time_diff = analysis['engine2_avg_time'] - analysis['engine1_avg_time']
        recommendations.append(f"⚡ **Performance:** Engine 1 is {time_diff:.1f}s faster on average. Consider for high-volume screening.")
    else:
        time_diff = analysis['engine1_avg_time'] - analysis['engine2_avg_time']
        recommendations.append(f"⚡ **Performance:** Engine 2 is {time_diff:.1f}s faster on average. Consider for high-volume screening.")
    
    # Decision distribution recommendations
    engine1_maybe_rate = analysis['engine1_decisions'].get('maybe', 0) / sum(analysis['engine1_decisions'].values()) * 100
    engine2_maybe_rate = analysis['engine2_decisions'].get('maybe', 0) / sum(analysis['engine2_decisions'].values()) * 100
    
    if engine1_maybe_rate < engine2_maybe_rate:
        recommendations.append(f"🎯 **Decisiveness:** Engine 1 has lower 'maybe' rate ({engine1_maybe_rate:.1f}% vs {engine2_maybe_rate:.1f}%), potentially reducing human review burden.")
    elif engine2_maybe_rate < engine1_maybe_rate:
        recommendations.append(f"🎯 **Decisiveness:** Engine 2 has lower 'maybe' rate ({engine2_maybe_rate:.1f}% vs {engine1_maybe_rate:.1f}%), potentially reducing human review burden.")
    
    # Cost considerations
    recommendations.append("💰 **Cost:** Consider the per-token pricing of each model for large-scale deployment.")
    
    # Quality assurance
    if len(disagreements) > 0:
        recommendations.append(f"🔍 **Quality Assurance:** {len(disagreements)} papers require human review. Consider implementing disagreement resolution protocols.")
    
    return recommendations

def main():
    """Main entry point for analysis tool."""
    
    parser = argparse.ArgumentParser(
        description="Analyze dual-engine screening results",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input JSON file from dual-engine screening"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="data/output",
        help="Output directory for analysis reports"
    )
    
    args = parser.parse_args()
    
    try:
        # Load and analyze results
        data = load_dual_results(args.input)
        
        print(f"📊 DUAL-ENGINE ANALYSIS TOOL")
        print("=" * 30)
        print(f"📄 Loaded results for {data['metadata']['total_papers']} papers")
        print(f"🤖 Engine 1: {data['metadata']['engine1_model']}")
        print(f"🤖 Engine 2: {data['metadata']['engine2_model']}")
        
        # Generate comprehensive report
        report_file = create_comparison_report(data, args.output)
        
        print(f"\n✅ Analysis complete! Check the generated reports for detailed insights.")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Debug the 3 false negative papers to understand why they were excluded.
"""

import sys
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models import ModelConfig, Paper
from integrated_screener import IntegratedStructuredScreener

def debug_false_negatives():
    """Debug the specific papers that were incorrectly excluded."""
    
    print("🔍 DEBUGGING FALSE NEGATIVE PAPERS")
    print("=" * 38)
    print()
    
    # Load config
    config_path = Path("config/config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    model_config = ModelConfig(
        model_name=config['models']['primary']['model_name'],
        api_url="https://openrouter.ai/api/v1",
        api_key=config['openrouter']['api_key'],
        provider="openrouter",
        temperature=0.1,
        max_tokens=1500
    )
    
    screener = IntegratedStructuredScreener(model_config)
    
    # The 3 problematic papers
    false_negative_papers = [
        Paper(
            paper_id="fn_1",
            title="Community Networks And Poverty Reduction Programmes: Evidence From Bangladesh",
            abstract="Whether basic entrepreneurship can be inculcated amongst the poorest in society and serve as a route out of poverty remains an open question. We provide evidence on this issue by looking at the effects of a large-scale asset transfer and training programme which is targeted at the poorest women in rural Bangladesh. We use a randomized control trial research design, and survey all households in the community. This allows us to map the full social network of the beneficiaries, on multiple dimensions of interaction. We find that beneficiaries' wealth levels and occupational structure converge to that of lower-middle class households. Beneficiaries use their newly found wealth to purchase household durables, and improve their human capital, as measured by business skills and their health status. We find the programme affects the composition of beneficiary households' networks: they form ties to wealthier residents after the programme. The programme also affects outcomes among social network members, but has no effect on households that are not socially connected to beneficiaries. Our findings suggest that such programs have effects beyond beneficiary households, and that the network structures and outcomes in targeted communities are transformed by them.",
            year=2009,
            journal="LSE STICERD Working Paper Series"
        ),
        Paper(
            paper_id="fn_2", 
            title="Labor Markets And Poverty In Village Economies",
            abstract="We study how women's choices over labor activities in village economies correlate with poverty and whether enabling the poorest women to take on the activities of their richer counterparts can set them on a sustainable trajectory out of poverty. To do this we conduct a large-scale randomized control trial, covering over 21,000 households in 1,309 villages surveyed four times over a seven-year period, to evaluate a nationwide program in Bangladesh that transfers livestock assets and skills to the poorest women. At baseline, the poorest women mostly engage in low return and seasonal casual wage labor while wealthier women solely engage in livestock rearing. The program enables poor women to start engaging in livestock rearing, increasing their aggregate labor supply and earnings. This leads to asset accumulation (livestock, land, and business assets) and poverty reduction, both sustained after four and seven years. These gains do not crowd out the livestock businesses of noneligible households while the wages these receive for casual jobs increase as the poor reduce their labor supply. Our results show that (i) the poor are able to take on the work activities of the nonpoor but face barriers to doing so, and, (ii) one-off interventions that remove these barriers lead to sustainable poverty reduction.",
            year=2017,
            journal="Quarterly Journal of Economics"
        ),
        Paper(
            paper_id="fn_3",
            title="No Longer Trapped? Promoting Entrepreneurship Through Cash Transfers to Ultra‐Poor Women in Northern Kenya", 
            abstract="We examine the short-to-medium-run impacts of the Rural Entrepreneur Access Program, a poverty graduation program that promotes entrepreneurship among ultra-poor women in arid and semi-arid northern Kenya, a context prone to poverty traps. The program relies on cash transfers (rather than asset transfers) in addition to business skills training, business mentoring, and savings. Participation in each of the program's three rounds was randomly determined through a public lottery. In the short-to-medium run, we find that the program has a positive and significant impact on income, savings, and asset accumulation, similar to more traditional poverty graduation programs that rely on asset transfers.",
            year=2017,
            journal="American Journal of Agricultural Economics"
        )
    ]
    
    for i, paper in enumerate(false_negative_papers, 1):
        print(f"📄 FALSE NEGATIVE #{i}: {paper.title}")
        print("-" * 60)
        print(f"Abstract: {paper.abstract[:100]}...")
        print()
        
        # Screen the paper
        result = screener.screen_paper(paper)
        
        print(f"🤖 AI Decision: {result.final_decision.value.upper()}")
        print(f"📝 Reasoning: {result.decision_reasoning}")
        print()
        
        print("📋 DETAILED CRITERIA BREAKDOWN:")
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
                print(f"     {criterion.reasoning}")
        
        print()
        print("🔍 ANALYSIS:")
        counts = result.count_criteria_by_status()
        print(f"   YES: {counts.get('YES', 0)}, NO: {counts.get('NO', 0)}, UNCLEAR: {counts.get('UNCLEAR', 0)}")
        
        # Identify the issue
        if result.final_decision.value == "exclude":
            no_criteria = []
            for attr_name, display_name in criteria_attrs:
                if hasattr(result, attr_name):
                    criterion = getattr(result, attr_name)
                    if criterion.assessment == "NO":
                        no_criteria.append(display_name)
            
            print(f"   ❌ EXCLUSION TRIGGER: {', '.join(no_criteria)}")
            print(f"   🚨 PROBLEM: This paper should be INCLUDED, not excluded!")
        
        print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    debug_false_negatives()
#!/usr/bin/env python3
"""
Archive development scripts and organize the workspace.
"""

import os
import shutil
from pathlib import Path

def archive_development_files():
    """Archive development and testing files to clean up workspace."""
    
    print("🗂️ ARCHIVING DEVELOPMENT FILES")
    print("=" * 31)
    
    # Define file categories
    archive_mapping = {
        "archive/analysis": [
            "analyze_bauchet.py",
            "analyze_component_logic.py", 
            "analyze_current_maybe.py",
            "analyze_decision_logic.py",
            "analyze_dual_component_redundancy.py",
            "analyze_issues.py",
            "analyze_streamlined_improvements.py",
            "analyze_unclear_patterns.py",
            "clarify_analysis.py",
            "corrected_analysis.py",
            "print_all_unclear.py",
            "print_maybe_papers.py",
            "reanalyze_decisions.py",
            "unclear_analysis_summary.py",
            "validation_analysis.py"
        ],
        "archive/testing": [
            "test_comparison.py",
            "test_comprehensive_final.py",
            "test_decision_logic.py",
            "test_enhanced_api.py",
            "test_enhanced_diagnostic.py",
            "test_enhanced_prompt.py",
            "test_enhanced_simple.py",
            "test_final_improved.py",
            "test_fixed_enhanced.py",
            "test_integrated_approach.py",
            "test_logic_fix.py",
            "test_optimized_prompt.py",
            "test_real_maybe_optimization.py",
            "test_simple_logic.py",
            "test_streamlined_screening.py",
            "test_structured_screening.py"
        ],
        "archive/validation": [
            "final_validation.py",
            "validate_streamlined.py", 
            "validate_structured.py",
            "debug_false_negatives.py",
            "debug_optimized_prompt.py"
        ],
        "archive/development": [
            "check_logic_fix.py",
            "compare_prompts.py",
            "create_optimized_prompt.py",
            "integrate_production.py",
            "streamlined_approach_summary.py",
            "prompt_enhancement_summary.py",
            "logic_validation_summary.py",
            "final_validation_summary.py"
        ]
    }
    
    # Keep in main directory (production files)
    keep_files = [
        "main.py",                    # Main entry point
        "integrated_screener.py",     # Production screener
        "validate_integrated.py",     # Validation framework
        "decision_processor.py",      # Core decision logic
        "requirements.txt",           # Dependencies
        "README.md"                   # Documentation
    ]
    
    # Archive summary files
    summary_files = [
        "ENHANCED_PROMPT_VALIDATION_SUMMARY.md",
        "INTEGRATION_SUMMARY.md", 
        "PROMPT_OPTIMIZATION_DEPLOYMENT_SUMMARY.md",
        "VALIDATION_DEPLOYMENT_SUMMARY.md"
    ]
    
    moved_count = 0
    
    # Move files to archive
    for archive_dir, files in archive_mapping.items():
        print(f"\n📁 Moving to {archive_dir}/:")
        
        for filename in files:
            if os.path.exists(filename):
                os.makedirs(archive_dir, exist_ok=True)
                shutil.move(filename, f"{archive_dir}/{filename}")
                print(f"   ✅ {filename}")
                moved_count += 1
            else:
                print(f"   ⚠️  {filename} (not found)")
    
    # Move summary files to archive/development
    print(f"\n📁 Moving summaries to archive/development/:")
    for filename in summary_files:
        if os.path.exists(filename):
            shutil.move(filename, f"archive/development/{filename}")
            print(f"   ✅ {filename}")
            moved_count += 1
    
    print(f"\n📊 ARCHIVING COMPLETE")
    print(f"   📦 Moved {moved_count} files to archive")
    print(f"   🏠 Kept {len(keep_files)} production files in main directory")
    
    # Show remaining files
    print(f"\n📁 REMAINING FILES IN MAIN DIRECTORY:")
    remaining_files = [f for f in os.listdir(".") if os.path.isfile(f) and not f.startswith('.')]
    for filename in sorted(remaining_files):
        if filename in keep_files:
            print(f"   ✅ {filename} (production)")
        else:
            print(f"   📄 {filename}")
    
    print(f"\n📁 DIRECTORIES:")
    dirs = [d for d in os.listdir(".") if os.path.isdir(d) and not d.startswith('.')]
    for dirname in sorted(dirs):
        print(f"   📂 {dirname}/")

if __name__ == "__main__":
    archive_development_files()
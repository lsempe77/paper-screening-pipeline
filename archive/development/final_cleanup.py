#!/usr/bin/env python3
"""
Final cleanup: Remove unused src subdirectories.
"""

import os
import shutil

def final_cleanup():
    """Remove unused src subdirectories."""
    
    print("🧹 FINAL CLEANUP - REMOVING UNUSED SRC MODULES")
    print("=" * 45)
    
    # Directories to remove (no longer needed with IntegratedStructuredScreener)
    unused_dirs = [
        "src/screeners",    # Old OpenRouterScreener approach
        "src/evaluators",   # Old evaluation system  
        "src/utils"         # Old utility functions
    ]
    
    # Keep these directories (still needed)
    keep_dirs = [
        "src/models",       # ✅ Core data models
        "src/parsers"       # ✅ RIS file parsing
    ]
    
    removed_count = 0
    
    for dir_path in unused_dirs:
        if os.path.exists(dir_path):
            print(f"🗑️  Removing: {dir_path}/")
            shutil.rmtree(dir_path)
            removed_count += 1
        else:
            print(f"⚠️  Not found: {dir_path}/")
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"   🗑️  Removed {removed_count} unused directories")
    print(f"   ✅ Kept essential modules: {', '.join(keep_dirs)}")
    
    # Show final src structure
    print(f"\n📁 FINAL SRC/ STRUCTURE:")
    if os.path.exists("src"):
        for item in sorted(os.listdir("src")):
            if os.path.isdir(f"src/{item}") and not item.startswith('__'):
                print(f"   📂 src/{item}/")
            elif item.endswith('.py'):
                print(f"   📄 src/{item}")
    
    print(f"\n✅ PRODUCTION CODEBASE OPTIMIZED")
    print("   🎯 Only essential modules remain")
    print("   🚀 Clean, minimal production structure")

if __name__ == "__main__":
    final_cleanup()
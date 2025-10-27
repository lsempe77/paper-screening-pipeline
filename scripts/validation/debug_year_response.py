"""
Debug: Check what the LLM is actually returning for publication_year.
"""

import sys
from pathlib import Path
import json

# Add parent directory to path
script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from src.models import Paper, ModelConfig
from integrated_screener import IntegratedStructuredScreener
import yaml

# Load config
with open(project_dir / 'config' / 'config.yaml', 'r') as f:
    config = yaml.safe_load(f)

model_config = ModelConfig(
    provider="openrouter",
    model_name="anthropic/claude-3-haiku",
    temperature=0.1,
    max_tokens=1000,
    api_key=config['openrouter']['api_key']
)

screener = IntegratedStructuredScreener(model_config)

# Simple test paper
paper = Paper(
    title="Test paper about poverty in Nigeria 2007",
    abstract="This is a test abstract.",
    year=2007,
    paper_id="test_001"
)

# Read updated prompt
with open(project_dir / "prompts" / "structured_screening_with_program_filter.txt", 'r', encoding='utf-8') as f:
    prompt_template = f.read()

result = screener.screen_paper(paper, prompt_template=prompt_template)

print("Raw LLM Response:")
print("=" * 80)
print(result.raw_response)
print("=" * 80)

# Parse to see the structure
try:
    parsed = json.loads(result.raw_response)
    pub_year_data = parsed.get('criteria_evaluation', {}).get('publication_year', {})
    print("\nPublication Year field from LLM:")
    print(json.dumps(pub_year_data, indent=2))
except:
    print("\nCouldn't parse JSON from response")

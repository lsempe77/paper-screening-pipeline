"""
Debug the JSON structure to understand what's failing
"""
import sys
from pathlib import Path

script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from integrated_screener import IntegratedStructuredScreener
from src.models import ModelConfig
from src.parsers import RISParser
import yaml
import json

# Test one paper
paper_id = 121296063  # Malawi SCTP

# Load config
config_path = project_dir / "config" / "config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

model_config = ModelConfig(
    provider="openrouter",
    model_name=config['models']['primary']['model_name'],
    api_url=config['openrouter']['api_url'],
    api_key=config['openrouter']['api_key'],
    temperature=0.0,
    max_tokens=4000
)

screener = IntegratedStructuredScreener(
    model_config=model_config,
    use_program_filter=True
)

# Load prompt
prompt_path = project_dir / 'prompts' / 'structured_screening_with_program_filter.txt'
with open(prompt_path, 'r', encoding='utf-8') as f:
    prompt_template = f.read()

# Load corpus
parser = RISParser()
ris_files = [
    project_dir / "data" / "input" / "Excluded by DEP classifier (n=54,924).txt",
    project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
]

corpus_lookup = {}
for ris_file in ris_files:
    if ris_file.exists():
        papers = parser.parse_file(str(ris_file))
        for paper in papers:
            if hasattr(paper, 'ris_fields') and 'U1' in paper.ris_fields:
                paper_ids = paper.ris_fields['U1']
                if isinstance(paper_ids, list):
                    paper_id_str = paper_ids[0] if paper_ids else None
                else:
                    paper_id_str = paper_ids
                
                if paper_id_str:
                    corpus_lookup[str(paper_id_str)] = paper

paper = corpus_lookup.get(str(paper_id))
if not paper:
    print(f"Paper {paper_id} not found!")
    exit(1)

print(f"Testing paper: {paper_id}")
print(f"Title: {paper.title[:80]}")

# Screen paper
result = screener.screen_paper(paper, prompt_template=prompt_template)

# Print the raw response to see structure
print("\n" + "=" * 80)
print("RAW RESPONSE:")
print("=" * 80)
print(result.raw_response[:2000])
print("...")

# Try to parse it
print("\n" + "=" * 80)
print("PARSING ANALYSIS:")
print("=" * 80)

try:
    data = json.loads(result.raw_response)
    print(f"Top-level keys: {list(data.keys())}")
    
    if 'first_pass' in data:
        print("\nThis is a FOLLOWUP response")
        print(f"first_pass type: {type(data['first_pass'])}")
        print(f"first_pass content (first 500 chars):\n{str(data['first_pass'])[:500]}")
    else:
        print("\nThis is a SIMPLE response")
        if 'criteria_evaluation' in data:
            criteria = data['criteria_evaluation']
            if 'program_recognition' in criteria:
                prog = criteria['program_recognition']
                print(f"Program Recognition Assessment: {prog.get('assessment')}")
                print(f"Program Recognition Reasoning: {prog.get('reasoning')[:100]}")
except Exception as e:
    print(f"Error parsing: {e}")

"""Quick debug test - just 5 papers"""
import sys
from pathlib import Path
import pandas as pd

script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from integrated_screener import IntegratedStructuredScreener
from src.models import Paper, ModelConfig
from src.parsers import RISParser
import yaml

# Load config
config_path = project_dir / "config" / "config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

model_config = ModelConfig(
    provider="openrouter",
    model_name=config['models']['primary']['model_name'],
    api_url=config['openrouter']['api_url'],
    api_key=config['openrouter']['api_key'],
    temperature=config['models']['primary'].get('temperature', 0.0),
    max_tokens=config['models']['primary'].get('max_tokens', 4000)
)

screener = IntegratedStructuredScreener(
    model_config=model_config,
    use_program_filter=True
)

print("✓ Screener initialized\n")

# Load just 5 papers
s14_path = project_dir / "data" / "input" / "s14above.xlsx"
df = pd.read_excel(s14_path)
print(f"Total papers: {len(df)}")
print("Labels:", df['include'].value_counts().to_dict())

# Load corpus
parser = RISParser()
ris_file = project_dir / "data" / "input" / "Not excluded by DEP classifier (n=12,394).txt"
print(f"\nLoading {ris_file.name}...")
papers = parser.parse_file(str(ris_file))
print(f"Loaded {len(papers)} papers")

corpus_lookup = {}
for paper in papers:
    if hasattr(paper, 'ris_fields') and 'U1' in paper.ris_fields:
        u1 = paper.ris_fields['U1']
        paper_id = u1[0] if isinstance(u1, list) else u1
        corpus_lookup[str(paper_id).strip()] = paper

print(f"Created lookup with {len(corpus_lookup)} papers\n")

# Test 5 papers
for idx in range(5):
    row = df.iloc[idx]
    paper_id = str(row['ID'])
    
    if paper_id in corpus_lookup:
        paper = corpus_lookup[paper_id]
        print(f"[{idx+1}] Testing paper {paper_id}")
        print(f"    Title: {paper.title[:70]}...")
        print(f"    Abstract length: {len(paper.abstract)}")
        print(f"    Human label: {row['include']}")
        
        result = screener.screen_paper(paper)
        print(f"    LLM decision: {result.final_decision}")
        print(f"    Decision reasoning: {result.decision_reasoning[:150] if hasattr(result, 'decision_reasoning') else 'N/A'}...")
        print()
    else:
        print(f"[{idx+1}] Paper {paper_id} not found in corpus")

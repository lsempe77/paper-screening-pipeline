import sys
from pathlib import Path

script_dir = Path(__file__).parent
project_dir = script_dir.parent.parent
sys.path.insert(0, str(project_dir))

from src.parsers import RISParser

parser = RISParser()
papers = {}

for f in [Path('data/input/Excluded by DEP classifier (n=54,924).txt'), 
          Path('data/input/Not excluded by DEP classifier (n=12,394).txt')]:
    for p in parser.parse_file(str(f)):
        if hasattr(p, 'ris_fields') and 'U1' in p.ris_fields:
            uid = p.ris_fields['U1']
            if isinstance(uid, list):
                uid = uid[0]
            papers[uid] = p

# SCTP
p1 = papers.get('121296063')
if p1:
    print('='*80)
    print('MALAWI SCTP (121296063)')
    print('='*80)
    print('\nTitle:', p1.title)
    print('\nAbstract:')
    print(p1.abstract)
    print('\n')

# LEAP  
p2 = papers.get('121328933')
if p2:
    print('='*80)
    print('GHANA LEAP (121328933)')
    print('='*80)
    print('\nTitle:', p2.title)
    print('\nAbstract:')
    print(p2.abstract)

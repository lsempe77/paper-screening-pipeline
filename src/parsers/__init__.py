"""
RIS file parsers for extracting paper data.
"""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..models import Paper


class RISParser:
    """Parser for RIS (Research Information Systems) format files."""
    
    # RIS field mappings to our Paper model
    FIELD_MAPPINGS = {
        'TY': 'publication_type',
        'T1': 'title',
        'TI': 'title',  # Alternative title field
        'JF': 'journal',
        'JO': 'journal',  # Alternative journal field
        'T2': 'journal',  # Secondary title (often journal)
        'PY': 'year',
        'Y1': 'year',  # Alternative year field
        'AB': 'abstract',
        'DO': 'doi',
        'UR': 'url',
        'U1': 'url',  # Alternative URL field
        'VL': 'volume',
        'IS': 'issue',
        'SP': 'start_page',
        'EP': 'end_page',
        'KW': 'keywords',
        'A1': 'authors',
        'AU': 'authors',  # Alternative author field
    }
    
    def __init__(self):
        self.papers: List[Paper] = []
    
    def parse_file(self, file_path: str) -> List[Paper]:
        """Parse a single RIS file and return list of papers."""
        papers = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                content = f.read()
        
        # Split into individual records (separated by ER  -)
        records = re.split(r'\nER\s*-\s*\n', content)
        
        for i, record in enumerate(records):
            if record.strip():
                paper = self._parse_record(record, file_path, i)
                if paper:
                    papers.append(paper)
        
        return papers
    
    def _parse_record(self, record: str, source_file: str, record_index: int) -> Optional[Paper]:
        """Parse a single RIS record into a Paper object."""
        paper_data = {}
        ris_fields = {}
        
        # Split record into lines
        lines = record.strip().split('\n')
        
        current_field = None
        current_value = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with RIS field pattern (XX  - )
            field_match = re.match(r'^([A-Z0-9]{1,2})\s*-\s*(.*)$', line)
            
            if field_match:
                # Save previous field if exists
                if current_field:
                    self._add_field_value(paper_data, ris_fields, current_field, current_value.strip())
                
                # Start new field
                current_field = field_match.group(1)
                current_value = field_match.group(2)
            else:
                # Continuation of previous field
                if current_field:
                    current_value += " " + line
        
        # Add last field
        if current_field:
            self._add_field_value(paper_data, ris_fields, current_field, current_value.strip())
        
        # Create Paper object if we have at least a title
        if paper_data.get('title'):
            # Set defaults and clean data
            paper = Paper(
                title=paper_data.get('title', ''),
                authors=paper_data.get('authors', []),
                journal=paper_data.get('journal', ''),
                year=self._parse_year(paper_data.get('year')),
                abstract=paper_data.get('abstract', ''),
                doi=self._clean_doi(paper_data.get('doi', '')),
                url=paper_data.get('url', ''),
                keywords=paper_data.get('keywords', []),
                publication_type=paper_data.get('publication_type', ''),
                volume=paper_data.get('volume', ''),
                issue=paper_data.get('issue', ''),
                pages=self._format_pages(paper_data.get('start_page', ''), paper_data.get('end_page', '')),
                source_file=Path(source_file).name,
                ris_fields=ris_fields
            )
            
            return paper
        
        return None
    
    def _add_field_value(self, paper_data: Dict, ris_fields: Dict, field_code: str, value: str):
        """Add a field value to paper data, handling multiple values for same field."""
        if not value:
            return
        
        # Store raw RIS field
        if field_code not in ris_fields:
            ris_fields[field_code] = []
        ris_fields[field_code].append(value)
        
        # Map to paper fields
        if field_code in self.FIELD_MAPPINGS:
            field_name = self.FIELD_MAPPINGS[field_code]
            
            if field_name in ['authors', 'keywords']:
                # Multi-value fields
                if field_name not in paper_data:
                    paper_data[field_name] = []
                paper_data[field_name].append(value)
            else:
                # Single value fields - take first non-empty value
                if field_name not in paper_data or not paper_data[field_name]:
                    paper_data[field_name] = value
    
    def _parse_year(self, year_str: Optional[str]) -> Optional[int]:
        """Extract year from year string."""
        if not year_str:
            return None
        
        # Extract 4-digit year
        year_match = re.search(r'(\d{4})', str(year_str))
        if year_match:
            return int(year_match.group(1))
        
        return None
    
    def _clean_doi(self, doi: str) -> str:
        """Clean DOI string."""
        if not doi or doi.lower() in ['no doi', 'none', '']:
            return ""
        
        # Remove common prefixes
        doi = re.sub(r'^(doi:|https?://dx\.doi\.org/|https?://doi\.org/)', '', doi, flags=re.IGNORECASE)
        
        return doi.strip()
    
    def _format_pages(self, start_page: str, end_page: str) -> str:
        """Format page range."""
        if start_page and end_page:
            return f"{start_page}-{end_page}"
        elif start_page:
            return start_page
        elif end_page:
            return end_page
        return ""


def parse_multiple_files(file_paths: List[str]) -> List[Paper]:
    """Parse multiple RIS files and return combined list of papers."""
    parser = RISParser()
    all_papers = []
    
    for file_path in file_paths:
        try:
            papers = parser.parse_file(file_path)
            all_papers.extend(papers)
            print(f"Parsed {len(papers)} papers from {Path(file_path).name}")
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    return all_papers
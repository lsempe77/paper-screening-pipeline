"""
Data models for the paper screening pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ScreeningDecision(Enum):
    """Possible screening decisions."""
    INCLUDE = "include"
    EXCLUDE = "exclude"
    MAYBE = "maybe"
    UNCERTAIN = "uncertain"
    NOT_SCREENED = "not_screened"


@dataclass
class Paper:
    """Represents a single academic paper from RIS file."""
    
    # RIS Standard Fields
    title: str = ""
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    year: Optional[int] = None
    abstract: str = ""
    doi: str = ""
    url: str = ""
    keywords: List[str] = field(default_factory=list)
    publication_type: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    
    # Internal tracking
    paper_id: str = ""
    source_file: str = ""
    
    # RIS raw data
    ris_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate paper ID if not provided."""
        if not self.paper_id:
            self.paper_id = f"{self.year}_{hash(self.title) % 10000:04d}"


@dataclass
class ScreeningResult:
    """Results from AI-based paper screening."""
    
    paper_id: str
    decision: ScreeningDecision
    confidence_score: float
    reasoning: str
    model_used: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Model response details
    raw_response: str = ""
    processing_time: float = 0.0
    
    # Human review fields
    human_reviewed: bool = False
    human_decision: Optional[ScreeningDecision] = None
    human_notes: str = ""


@dataclass
class ScreeningBatch:
    """Represents a batch of papers being screened together."""
    
    batch_id: str
    papers: List[Paper] = field(default_factory=list)
    results: List[ScreeningResult] = field(default_factory=list)
    
    # Batch metadata
    created_at: datetime = field(default_factory=datetime.now)
    model_config: Dict[str, Any] = field(default_factory=dict)
    prompt_version: str = ""
    
    # Statistics
    total_papers: int = 0
    completed_papers: int = 0
    
    def __post_init__(self):
        """Update total papers count."""
        self.total_papers = len(self.papers)
    
    def add_result(self, result: ScreeningResult):
        """Add a screening result to the batch."""
        self.results.append(result)
        self.completed_papers = len(self.results)
    
    @property
    def completion_rate(self) -> float:
        """Calculate completion percentage."""
        if self.total_papers == 0:
            return 0.0
        return (self.completed_papers / self.total_papers) * 100


@dataclass
class ModelConfig:
    """Configuration for AI model used in screening."""
    
    provider: str  # "openrouter"
    model_name: str  # e.g., "anthropic/claude-3-haiku"
    temperature: float = 0.1
    max_tokens: int = 1000
    
    # OpenRouter specific
    api_key: str = ""
    api_url: str = "https://openrouter.ai/api/v1"
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class CriteriaAssessment:
    """Assessment of individual inclusion criteria."""
    assessment: str  # "YES", "NO", or "UNCLEAR"
    reasoning: str


@dataclass
class StructuredScreeningResult:
    """Results from structured criteria-based screening."""
    
    paper_id: str
    final_decision: ScreeningDecision  # INCLUDE, EXCLUDE, MAYBE
    decision_reasoning: str
    
    # Individual criteria assessments
    program_recognition: CriteriaAssessment  # NEW: Program filter
    participants_lmic: CriteriaAssessment
    component_a_cash_support: CriteriaAssessment
    component_b_productive_assets: CriteriaAssessment
    relevant_outcomes: CriteriaAssessment
    appropriate_study_design: CriteriaAssessment
    publication_year_2004_plus: CriteriaAssessment
    completed_study: CriteriaAssessment
    
    # Model details
    model_used: str
    timestamp: datetime = field(default_factory=datetime.now)
    raw_response: str = ""
    processing_time: float = 0.0
    
    def get_criteria_summary(self) -> Dict[str, str]:
        """Get summary of all criteria assessments."""
        return {
            "program_recognition": self.program_recognition.assessment,
            "participants_lmic": self.participants_lmic.assessment,
            "component_a_cash": self.component_a_cash_support.assessment,
            "component_b_assets": self.component_b_productive_assets.assessment,
            "outcomes": self.relevant_outcomes.assessment,
            "study_design": self.appropriate_study_design.assessment,
            "year_2004_plus": self.publication_year_2004_plus.assessment,
            "completed": self.completed_study.assessment
        }
    
    def count_criteria_by_status(self) -> Dict[str, int]:
        """Count how many criteria have each status."""
        assessments = self.get_criteria_summary()
        counts = {"YES": 0, "NO": 0, "UNCLEAR": 0}
        
        for assessment in assessments.values():
            if assessment in counts:
                counts[assessment] += 1
        
        return counts
    retry_delay: float = 1.0
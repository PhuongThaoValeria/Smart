"""
Exam-related Data Models
Dataclasses for exam questions, concepts, and trend analysis
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.core.common import TopicType, DifficultyLevel, QuestionType


@dataclass
class ExamQuestion:
    """Represents a single exam question."""
    question_id: str
    question_text: str
    topic_type: str
    question_type: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    difficulty_level: str = "intermediate"
    target_score_level: str = "8_plus"
    year: int = 2024


@dataclass
class ConceptPattern:
    """Represents patterns observed for a specific concept."""
    concept_name: str
    topic_type: str
    frequency: int
    difficulty_distribution: Dict[str, int]
    target_score_relevance: Dict[str, float]
    example_patterns: List[str]
    grammar_rule: Optional[str] = None
    common_mistakes: List[str] = field(default_factory=list)


@dataclass
class TrendReport:
    """Comprehensive trend analysis report."""
    year: int
    total_questions: int
    topic_distribution: Dict[str, int]
    concept_patterns: List[ConceptPattern]
    difficulty_analysis: Dict[str, Any]
    target_score_guidance: Dict[str, List[str]]
    synthetic_generation_seed: Dict[str, Any]
    generated_at: str


@dataclass
class GeneratedQuestion:
    """A synthetically generated question."""
    question_id: str
    question_text: str
    topic_type: str
    question_type: str
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty_level: str
    concept_id: str
    is_synthetic: bool = True

"""
Learning-related Data Models
Dataclasses for tests, feedback, and assessment
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class RootCauseAnalysis:
    """Analysis of why a student got a question wrong."""
    concept_id: str
    concept_name: str
    root_cause: str
    misconception_pattern: str
    related_concepts: List[str]
    priority_score: float


@dataclass
class FeedbackResponse:
    """Complete feedback response for a question attempt."""
    question_id: str
    student_id: str
    is_correct: bool
    explanation_vn: str
    explanation_en: str
    grammar_rule: str
    why_wrong: Optional[str] = None
    quick_recap_examples: List[Dict[str, str]] = field(default_factory=list)
    alternative_explanation: Optional[str] = None
    memory_hook: Optional[str] = None
    root_cause: Optional[RootCauseAnalysis] = None
    recommended_practice: Optional[List[str]] = None
    follow_up_concepts: Optional[List[str]] = None
    response_time_seconds: float = 0.0
    confidence_score: float = 0.0


@dataclass
class DailyTest:
    """A 15-question daily test."""
    test_id: str
    student_id: str
    test_date: str
    test_sequence: int
    questions: List[Any]
    concepts_covered: List[str]
    adaptive_weights: Dict[str, float]
    time_limit_minutes: int = 15
    estimated_duration_minutes: int = 12


@dataclass
class CompetencyScore:
    """Score for a specific competency area."""
    area: str
    score: float
    question_count: int
    correct_count: int
    improvement_needed: bool
    priority_level: str


@dataclass
class CompetencyMap:
    """Complete competency map for a student (Radar Chart data)."""
    student_id: str
    mega_test_id: str
    test_date: str
    grammar: CompetencyScore
    vocabulary: CompetencyScore
    reading_comprehension: CompetencyScore
    phonetics: CompetencyScore
    overall_score: float
    percentile_rank: float
    strengths: List[str]
    weaknesses: List[str]
    topic_breakdown: Dict[str, Dict[str, Any]]
    improvement_recommendations: List[Dict[str, Any]]
    score_trend: List[float]
    improvement_rate: float


@dataclass
class MegaTest:
    """Bi-weekly full-length mock exam."""
    mega_test_id: str
    student_id: str
    test_date: str
    test_sequence: int
    total_questions: int = 50
    duration_minutes: int = 60
    questions_per_topic: Dict[str, int] = field(default_factory=dict)
    questions: List[Any] = field(default_factory=list)
    status: str = "pending"
    overall_score: Optional[float] = None
    competency_map: Optional[CompetencyMap] = None

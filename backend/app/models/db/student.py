"""
Student-related Data Models
Dataclasses for student learning state and university counseling
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


@dataclass
class StudentLearningState:
    """Tracks student's current learning state."""
    student_id: str
    weak_concepts: List[Tuple[str, float]]  # (concept_name, weakness_score)
    strong_concepts: List[Tuple[str, float]]  # (concept_name, mastery_level)
    current_streak: int
    last_test_date: Optional[str]
    target_score: str
    overall_mastery: float


@dataclass
class UniversityBenchmark:
    """Vietnamese university admission benchmark data."""
    university_id: str
    university_name: str
    university_code: str
    province: str
    major_id: str
    major_name: str
    major_code: str
    subject_group: str
    english_weight: float
    year_2024: Optional[float] = None
    year_2025: Optional[float] = None
    admission_quota: int = 0
    competition_ratio: float = 0.0


@dataclass
class UniversityRecommendation:
    """University/major recommendation for a student."""
    university_name: str
    major_name: str
    benchmark_score: float
    predicted_student_score: float
    admission_probability: float
    match_score: float
    gap_to_benchmark: float
    recommendation_reason: str
    risk_level: str
    application_strategy: str


@dataclass
class RecoveryPlan:
    """Personalized recovery plan for weak areas."""
    student_id: str
    plan_id: str
    target_exam_date: str
    weeks_remaining: int
    weak_concepts: List[str]
    priority_ordering: List[Tuple[str, float]]
    weekly_study_hours: float
    study_schedule: Dict[str, List[str]]
    daily_practice_recommendations: List[Dict[str, Any]]
    expected_score_improvement: float
    target_score: str
    current_predicted_score: float
    gap_to_target: float
    milestones: List[Dict[str, Any]] = field(default_factory=list)

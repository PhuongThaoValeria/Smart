"""
API Response Models
Pydantic models for API responses
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.core.common import TargetScoreLevel, TopicType, DifficultyLevel, TestStatus


# =====================================================
# STUDENT RESPONSES
# =====================================================

class StudentResponse(BaseModel):
    """Model for student response."""
    student_id: str
    email: str
    full_name: str
    current_grade: Optional[int]
    target_score: str
    exam_date: Optional[str]
    current_streak: int
    longest_streak: int
    overall_accuracy: float
    created_at: datetime


class TokenResponse(BaseModel):
    """Model for token response."""
    access_token: str
    token_type: str = "bearer"
    student_id: str
    email: str


# =====================================================
# QUESTION RESPONSES
# =====================================================

class QuestionResponse(BaseModel):
    """Model for question with answer info."""
    question_id: str
    concept_name: str
    topic_type: TopicType
    difficulty: DifficultyLevel
    question_text: str
    options: List[str]
    explanation: Optional[str] = None
    correct_answer: str
    is_synthetic: bool


# =====================================================
# DAILY TEST RESPONSES
# =====================================================

class DailyTestResponse(BaseModel):
    """Model for daily test response."""
    test_id: str
    student_id: str
    test_date: str
    test_sequence: int
    total_questions: int
    duration_minutes: int
    concepts_covered: List[str]
    adaptive_weights: Dict[str, float]
    reasoning: Optional[str] = None  # AI explanation for why these questions were chosen
    status: TestStatus
    questions: List[QuestionResponse]
    created_at: datetime


class DailyTestResult(BaseModel):
    """Model for daily test results."""
    test_id: str
    student_id: str
    total_questions: int
    correct_count: int
    accuracy: float
    time_spent_seconds: int
    streak_earned: int
    completed_at: datetime


# =====================================================
# FEEDBACK RESPONSES
# =====================================================

class FeedbackResponse(BaseModel):
    """Model for feedback response."""
    question_id: str
    is_correct: bool
    explanation_vn: str
    explanation_en: str
    grammar_rule: str
    recap_rule: Optional[str] = None  # Quick recap of the rule
    why_wrong: Optional[str] = None
    quick_recap_examples: List[Dict[str, str]]
    memory_hook: Optional[str] = None
    root_cause: Optional[Dict[str, Any]] = None
    recommended_practice: Optional[List[str]] = None


# =====================================================
# ASSESSMENT RESPONSES
# =====================================================

class MegaTestResponse(BaseModel):
    """Model for mega test response."""
    mega_test_id: str
    student_id: str
    test_date: str
    test_sequence: int
    total_questions: int
    duration_minutes: int
    status: TestStatus
    created_at: datetime


class CompetencyMapResponse(BaseModel):
    """Model for competency map response."""
    student_id: str
    mega_test_id: str
    test_date: str
    grammar_score: float
    vocabulary_score: float
    reading_comprehension_score: float
    phonetics_score: float
    overall_score: float
    percentile_rank: float
    strengths: List[str]
    weaknesses: List[str]
    improvement_recommendations: List[Dict[str, Any]]


class AssessmentStatus(BaseModel):
    """Model for assessment status check."""
    is_due: bool
    due_date: str
    has_active_test: bool
    days_until_next_test: int
    can_start_new: bool


# =====================================================
# COUNSELING RESPONSES
# =====================================================

class UniversityRecommendation(BaseModel):
    """Model for university recommendation."""
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


class RecoveryPlan(BaseModel):
    """Model for recovery plan."""
    student_id: str
    plan_id: str
    target_exam_date: str
    weeks_remaining: int
    weak_concepts: List[str]
    priority_ordering: List[Dict[str, Any]]
    weekly_study_hours: float
    study_schedule: Dict[str, List[str]]
    daily_practice_recommendations: List[Dict[str, Any]]
    expected_score_improvement: float
    target_score: str
    current_predicted_score: float
    gap_to_target: float


class CounselingReport(BaseModel):
    """Model for counseling report."""
    student_id: str
    generated_at: str
    current_predicted_score: float
    target_score: float
    days_until_exam: int
    safe_schools: List[UniversityRecommendation]
    target_schools: List[UniversityRecommendation]
    reach_schools: List[UniversityRecommendation]
    recovery_plan: RecoveryPlan
    overall_strategy: str
    key_recommendations: List[str]


# =====================================================
# GENERIC RESPONSES
# =====================================================

class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    timestamp: datetime = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database_connected: bool
    timestamp: datetime

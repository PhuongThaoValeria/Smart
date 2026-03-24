"""
API Request Models
Pydantic models for incoming API requests
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

from app.models.core.common import TargetScoreLevel


# =====================================================
# STUDENT REQUESTS
# =====================================================

class StudentCreate(BaseModel):
    """Model for creating a new student."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    current_grade: Optional[int] = Field(None, ge=10, le=12)
    target_score: TargetScoreLevel = TargetScoreLevel.EIGHT_PLUS
    exam_date: Optional[str] = None


class StudentLogin(BaseModel):
    """Model for student login."""
    email: EmailStr
    password: str


class StudentUpdate(BaseModel):
    """Model for updating student info."""
    full_name: Optional[str] = None
    current_grade: Optional[int] = None
    target_score: Optional[TargetScoreLevel] = None
    exam_date: Optional[str] = None


# =====================================================
# TEST REQUESTS
# =====================================================

class DailyTestCreate(BaseModel):
    """Model for creating a daily test."""
    student_id: str
    test_date: Optional[str] = None


class DailyTestStart(BaseModel):
    """Model for starting a daily test."""
    test_id: str


class DailyTestSubmit(BaseModel):
    """Model for submitting daily test answers."""
    test_id: str
    answers: List[Dict[str, Any]]  # [{"question_id": "...", "selected_answer": "A", "time_spent": 30}]


# =====================================================
# FEEDBACK REQUESTS
# =====================================================

class FeedbackRequest(BaseModel):
    """Model for feedback request."""
    student_id: str
    question_id: str
    selected_answer: str
    time_spent_seconds: Optional[int] = 0


class BatchFeedbackRequest(BaseModel):
    """Model for batch feedback request."""
    student_id: str
    attempts: List["FeedbackRequest"]


# =====================================================
# IMPORTS
# =====================================================
from typing import Dict, Any

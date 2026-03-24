"""
Student management endpoints - No Auth Required
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional
from datetime import datetime
import uuid

from app.models.api.responses import StudentResponse

router = APIRouter()

# Guest student ID for seamless access
GUEST_STUDENT_ID = "guest_student_001"

# Demo mode: In-memory storage for guest student
DEMO_MODE = True
guest_student = {
    "student_id": GUEST_STUDENT_ID,
    "email": "guest@english-testprep.com",
    "full_name": "Guest Student",
    "current_grade": "12",
    "target_score": "8.5_plus",  # String format as expected by Pydantic
    "exam_date": "2025-06-15",
    "current_streak": 0,
    "longest_streak": 0,
    "overall_accuracy": 0.78,
    "created_at": datetime.now()
}


@router.get("/me", response_model=StudentResponse)
async def get_guest_profile():
    """
    Get guest student profile (no auth required).
    """
    if DEMO_MODE:
        return StudentResponse(
            student_id=guest_student['student_id'],
            email=guest_student['email'],
            full_name=guest_student['full_name'],
            current_grade=guest_student['current_grade'],
            target_score=guest_student['target_score'],
            exam_date=guest_student['exam_date'],
            current_streak=guest_student['current_streak'],
            longest_streak=guest_student['longest_streak'],
            overall_accuracy=guest_student['overall_accuracy'],
            created_at=guest_student['created_at']
        )

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database unavailable in demo mode"
    )


@router.get("/progress")
async def get_guest_progress():
    """
    Get guest student's learning progress (no auth required).
    """
    if DEMO_MODE:
        return {
            "student_id": GUEST_STUDENT_ID,
            "overall_accuracy": 0.78,
            "current_streak": 5,
            "longest_streak": 12,
            "daily_tests_completed": 15,
            "mega_tests_completed": 2,
            "weak_concepts": [
                {"concept": "Reported Speech", "mastery": 45.0, "weakness_score": 8.5},
                {"concept": "Conditionals", "mastery": 55.0, "weakness_score": 7.2},
                {"concept": "Word Formation", "mastery": 65.0, "weakness_score": 5.8}
            ],
            "strong_concepts": [
                {"concept": "Subject-Verb Agreement", "mastery": 92.0},
                {"concept": "Tense Forms", "mastery": 88.0},
                {"concept": "Articles", "mastery": 85.0}
            ]
        }

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database unavailable in demo mode"
    )

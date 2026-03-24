"""
from app.routes.students import GUEST_STUDENT_ID
Assessment endpoints - Mega tests and Competency Maps
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, date

from app.database import DatabaseManager
from app.models.api.responses import (
    MegaTestResponse, CompetencyMapResponse, AssessmentStatus
)
from app.services.assessment import AssessmentService
from app.config import get_config

router = APIRouter()

config = get_config()


@router.get("/status", response_model=AssessmentStatus)
async def get_assessment_status(
    student_id: str = "guest_student_001",
    db: DatabaseManager = Depends()
):
    """
    Check if a mega test is due for the student.

    Returns:
    - Whether a mega test is due
    - Days until next test
    - Whether student has an active test
    """
    try:
        service = AssessmentService(config.db.url)
        status_data = service.check_test_status(student_id)
        service.close_all()

        return AssessmentStatus(**status_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check assessment status: {str(e)}"
        )


@router.post("/mega-test/generate", response_model=MegaTestResponse)
async def generate_mega_test(
    student_id: str = "guest_student_001",
    db: DatabaseManager = Depends()
):
    """
    Generate a bi-weekly mega test (50 questions, 60 minutes).

    Only available every 14 days or when manually triggered.
    """
    try:
        service = AssessmentService(config.db.url)

        # Check if student can start new test
        status_data = service.check_test_status(student_id)

        if not status_data['can_start_new']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot start new mega test. {status_data['days_until_next_test']} days until next test."
            )

        # Generate test
        mega_test = service.create_mega_test(student_id)
        service.close_all()

        return MegaTestResponse(
            mega_test_id=mega_test.mega_test_id,
            student_id=mega_test.student_id,
            test_date=mega_test.test_date,
            test_sequence=mega_test.test_sequence,
            total_questions=mega_test.total_questions,
            duration_minutes=mega_test.duration_minutes,
            status=mega_test.status,
            created_at=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate mega test: {str(e)}"
        )


@router.post("/mega-test/{mega_test_id}/submit")
async def submit_mega_test(
    mega_test_id: str,
    answers: List[dict],
    student_id: str = "guest_student_001",
    db: DatabaseManager = Depends()
):
    """
    Submit mega test answers and generate competency map.

    Automatically:
    - Scores the test
    - Generates competency map (Radar Chart data)
    - Provides detailed analytics
    - Updates student progress
    """
    # Verify test ownership
    result = db.execute_query(
        """SELECT * FROM mega_tests WHERE mega_test_id = %s AND student_id = %s""",
        (mega_test_id, student_id)
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mega test not found"
        )

    test = result[0]

    if test['status'] == 'completed':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test already completed"
        )

    # Calculate score and generate competency map
    try:
        service = AssessmentService(config.db.url)

        # Generate competency map (this would normally process answers first)
        competency_map = service.generate_competency_map(student_id, mega_test_id)
        service.close_all()

        # Update test status
        db.execute_update(
            """UPDATE mega_tests
               SET status = 'completed', completed_at = %s, overall_score = %s
               WHERE mega_test_id = %s""",
            (datetime.now(), competency_map.overall_score, mega_test_id)
        )

        return {
            "mega_test_id": mega_test_id,
            "status": "completed",
            "overall_score": competency_map.overall_score,
            "percentile_rank": competency_map.percentile_rank,
            "competency_map": {
                "grammar": competency_map.grammar.score,
                "vocabulary": competency_map.vocabulary.score,
                "reading_comprehension": competency_map.reading_comprehension.score,
                "phonetics": competency_map.phonetics.score
            },
            "strengths": competency_map.strengths,
            "weaknesses": competency_map.weaknesses
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit mega test: {str(e)}"
        )


@router.get("/competency-map/latest", response_model=CompetencyMapResponse)
async def get_latest_competency_map(
    student_id: str = "guest_student_001",
    db: DatabaseManager = Depends()
):
    """
    Get student's latest competency map.

    Provides Radar Chart data for:
    - Grammar
    - Vocabulary
    - Reading Comprehension
    - Phonetics
    """
    result = db.execute_query("""
        SELECT cm.*, mt.test_sequence
        FROM competency_maps cm
        JOIN mega_tests mt ON cm.mega_test_id = mt.mega_test_id
        WHERE cm.student_id = %s
        ORDER BY mt.test_sequence DESC
        LIMIT 1
    """, (student_id,))

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No competency map found. Complete a mega test first."
        )

    cm = result[0]

    return CompetencyMapResponse(
        student_id=cm['student_id'],
        mega_test_id=cm['mega_test_id'],
        test_date=cm['generated_at'].isoformat(),
        grammar_score=float(cm['grammar_score']),
        vocabulary_score=float(cm['vocabulary_score']),
        reading_comprehension_score=float(cm['reading_comprehension_score']),
        phonetics_score=float(cm['phonetics_score']),
        overall_score=cm['grammar_score'] + cm['vocabulary_score'] +
                      cm['reading_comprehension_score'] + cm['phonetics_score'],
        percentile_rank=float(cm.get('percentile_rank', 50.0)),
        strengths=cm['strength_areas'] or [],
        weaknesses=cm['weakness_areas'] or [],
        improvement_recommendations=cm.get('improvement_recommendations', [])
    )


@router.get("/progress-summary")
async def get_progress_summary(
    student_id: str = "guest_student_001",
    db: DatabaseManager = Depends()
):
    """
    Get comprehensive progress summary including mega test performance.
    """
    try:
        service = AssessmentService(config.db.url)
        summary = service.get_student_progress_summary(student_id)
        service.close_all()

        return summary

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress summary: {str(e)}"
        )


@router.get("/mega-tests/history")
async def get_mega_test_history(
    limit: int = 5,
    student_id: str = "guest_student_001",
    db: DatabaseManager = Depends()
):
    """
    Get student's mega test history.
    """
    result = db.execute_query(
        """SELECT * FROM mega_tests
           WHERE student_id = %s AND status = 'completed'
           ORDER BY test_date DESC
           LIMIT %s""",
        (student_id, limit)
    )

    history = []
    for row in result:
        history.append({
            "mega_test_id": row['mega_test_id'],
            "test_date": row['test_date'].isoformat(),
            "test_sequence": row['test_sequence'],
            "overall_score": float(row['overall_score']) if row['overall_score'] else None,
            "percentile_rank": float(row['percentile_rank']) if row['percentile_rank'] else None,
            "completed_at": row['completed_at'].isoformat() if row['completed_at'] else None
        })

    return {
        "student_id": student_id,
        "total_mega_tests": len(history),
        "history": history
    }

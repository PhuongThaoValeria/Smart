"""
from app.routes.students import GUEST_STUDENT_ID
Feedback endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.database import DatabaseManager
from app.models.api.requests import FeedbackRequest, BatchFeedbackRequest
from app.models.api.responses import FeedbackResponse
from app.services.feedback import FeedbackService
from app.config import get_config

router = APIRouter()

config = get_config()


@router.post("/generate", response_model=FeedbackResponse)
async def generate_feedback(
    request: FeedbackRequest,
    student_id: str = "guest_student_001"
):
    """
    Generate feedback for a single question attempt.

    Provides:
    - Vietnamese and English explanations
    - Grammar rules
    - Why the answer was wrong
    - Mini-examples for reinforcement
    - Root cause analysis
    - Recommended practice
    """
    # Verify student ownership
    if request.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot get feedback for another student"
        )

    try:
        # Use FeedbackService
        service = FeedbackService(config.db.url)
        feedback_data = service.get_feedback_for_attempt(
            student_id=request.student_id,
            question_id=request.question_id,
            selected_answer=request.selected_answer,
            time_spent_seconds=request.time_spent_seconds
        )
        service.close()

        return FeedbackResponse(**feedback_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate feedback: {str(e)}"
        )


@router.post("/batch", response_model=List[FeedbackResponse])
async def generate_batch_feedback(
    request: BatchFeedbackRequest,
    student_id: str = "guest_student_001"
):
    """
    Generate feedback for multiple question attempts at once.

    Useful for submitting complete tests and getting all feedback.
    """
    # Verify student ownership
    if request.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot get feedback for another student"
        )

    try:
        service = FeedbackService(config.db.url)
        feedbacks = service.batch_feedback(
            student_id=request.student_id,
            attempts=request.attempts
        )
        service.close()

        # Convert to response models
        from app.models.api.responses import asdict

        return [
            FeedbackResponse(**asdict(f))
            for f in feedbacks
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate batch feedback: {str(e)}"
        )


@router.get("/concepts/{concept_name}/explanation")
async def get_concept_explanation(
    concept_name: str,
    student_id: str = "guest_student_001",
    db: DatabaseManager = Depends()
):
    """
    Get detailed explanation and examples for a specific concept.

    Useful for studying before or after a test.
    """
    result = db.execute_query(
        """SELECT * FROM concepts WHERE concept_name = %s""",
        (concept_name,)
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept '{concept_name}' not found"
        )

    concept = result[0]

    # Get student's mastery level
    mastery_result = db.execute_query("""
        SELECT mastery_level, incorrect_attempts, correct_attempts
        FROM student_knowledge_graph skg
        JOIN concepts c ON skg.concept_id = c.concept_id
        WHERE skg.student_id = %s AND c.concept_name = %s
    """, (student_id, concept_name))

    mastery = mastery_result[0] if mastery_result else None

    return {
        "concept_name": concept['concept_name'],
        "topic_type": concept['topic_type'],
        "description": concept['description'],
        "grammar_rule": concept['grammar_rule'],
        "examples": concept.get('examples', []),
        "your_mastery": {
            "mastery_level": float(mastery['mastery_level']) if mastery else None,
            "correct_attempts": mastery['correct_attempts'] if mastery else 0,
            "incorrect_attempts": mastery['incorrect_attempts'] if mastery else 0
        } if mastery else None
    }


@router.get("/weak-concepts")
async def get_weak_concepts(
    student_id: str = "guest_student_001",
    db: DatabaseManager = Depends()
):
    """
    Get student's weak concepts with recommended practice.

    Returns concepts where mastery < 70%, ordered by weakness score.
    """
    result = db.execute_query("""
        SELECT
            c.concept_name,
            c.topic_type,
            skg.mastery_level,
            skg.weakness_score,
            skg.streak_incorrect,
            skg.adaptive_weight
        FROM student_knowledge_graph skg
        JOIN concepts c ON skg.concept_id = c.concept_id
        WHERE skg.student_id = %s AND skg.mastery_level < 70
        ORDER BY skg.weakness_score DESC
        LIMIT 10
    """, (student_id,))

    weak_concepts = []
    for row in result:
        weak_concepts.append({
            "concept_name": row['concept_name'],
            "topic_type": row['topic_type'],
            "mastery_level": float(row['mastery_level']),
            "weakness_score": float(row['weakness_score']),
            "streak_incorrect": row['streak_incorrect'],
            "adaptive_weight": float(row['adaptive_weight']),
            "recommended_practice": f"Focus on {row['concept_name']} - current priority due to {row['streak_incorrect']} consecutive incorrect answers"
        })

    return {
        "weak_concepts": weak_concepts,
        "count": len(weak_concepts),
        "top_priority": weak_concepts[0] if weak_concepts else None
    }

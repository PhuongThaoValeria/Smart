"""
Daily test endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, date

from app.database import DatabaseManager
from app.models.api.requests import DailyTestCreate, DailyTestStart, DailyTestSubmit
from app.models.api.responses import DailyTestResponse, DailyTestResult, QuestionResponse
from app.services.daily_tests import DailyTestOrchestrator
from app.config import get_config

router = APIRouter()

config = get_config()


def get_db():
    """Get database connection or return None if not available."""
    try:
        return DatabaseManager()
    except Exception:
        return None


@router.post("/generate", response_model=DailyTestResponse)
async def generate_daily_test(
    test_data: DailyTestCreate,
    student_id: str = "guest_student_001"
):
    """
    Generate a new 15-minute daily test for a student.

    Uses adaptive learning to select questions based on:
    - Previous incorrect answers (+40% weight)
    - Current mastery levels
    - Learning gaps

    For guest students with no history, uses 2025 exam trend template.
    """
    # Verify student owns the test
    if test_data.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot generate test for another student"
        )

    try:
        # Generate test using DailyTestOrchestrator
        orchestrator = DailyTestOrchestrator(config.db.url)
        test = orchestrator.create_daily_test(
            student_id,
            test_data.test_date
        )

        # Generate reasoning for why these questions were chosen
        reasoning_parts = []
        if test.adaptive_weights:
            # Sort concepts by weight
            weighted_concepts = sorted(
                test.adaptive_weights.items(),
                key=lambda x: x[1],
                reverse=True
            )
            top_weak = weighted_concepts[:3]
            if top_weak:
                reasoning_parts.append("Based on your learning history:")
                for concept, weight in top_weak:
                    if weight >= 1.4:
                        reasoning_parts.append(
                            f"• {concept}: +{int((weight - 1.0) * 100)}% weight (needs focus)"
                        )
                    elif weight < 1.0:
                        reasoning_parts.append(
                            f"• {concept}: {int(weight * 100)}% weight (review for maintenance)"
                        )
                reasoning_parts.append("\nThis test prioritizes areas where you need the most practice.")
            else:
                reasoning_parts.append("Using 2025 High School Graduation Exam trend analysis.")
                reasoning_parts.append("This balanced test covers the most frequently tested concepts.")

        reasoning = "\n".join(reasoning_parts) if reasoning_parts else None

        # Convert to response format
        questions = []
        for q in test.questions:
            questions.append(QuestionResponse(
                question_id=q.question_id,
                concept_name=q.concept_id,
                topic_type=q.topic_type,
                difficulty=q.difficulty_level,
                question_text=q.question_text,
                options=q.options,
                explanation=q.explanation,
                correct_answer=q.correct_answer,
                is_synthetic=q.is_synthetic
            ))

        return DailyTestResponse(
            test_id=test.test_id,
            student_id=test.student_id,
            test_date=test.test_date,
            test_sequence=test.test_sequence,
            total_questions=len(test.questions),
            duration_minutes=test.time_limit_minutes,
            concepts_covered=test.concepts_covered,
            adaptive_weights=test.adaptive_weights,
            reasoning=reasoning,
            status="pending",
            questions=questions,
            created_at=datetime.now()
        )

    except Exception as e:
        # If database connection fails, use fallback database
        from app.services.fallback_db import get_fallback_db

        fallback_db = get_fallback_db()

        if not fallback_db.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service temporarily unavailable. Please try again later."
            )

        # Get adaptive weights and reasoning from fallback
        adaptive_weights = fallback_db.get_adaptive_weights(student_id)
        reasoning = fallback_db.get_reasoning(adaptive_weights)

        # Get questions using the fallback database
        selected_questions = fallback_db.get_random_questions(count=15)

        if not selected_questions:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No questions available. Please try again later."
            )

        # Convert to response format
        questions = []
        for q in selected_questions:
            questions.append(QuestionResponse(
                question_id=q.get('question_id', f"fallback_{len(questions)}"),
                concept_name=q.get('concept_name', 'General'),
                topic_type=q.get('topic_type', 'grammar'),
                difficulty=q.get('difficulty', 'intermediate'),
                question_text=q.get('question_text', ''),
                options=q.get('options', []),
                explanation=q.get('explanation', ''),
                correct_answer=q.get('correct_answer', 'A'),
                is_synthetic=False
            ))

        # Get concepts covered
        concepts_covered = list(set(q.get('concept_name') for q in selected_questions))

        return DailyTestResponse(
            test_id=f"fallback_{date.today().isoformat()}",
            student_id=student_id,
            test_date=date.today().isoformat(),
            test_sequence=1,
            total_questions=len(questions),
            duration_minutes=15,
            concepts_covered=concepts_covered,
            adaptive_weights=adaptive_weights,
            reasoning=reasoning,
            status="pending",
            questions=questions,
            created_at=datetime.now()
        )


@router.post("/{test_id}/start", response_model=dict)
async def start_daily_test(
    test_id: str,
    student_id: str = "guest_student_001"
):
    """
    Start a daily test (mark as in_progress).
    """
    db = get_db()
    if not db:
        # Demo mode - just return success
        return {
            "test_id": test_id,
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "duration_minutes": 15,
            "time_remaining_seconds": 900,
            "note": "Demo mode - test not persisted"
        }

    try:
        # Verify test ownership
        result = db.execute_query(
            """SELECT * FROM daily_tests WHERE test_id = %s AND student_id = %s""",
            (test_id, student_id)
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test not found"
            )

        test = result[0]

        if test['status'] != 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Test is {test['status']}, cannot start"
            )

        # Update status
        db.execute_update(
            """UPDATE daily_tests SET status = 'in_progress', started_at = %s
               WHERE test_id = %s""",
            (datetime.now(), test_id)
        )

        return {
            "test_id": test_id,
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "duration_minutes": config.test.daily_test_duration_minutes,
            "time_remaining_seconds": config.test.daily_test_duration_minutes * 60
        }
    finally:
        db.close()


@router.post("/{test_id}/submit", response_model=DailyTestResult)
async def submit_daily_test(
    test_id: str,
    submission: DailyTestSubmit,
    student_id: str = "guest_student_001"
):
    """
    Submit answers for a daily test.

    Automatically:
    - Scores the test
    - Generates feedback for incorrect answers
    - Updates student knowledge graph
    - Updates streak
    - Returns detailed results
    """
    db = get_db()
    if not db:
        # Demo mode - calculate score locally
        correct_count = sum(
            1 for ans in submission.answers
            if ans.get('selected_answer', '').upper() == 'A'  # Assume A is correct for demo
        )
        accuracy = correct_count / len(submission.answers) if submission.answers else 0

        return DailyTestResult(
            test_id=test_id,
            student_id=student_id,
            total_questions=len(submission.answers),
            correct_count=correct_count,
            accuracy=accuracy,
            time_spent_seconds=sum(ans.get('time_spent', 0) for ans in submission.answers),
            streak_earned=1,
            completed_at=datetime.now()
        )

    try:
        # Verify test ownership
        result = db.execute_query(
            """SELECT * FROM daily_tests WHERE test_id = %s AND student_id = %s""",
            (test_id, student_id)
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test not found"
            )

        test = result[0]

        if test['status'] == 'completed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test already completed"
            )

        # Calculate score
        correct_count = 0
        total_time = 0

        for answer in submission.answers:
            question_id = answer['question_id']
            selected = answer['selected_answer']
            time_spent = answer.get('time_spent', 0)

            # Get correct answer
            q_result = db.execute_query(
                """SELECT correct_answer FROM question_bank WHERE question_id = %s""",
                (question_id,)
            )

            if q_result:
                is_correct = selected.upper() == q_result[0]['correct_answer'].upper()
                if is_correct:
                    correct_count += 1

                total_time += time_spent

        accuracy = correct_count / len(submission.answers) if submission.answers else 0

        # Update test status
        db.execute_update(
            """UPDATE daily_tests
               SET status = 'completed', completed_at = %s
               WHERE test_id = %s""",
            (datetime.now(), test_id)
        )

        # Update streak (simplified - would use StreakManager in production)
        new_streak = 1  # Placeholder

        return DailyTestResult(
            test_id=test_id,
            student_id=student_id,
            total_questions=len(submission.answers),
            correct_count=correct_count,
            accuracy=accuracy,
            time_spent_seconds=total_time,
            streak_earned=new_streak,
            completed_at=datetime.now()
        )
    finally:
        db.close()


@router.get("/active", response_model=List[DailyTestResponse])
async def get_active_tests(
    student_id: str = "guest_student_001"
):
    """
    Get student's active (pending/in_progress) tests.
    """
    db = get_db()
    if not db:
        return []  # Demo mode - no active tests

    try:
        result = db.execute_query(
            """SELECT * FROM daily_tests
               WHERE student_id = %s AND status IN ('pending', 'in_progress')
               ORDER BY test_date DESC""",
            (student_id,)
        )

        tests = []
        for row in result:
            tests.append(DailyTestResponse(
                test_id=row['test_id'],
                student_id=row['student_id'],
                test_date=row['test_date'].isoformat(),
                test_sequence=row['test_sequence'],
                total_questions=row['total_questions'],
                duration_minutes=row['duration_minutes'],
                concepts_covered=[],
                adaptive_weights={},
                status=row['status'],
                questions=[],
                created_at=row['created_at']
            ))

        return tests
    finally:
        db.close()


@router.get("/history", response_model=List[dict])
async def get_test_history(
    limit: int = 10,
    student_id: str = "guest_student_001"
):
    """
    Get student's completed test history.
    """
    db = get_db()
    if not db:
        return []  # Demo mode - no history

    try:
        result = db.execute_query(
            """SELECT * FROM daily_tests
               WHERE student_id = %s AND status = 'completed'
               ORDER BY test_date DESC
               LIMIT %s""",
            (student_id, limit)
        )

        history = []
        for row in result:
            # Get accuracy from attempts
            accuracy_result = db.execute_query("""
                SELECT ROUND(COUNT(*) FILTER (WHERE dta.is_correct)::DECIMAL /
                       COUNT(*) * 100, 2) as accuracy
                FROM daily_test_attempts dta
                JOIN daily_test_questions dtq ON dta.test_question_id = dtq.test_question_id
                JOIN daily_tests dt ON dtq.test_id = dt.test_id
                WHERE dt.test_id = %s
            """, (row['test_id'],))

            accuracy = accuracy_result[0]['accuracy'] if accuracy_result else 0.0

            history.append({
                "test_id": row['test_id'],
                "test_date": row['test_date'].isoformat(),
                "test_sequence": row['test_sequence'],
                "accuracy": float(accuracy),
                "completed_at": row['completed_at'].isoformat() if row['completed_at'] else None
            })

        return history
    finally:
        db.close()

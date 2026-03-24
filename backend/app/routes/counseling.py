"""
from app.routes.students import GUEST_STUDENT_ID
Counseling endpoints - University admission recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.database import DatabaseManager
from app.models.api.responses import (
    UniversityRecommendation, CounselingReport, RecoveryPlan
)
from app.services.counseling import AdmissionCounselorAgent
from app.config import get_config

router = APIRouter()

config = get_config()


@router.get("/report", response_model=CounselingReport)
async def get_counseling_report(
    student_id: str = "guest_student_001"
):
    """
    Generate comprehensive university admission counseling report.

    Includes:
    - Current predicted score
    - Safe, target, and reach schools
    - Recovery plan for weak areas
    - Strategic recommendations
    - Days until exam countdown
    """
    try:
        counselor = AdmissionCounselorAgent(config.db.url)
        report = counselor.generate_counseling_report(student_id)
        counselor.close()

        return CounselingReport(
            student_id=report.student_id,
            generated_at=report.generated_at,
            current_predicted_score=report.current_predicted_score,
            target_score=report.target_score,
            days_until_exam=report.days_until_exam,
            safe_schools=[
                UniversityRecommendation(**school.__dict__)
                for school in report.safe_schools
            ],
            target_schools=[
                UniversityRecommendation(**school.__dict__)
                for school in report.target_schools
            ],
            reach_schools=[
                UniversityRecommendation(**school.__dict__)
                for school in report.reach_schools
            ],
            recovery_plan=RecoveryPlan(**report.recovery_plan.__dict__),
            overall_strategy=report.overall_strategy,
            key_recommendations=report.key_recommendations
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate counseling report: {str(e)}"
        )


@router.get("/universities")
async def get_universities(
    search: str = None,
    province: str = None,
    subject_group: str = None,
    min_benchmark: float = None,
    max_benchmark: float = None,
    db: DatabaseManager = Depends()
):
    """
    Search Vietnamese universities with admission benchmarks.

    Filter by:
    - search: Search in university or major name
    - province: Filter by province
    - subject_group: Filter by subject group (A01, D01, C03, etc.)
    - min_benchmark/max_benchmark: Filter by benchmark score range
    """
    from app.services.counseling import VIETNAMESE_UNIVERSITY_BENCHMARKS

    universities = []
    for uni_data in VIETNAMESE_UNIVERSITY_BENCHMARKS:
        # Apply filters
        if province and uni_data['province'] != province:
            continue

        for major in uni_data['majors']:
            # Subject group filter
            if subject_group and major['subject_group'] != subject_group:
                continue

            # Benchmark range filter
            benchmark = major.get('year_2025') or major.get('year_2024', 25.0)
            if min_benchmark and benchmark < min_benchmark:
                continue
            if max_benchmark and benchmark > max_benchmark:
                continue

            # Search filter
            if search:
                search_lower = search.lower()
                if (search_lower not in uni_data['university_name'].lower() and
                    search_lower not in major['major_name'].lower()):
                    continue

            universities.append({
                "university_name": uni_data['university_name'],
                "university_code": uni_data['university_code'],
                "province": uni_data['province'],
                "major_name": major['major_name'],
                "major_code": major['major_code'],
                "subject_group": major['subject_group'],
                "english_weight": major['english_weight'],
                "benchmark_2024": major.get('year_2024'),
                "benchmark_2025": major.get('year_2025'),
                "admission_quota": major.get('quota', 0)
            })

    return {
        "count": len(universities),
        "universities": universities
    }


@router.get("/universities/similar")
async def get_similar_universities(
    benchmark_score: float,
    tolerance: float = 2.0,
    subject_group: str = None,
    db: DatabaseManager = Depends()
):
    """
    Get universities with similar benchmark scores.

    Useful for finding alternative options based on predicted score.
    """
    from app.services.counseling import VIETNAMESE_UNIVERSITY_BENCHMARKS

    min_score = benchmark_score - tolerance
    max_score = benchmark_score + tolerance

    universities = []
    for uni_data in VIETNAMESE_UNIVERSITY_BENCHMARKS:
        for major in uni_data['majors']:
            if subject_group and major['subject_group'] != subject_group:
                continue

            benchmark = major.get('year_2025') or major.get('year_2024', 25.0)

            if min_score <= benchmark <= max_score:
                universities.append({
                    "university_name": uni_data['university_name'],
                    "province": uni_data['province'],
                    "major_name": major['major_name'],
                    "subject_group": major['subject_group'],
                    "benchmark": benchmark,
                    "english_weight": major['english_weight'],
                    "gap": benchmark_score - benchmark
                })

    # Sort by gap (closest first)
    universities.sort(key=lambda x: abs(x['gap']))

    return {
        "benchmark_score": benchmark_score,
        "tolerance": tolerance,
        "count": len(universities),
        "universities": universities
    }


@router.get("/recovery-plan", response_model=RecoveryPlan)
async def get_recovery_plan(
    student_id: str = "guest_student_001"
):
    """
    Get personalized recovery plan for weak areas.

    Focuses on top weak concepts with:
    - Priority ordering
    - Study schedule
    - Daily practice recommendations
    - Expected improvement timeline
    """
    try:
        counselor = AdmissionCounselorAgent(config.db.url)

        # Get full report and extract recovery plan
        report = counselor.generate_counseling_report(student_id)
        counselor.close()

        return RecoveryPlan(**report.recovery_plan.__dict__)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recovery plan: {str(e)}"
        )


@router.get("/exam-countdown")
async def get_exam_countdown():
    """
    Get countdown information for the national exam.

    Returns:
    - Exam date
    - Days remaining
    - Weeks remaining
    - Study milestones
    """
    from app.services.counseling import ExamCountdownManager

    exam_date = ExamCountdownManager.get_exam_date()
    days_until = ExamCountdownManager.get_days_until_exam(exam_date)
    weeks_until = ExamCountdownManager.get_weeks_until_exam(exam_date)
    milestones = ExamCountdownManager.get_study_milestones(weeks_until)

    return {
        "exam_date": exam_date.isoformat(),
        "days_until_exam": days_until,
        "weeks_until_exam": weeks_until,
        "today": date.today().isoformat(),
        "milestones": milestones,
        "urgency": "high" if weeks_until < 4 else "medium" if weeks_until < 12 else "low"
    }


@router.get("/predictions")
async def get_admission_predictions(
    student_id: str = "guest_student_001",
    db: DatabaseManager = Depends()
):
    """
    Get admission probability predictions for various universities.

    Based on current predicted score and university benchmarks.
    """
    try:
        counselor = AdmissionCounselorAgent(config.db.url)
        report = counselor.generate_counseling_report(student_id)
        counselor.close()

        # Combine all recommendations
        all_recommendations = (
            report.safe_schools + report.target_schools + report.reach_schools
        )

        # Sort by admission probability
        all_recommendations.sort(
            key=lambda x: x.admission_probability,
            reverse=True
        )

        return {
            "student_id": student_id,
            "current_predicted_score": report.current_predicted_score,
            "total_options": len(all_recommendations),
            "recommendations": [
                {
                    "university_name": r.university_name,
                    "major_name": r.major_name,
                    "benchmark_score": r.benchmark_score,
                    "admission_probability": r.admission_probability,
                    "risk_level": r.risk_level
                }
                for r in all_recommendations
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get predictions: {str(e)}"
        )

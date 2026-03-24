"""
Smart English Test-Prep Agent - University Admission Counselor
Phase 5: Strategic Consulting & University Admission AI

This module handles:
1. University admission benchmark database (Điểm chuẩn)
2. Admission probability calculation
3. Recovery plan generation for weak areas
4. University/major recommendations based on predicted score
5. Exam countdown integration
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, date
from collections import defaultdict

from anthropic import Anthropic
import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector

from app.config import get_config


# =====================================================
# DATA MODELS
# =====================================================

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
    subject_group: str  # A01, D01, etc.
    english_weight: float  # How much English counts (0.0-1.0)
    year_2024: Optional[float] = None  # 2024 benchmark score
    year_2025: Optional[float] = None  # 2025 benchmark score (projected)
    admission_quota: int = 0
    competition_ratio: float = 0.0


@dataclass
class RecoveryPlan:
    """Personalized recovery plan for weak areas."""

    student_id: str
    plan_id: str
    target_exam_date: str
    weeks_remaining: int

    # Weakness focus
    weak_concepts: List[str]  # Top 3-5 concepts to master
    priority_ordering: List[Tuple[str, float]]  # (concept, urgency_score)

    # Study schedule
    weekly_study_hours: float
    study_schedule: Dict[str, List[str]]  # Week-by-week breakdown

    # Daily practice
    daily_practice_recommendations: List[Dict[str, Any]]

    # Expected outcomes
    expected_score_improvement: float
    target_score: str
    current_predicted_score: float
    gap_to_target: float

    # Milestones
    milestones: List[Dict[str, Any]]


@dataclass
class UniversityRecommendation:
    """University/major recommendation for a student."""

    university_name: str
    major_name: str
    benchmark_score: float
    predicted_student_score: float
    admission_probability: float  # 0-100
    match_score: float  # 0-100
    gap_to_benchmark: float  # Can be negative (above benchmark)
    recommendation_reason: str
    risk_level: str  # 'safe', 'target', 'reach'
    application_strategy: str


@dataclass
class AdmissionCounselingReport:
    """Complete admission counseling report."""

    student_id: str
    generated_at: str

    # Current status
    current_predicted_score: float
    target_score: float
    days_until_exam: int

    # Recommendations
    safe_schools: List[UniversityRecommendation]  # >80% probability
    target_schools: List[UniversityRecommendation]  # 50-80% probability
    reach_schools: List[UniversityRecommendation]  # <50% probability

    # Recovery plan
    recovery_plan: RecoveryPlan

    # Strategic advice
    overall_strategy: str
    key_recommendations: List[str]


# =====================================================
# UNIVERSITY BENCHMARK DATA
# =====================================================

VIETNAMESE_UNIVERSITY_BENCHMARKS = [
    # National Universities
    {
        'university_name': 'Đại học Quốc gia Hà Nội',
        'university_code': 'VNU',
        'province': 'Hà Nội',
        'majors': [
            {'major_name': 'Nhật Bản học', 'major_code': 'NJ', 'subject_group': 'D01', 'english_weight': 1.0, 'year_2024': 28.5, 'year_2025': 28.0, 'quota': 50},
            {'major_name': 'Trung Quốc học', 'major_code': 'TC', 'subject_group': 'D01', 'english_weight': 1.0, 'year_2024': 27.0, 'year_2025': 27.5, 'quota': 60},
            {'major_name': 'Hàn Quốc học', 'major_code': 'HK', 'subject_group': 'D01', 'english_weight': 1.0, 'year_2024': 26.5, 'year_2025': 26.0, 'quota': 55},
            {'major_name': 'Ngôn ngữ Anh', 'major_code': 'NA', 'subject_group': 'D01', 'english_weight': 1.0, 'year_2024': 29.0, 'year_2025': 28.5, 'quota': 100},
        ]
    },
    {
        'university_name': 'Đại học Quốc gia TP.HCM',
        'university_code': 'VNU-HCM',
        'province': 'TP. Hồ Chí Minh',
        'majors': [
            {'major_name': 'Nhật Bản học', 'major_code': 'NJ', 'subject_group': 'D01', 'english_weight': 1.0, 'year_2024': 27.5, 'year_2025': 27.0, 'quota': 45},
            {'major_name': 'Trung Quốc học', 'major_code': 'TC', 'subject_group': 'D01', 'english_weight': 1.0, 'year_2024': 26.0, 'year_2025': 26.5, 'quota': 50},
            {'major_name': 'Ngôn ngữ Anh', 'major_code': 'NA', 'subject_group': 'D01', 'english_weight': 1.0, 'year_2024': 28.0, 'year_2025': 28.0, 'quota': 80},
        ]
    },
    {
        'university_name': 'Đại học Ngoại ngữ - ĐHQG Hà Nội',
        'university_code': 'ULIS',
        'province': 'Hà Nội',
        'majors': [
            {'major_name': 'Sư phạm Tiếng Anh', 'major_code': 'SPA', 'subject_group': 'D01', 'english_weight': 1.0, 'year_2024': 29.5, 'year_2025': 29.0, 'quota': 200},
            {'major_name': 'Ngôn ngữ Anh thương mại', 'major_code': 'NAT', 'subject_group': 'D01', 'english_weight': 1.0, 'year_2024': 28.0, 'year_2025': 28.5, 'quota': 80},
            {'major_name': 'Phiên dịch tiếng Anh', 'major_code': 'PA', 'subject_group': 'D01', 'english_weight': 1.0, 'year_2024': 30.0, 'year_2025': 29.5, 'quota': 40},
        ]
    },
    {
        'university_name': 'Đại học Kinh tế Quốc dân',
        'university_code': 'NEU',
        'province': 'Hà Nội',
        'majors': [
            {'major_name': 'Kinh doanh đối ngoại', 'major_code': 'KDDN', 'subject_group': 'A01', 'english_weight': 0.3, 'year_2024': 26.5, 'year_2025': 26.0, 'quota': 150},
            {'major_name': 'Kinh tế học', 'major_code': 'KT', 'subject_group': 'A01', 'english_weight': 0.2, 'year_2024': 25.5, 'year_2025': 25.0, 'quota': 200},
            {'major_name': 'Tài chính - Ngân hàng', 'major_code': 'TCNH', 'subject_group': 'A01', 'english_weight': 0.25, 'year_2024': 27.0, 'year_2025': 26.5, 'quota': 180},
        ]
    },
    {
        'university_name': 'Đại học Ngoại thương',
        'university_code': 'FTU',
        'province': 'Hà Nội',
        'majors': [
            {'major_name': 'Kinh doanh quốc tế', 'major_code': 'KDTQ', 'subject_group': 'A01', 'english_weight': 0.3, 'year_2024': 28.5, 'year_2025': 28.0, 'quota': 120},
            {'major_name': 'Tài chính quốc tế', 'major_code': 'TCTQ', 'subject_group': 'A01', 'english_weight': 0.3, 'year_2024': 27.5, 'year_2025': 27.0, 'quota': 80},
        ]
    },
    {
        'university_name': 'Học viện Báo chí và Tuyên truyền',
        'university_code': 'AJC',
        'province': 'Hà Nội',
        'majors': [
            {'major_name': 'Quan hệ công chúng', 'major_code': 'QHCC', 'subject_group': 'C03', 'english_weight': 0.25, 'year_2024': 24.5, 'year_2025': 24.0, 'quota': 100},
            {'major_name': 'Báo chí', 'major_code': 'BC', 'subject_group': 'C03', 'english_weight': 0.2, 'year_2024': 24.0, 'year_2025': 24.0, 'quota': 120},
        ]
    },
    {
        'university_name': 'Đại học Sư phạm Hà Nội',
        'university_code': 'HNUE',
        'province': 'Hà Nội',
        'majors': [
            {'major_name': 'Sư phạm Tiếng Anh', 'major_code': 'SPA', 'subject_group': 'D01', 'english_weight': 1.0, 'year_2024': 26.0, 'year_2025': 26.0, 'quota': 150},
        ]
    },
    {
        'university_name': 'Đại học Sư phạm TP.HCM',
        'university_code': 'HCMUE',
        'province': 'TP. Hồ Chí Minh',
        'majors': [
            {'major_name': 'Sư phạm Tiếng Anh', 'major_code': 'SPA', 'subject_group': 'D01', 'english_weight': 1.0, 'year_2024': 25.5, 'year_2025': 25.0, 'quota': 130},
        ]
    },
    {
        'university_name': 'Đại học Công nghiệp',
        'university_code': 'HAI',
        'province': 'Hà Nội',
        'majors': [
            {'major_name': 'Công nghệ thông tin', 'major_code': 'IT', 'subject_group': 'A01', 'english_weight': 0.2, 'year_2024': 23.0, 'year_2025': 23.5, 'quota': 300},
            {'major_name': 'Kinh doanh thương mại', 'major_code': 'KDTM', 'subject_group': 'D01', 'english_weight': 0.5, 'year_2024': 22.5, 'year_2025': 23.0, 'quota': 200},
        ]
    },
    {
        'university_name': 'Đại học Thương mại',
        'university_code': 'TBU',
        'province': 'Hà Nội',
        'majors': [
            {'major_name': 'Marketing', 'major_code': 'MKT', 'subject_group': 'A01', 'english_weight': 0.25, 'year_2024': 24.5, 'year_2025': 24.0, 'quota': 150},
            {'major_name': 'Quản trị kinh doanh', 'major_code': 'QTKD', 'subject_group': 'A01', 'english_weight': 0.25, 'year_2024': 24.0, 'year_2025': 24.0, 'quota': 200},
        ]
    },
]


# =====================================================
# EXAM COUNTDOWN MANAGER
# =====================================================

class ExamCountdownManager:
    """
    Manages exam date countdown and milestones.

    Official Vietnamese National High School Exam dates:
    - Usually late June to early July
    - Dates vary slightly each year
    """

    # Official exam dates (year: date)
    EXAM_DATES = {
        2024: date(2024, 6, 27),  # June 27, 2024
        2025: date(2025, 6, 26),  # June 26, 2025 (projected)
        2026: date(2026, 6, 25),  # June 25, 2026 (projected)
    }

    @classmethod
    def get_exam_date(cls, year: int = None) -> date:
        """Get the exam date for a given year."""
        if year is None:
            year = date.today().year

        # Use current year if available, otherwise project
        if year in cls.EXAM_DATES:
            return cls.EXAM_DATES[year]

        # Project for future years (late June)
        return date(year, 6, 25)

    @classmethod
    def get_days_until_exam(cls, exam_date: date = None) -> int:
        """Get number of days until the exam."""
        if exam_date is None:
            exam_date = cls.get_exam_date()

        today = date.today()
        days_until = (exam_date - today).days
        return max(0, days_until)

    @classmethod
    def get_weeks_until_exam(cls, exam_date: date = None) -> int:
        """Get number of weeks until the exam."""
        days = cls.get_days_until_exam(exam_date)
        return max(0, days // 7)

    @classmethod
    def get_study_milestones(cls, weeks_remaining: int) -> List[Dict[str, Any]]:
        """
        Generate study milestones based on time remaining.

        Args:
            weeks_remaining: Number of weeks until exam

        Returns:
            List of milestone dictionaries
        """
        milestones = []

        if weeks_remaining >= 12:
            milestones.append({
                'phase': 'Foundation Building',
                'week_range': f"Weeks 1-{weeks_remaining - 8}",
                'focus': 'Complete all grammar concepts, build vocabulary base',
                'target_mastery': '70%'
            })

        if weeks_remaining >= 8:
            milestones.append({
                'phase': 'Intensive Practice',
                'week_range': f"Weeks {max(1, weeks_remaining - 8)}-{weeks_remaining - 4}",
                'focus': 'Daily tests, weak concept reinforcement',
                'target_mastery': '80%'
            })

        if weeks_remaining >= 4:
            milestones.append({
                'phase': 'Exam Simulation',
                'week_range': f"Weeks {max(1, weeks_remaining - 4)}-{weeks_remaining}",
                'focus': 'Full mock exams, time management, error reduction',
                'target_mastery': '85%'
            })

        if weeks_remaining >= 2:
            milestones.append({
                'phase': 'Final Review',
                'week_range': f"Weeks {max(1, weeks_remaining - 2)}-{weeks_remaining}",
                'focus': 'Review mistakes, memorize key patterns, stay confident',
                'target_mastery': 'Target score'
            })

        return milestones


# =====================================================
# RECOVERY PLAN GENERATOR
# =====================================================

class RecoveryPlanGenerator:
    """
    Generates personalized recovery plans for weak areas.

    Analyzes student performance and creates targeted study plans.
    """

    def __init__(self, db_connection: str):
        """Initialize database connection."""
        self.conn = psycopg2.connect(db_connection)
        register_vector(self.conn)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def generate_recovery_plan(
        self,
        student_id: str,
        target_score: str,
        weeks_remaining: int
    ) -> RecoveryPlan:
        """
        Generate a comprehensive recovery plan.

        Args:
            student_id: Student's unique ID
            target_score: Target score (6.5_plus, 8_plus, 9_plus)
            weeks_remaining: Weeks until exam

        Returns:
            RecoveryPlan with detailed study schedule
        """
        # Get student's weak concepts
        weak_concepts = self._get_weak_concepts(student_id, limit=5)

        # Get current predicted score
        current_score = self._calculate_predicted_score(student_id)

        # Parse target score
        target_numeric = self._parse_target_score(target_score)
        gap = target_numeric - current_score

        # Priority ordering (by weakness score and recency)
        priority_ordering = self._prioritize_concepts(student_id, weak_concepts)

        # Calculate study schedule
        study_schedule = self._create_study_schedule(
            weeks_remaining, priority_ordering
        )

        # Daily practice recommendations
        daily_practice = self._generate_daily_practice(
            priority_ordering, weeks_remaining
        )

        # Calculate expected improvement
        expected_improvement = self._estimate_improvement(
            current_score, gap, weeks_remaining, daily_practice
        )

        # Generate milestones
        milestones = ExamCountdownManager.get_study_milestones(weeks_remaining)

        # Get exam date
        exam_date = ExamCountdownManager.get_exam_date()

        plan = RecoveryPlan(
            student_id=student_id,
            plan_id=f"recovery_{student_id}_{datetime.now().strftime('%Y%m%d')}",
            target_exam_date=exam_date.isoformat(),
            weeks_remaining=weeks_remaining,
            weak_concepts=[c[0] for c in priority_ordering],
            priority_ordering=priority_ordering,
            weekly_study_hours=15.0,  # Recommended 2-3 hours/day
            study_schedule=study_schedule,
            daily_practice_recommendations=daily_practice,
            expected_score_improvement=expected_improvement,
            target_score=target_score,
            current_predicted_score=current_score,
            gap_to_target=gap,
            milestones=milestones
        )

        # Save to database
        self._save_recovery_plan(plan)

        return plan

    def _get_weak_concepts(
        self, student_id: str, limit: int = 5
    ) -> List[str]:
        """Get student's weakest concepts."""
        self.cursor.execute("""
            SELECT c.concept_name, skg.mastery_level, skg.weakness_score
            FROM student_knowledge_graph skg
            JOIN concepts c ON skg.concept_id = c.concept_id
            WHERE skg.student_id = %s
            ORDER BY skg.weakness_score DESC, skg.last_attempt_at DESC
            LIMIT %s
        """, (student_id, limit))

        return [row['concept_name'] for row in self.cursor.fetchall()]

    def _calculate_predicted_score(self, student_id: str) -> float:
        """
        Calculate student's predicted score based on performance.

        Uses weighted average of:
        - Latest mega test score (60%)
        - Daily test accuracy (30%)
        - Knowledge graph mastery (10%)
        """
        # Get latest mega test score
        self.cursor.execute("""
            SELECT overall_score
            FROM mega_tests
            WHERE student_id = %s AND status = 'completed'
            ORDER BY test_date DESC
            LIMIT 1
        """, (student_id,))

        mega_test = self.cursor.fetchone()

        # Get daily test accuracy
        self.cursor.execute("""
            SELECT overall_accuracy
            FROM students
            WHERE student_id = %s
        """, (student_id,))

        student = self.cursor.fetchone()

        # Get knowledge graph average mastery
        self.cursor.execute("""
            SELECT AVG(mastery_level) as avg_mastery
            FROM student_knowledge_graph
            WHERE student_id = %s
        """, (student_id,))

        kg = self.cursor.fetchone()

        # Calculate weighted average
        mega_score = mega_test['overall_score'] if mega_test else 0.0
        daily_accuracy = float(student['overall_accuracy']) if student else 0.0
        kg_mastery = float(kg['avg_mastery']) if kg and kg['avg_mastery'] else 0.0

        predicted = (mega_score * 0.6) + (daily_accuracy * 0.3) + (kg_mastery * 0.1)

        return round(predicted, 2)

    def _parse_target_score(self, target_score: str) -> float:
        """Convert target score string to numeric."""
        score_map = {
            '6.5_plus': 6.5,
            '8_plus': 8.0,
            '8.5_plus': 8.5,
            '9_plus': 9.0
        }
        return score_map.get(target_score, 8.0)

    def _prioritize_concepts(
        self, student_id: str, weak_concepts: List[str]
    ) -> List[Tuple[str, float]]:
        """
        Prioritize concepts by urgency.

        Factors:
        - Weakness score (40%)
        - Streak of incorrect answers (30%)
        - Recency of last attempt (20%)
        - Exam frequency (10%)
        """
        prioritized = []

        for concept in weak_concepts:
            self.cursor.execute("""
                SELECT
                    weakness_score,
                    streak_incorrect,
                    last_attempt_at
                FROM student_knowledge_graph skg
                JOIN concepts c ON skg.concept_id = c.concept_id
                WHERE skg.student_id = %s AND c.concept_name = %s
            """, (student_id, concept))

            data = self.cursor.fetchone()

            if data:
                # Calculate urgency score
                weakness = data['weakness_score'] or 0.0
                streak = data['streak_incorrect'] or 0
                recency_days = (datetime.now().date() - data['last_attempt_at']).days if data['last_attempt_at'] else 999

                urgency = (weakness * 0.4) + (streak * 10 * 0.3) + ((100 - min(recency_days, 100)) * 0.2) + (10 * 0.1)
                prioritized.append((concept, urgency))

        # Sort by urgency (descending)
        prioritized.sort(key=lambda x: x[1], reverse=True)

        return prioritized

    def _create_study_schedule(
        self, weeks_remaining: int, concepts: List[Tuple[str, float]]
    ) -> Dict[str, List[str]]:
        """
        Create week-by-week study schedule.

        Distributes concepts across weeks with reinforcement.
        """
        schedule = {}

        # Top concepts get more focus weeks
        top_concepts = concepts[:3]

        for week in range(1, weeks_remaining + 1):
            week_focus = []

            # Rotate through concepts
            for i, (concept, _) in enumerate(top_concepts):
                # Focus on concept i in week i, i+4, i+8, etc.
                if (week - i - 1) % 4 == 0:
                    week_focus.append(f"Master {concept}")

            # Add review weeks every 4 weeks
            if week % 4 == 0:
                week_focus.append("Review all concepts from previous 3 weeks")
                week_focus.append("Take practice test")

            # Add daily test practice
            week_focus.append("Complete daily 15-minute tests")

            schedule[f"Week {week}"] = week_focus

        return schedule

    def _generate_daily_practice(
        self, concepts: List[Tuple[str, float]], weeks_remaining: int
    ) -> List[Dict[str, Any]]:
        """Generate daily practice recommendations."""
        practice = []

        for concept, urgency in concepts:
            practice.append({
                'concept': concept,
                'urgency': urgency,
                'daily_minutes': 20 if urgency > 50 else 15,
                'exercises_per_day': 5 if urgency > 50 else 3,
                'focus': f"Practice {concept} rules and patterns"
            })

        return practice

    def _estimate_improvement(
        self, current_score: float, gap: float,
        weeks_remaining: int, daily_practice: List[Dict]
    ) -> float:
        """
        Estimate expected score improvement.

        Based on:
        - Gap to target
        - Time remaining
        - Practice intensity
        """
        if weeks_remaining == 0 or gap <= 0:
            return 0.0

        # Base improvement per week with consistent practice
        base_weekly_improvement = 0.3  # 0.3 points per week

        # Adjust for practice intensity
        total_daily_minutes = sum(p['daily_minutes'] for p in daily_practice)
        intensity_multiplier = min(total_daily_minutes / 60.0, 2.0)  # Cap at 2x

        # Calculate expected improvement
        expected = base_weekly_improvement * intensity_multiplier * weeks_remaining

        # Cap at the gap (can't exceed target)
        return round(min(expected, gap), 2)

    def _save_recovery_plan(self, plan: RecoveryPlan):
        """Save recovery plan to database."""
        self.cursor.execute("""
            INSERT INTO recovery_plans (
                plan_id, student_id, generated_at,
                target_exam_date, weeks_remaining, weak_concepts,
                study_schedule, daily_practice_recommendations,
                expected_score_improvement, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING plan_id
        """, (
            plan.plan_id, plan.student_id, datetime.now().isoformat(),
            plan.target_exam_date, plan.weeks_remaining, plan.weak_concepts,
            json.dumps(plan.study_schedule), json.dumps(plan.daily_practice_recommendations),
            plan.expected_score_improvement, 'active'
        ))

        self.conn.commit()

    def close(self):
        """Close database connection."""
        self.conn.close()


# =====================================================
# ADMISSION COUNSELOR AGENT
# =====================================================

class AdmissionCounselorAgent:
    """
    The University Admission Counselor.

    Provides:
    - University/major recommendations
    - Admission probability calculation
    - Recovery plan generation
    - Strategic guidance
    """

    def __init__(self, db_connection: str):
        """Initialize the counselor agent."""
        self.db_connection = db_connection
        self.recovery_generator = RecoveryPlanGenerator(db_connection)
        self.countdown_manager = ExamCountdownManager()

    def generate_counseling_report(
        self, student_id: str
    ) -> AdmissionCounselingReport:
        """
        Generate a complete admission counseling report.

        Args:
            student_id: Student's unique ID

        Returns:
            Comprehensive counseling report with recommendations
        """
        # Get current predicted score
        current_score = self.recovery_generator._calculate_predicted_score(student_id)

        # Get student info
        self.recovery_generator.cursor.execute("""
            SELECT target_score FROM students WHERE student_id = %s
        """, (student_id,))

        student_info = self.recovery_generator.cursor.fetchone()
        target_score_str = student_info['target_score'] if student_info else '8_plus'
        target_numeric = self.recovery_generator._parse_target_score(target_score_str)

        # Calculate days until exam
        days_until_exam = self.countdown_manager.get_days_until_exam()
        weeks_remaining = self.countdown_manager.get_weeks_until_exam()

        # Generate recommendations
        all_recommendations = self._generate_all_recommendations(
            current_score, target_score_str
        )

        # Categorize by safety
        safe_schools = [r for r in all_recommendations if r.admission_probability > 80]
        target_schools = [r for r in all_recommendations if 50 <= r.admission_probability <= 80]
        reach_schools = [r for r in all_recommendations if r.admission_probability < 50]

        # Generate recovery plan
        recovery_plan = self.recovery_generator.generate_recovery_plan(
            student_id, target_score_str, weeks_remaining
        )

        # Generate strategic advice
        overall_strategy = self._generate_strategy(
            current_score, target_numeric, weeks_remaining, safe_schools
        )

        key_recommendations = self._generate_key_recommendations(
            current_score, target_numeric, weeks_remaining, recovery_plan
        )

        return AdmissionCounselingReport(
            student_id=student_id,
            generated_at=datetime.now().isoformat(),
            current_predicted_score=current_score,
            target_score=target_numeric,
            days_until_exam=days_until_exam,
            safe_schools=safe_schools,
            target_schools=target_schools,
            reach_schools=reach_schools,
            recovery_plan=recovery_plan,
            overall_strategy=overall_strategy,
            key_recommendations=key_recommendations
        )

    def _generate_all_recommendations(
        self, predicted_score: float, target_score_str: str
    ) -> List[UniversityRecommendation]:
        """Generate university recommendations."""
        recommendations = []

        for uni_data in VIETNAMESE_UNIVERSITY_BENCHMARKS:
            for major in uni_data['majors']:
                # Calculate admission probability
                benchmark = major.get('year_2025') or major.get('year_2024', 25.0)
                probability = self._calculate_admission_probability(
                    predicted_score, benchmark, major['english_weight']
                )

                # Determine risk level
                if probability >= 80:
                    risk_level = 'safe'
                elif probability >= 50:
                    risk_level = 'target'
                else:
                    risk_level = 'reach'

                # Generate recommendation
                recommendation = UniversityRecommendation(
                    university_name=uni_data['university_name'],
                    major_name=major['major_name'],
                    benchmark_score=benchmark,
                    predicted_student_score=predicted_score,
                    admission_probability=probability,
                    match_score=self._calculate_match_score(predicted_score, benchmark),
                    gap_to_benchmark=predicted_score - benchmark,
                    recommendation_reason=self._generate_recommendation_reason(
                        predicted_score, benchmark, major
                    ),
                    risk_level=risk_level,
                    application_strategy=self._generate_application_strategy(risk_level)
                )

                # Only include if reasonable chance (>30%)
                if probability > 30:
                    recommendations.append(recommendation)

        # Sort by probability (descending)
        recommendations.sort(key=lambda r: r.admission_probability, reverse=True)

        return recommendations

    def _calculate_admission_probability(
        self, predicted_score: float, benchmark: float, english_weight: float
    ) -> float:
        """
        Calculate admission probability.

        Formula:
        probability = (predicted_score / benchmark) * 100

        Adjusted by English weight (higher weight = more direct correlation)
        """
        base_probability = (predicted_score / benchmark) * 100

        # Adjust by English weight
        # If English weight is 1.0, use direct correlation
        # If lower, reduce correlation slightly (other subjects matter more)
        adjustment = 0.8 + (english_weight * 0.2)  # 0.8 to 1.0 range

        probability = base_probability * adjustment

        # Clamp to 0-100
        return max(0.0, min(100.0, probability))

    def _calculate_match_score(
        self, predicted_score: float, benchmark: float
    ) -> float:
        """
        Calculate how well student matches the university.

        Considers:
        - Score alignment
        - Safety margin
        """
        if predicted_score >= benchmark:
            # Above benchmark - calculate how much
            excess = predicted_score - benchmark
            match = 85.0 + min(excess * 2, 15.0)  # 85-100 range
        else:
            # Below benchmark - calculate gap
            gap = benchmark - predicted_score
            match = max(50.0, 100.0 - (gap * 5))  # 50-100 range

        return round(match, 2)

    def _generate_recommendation_reason(
        self, predicted_score: float, benchmark: float, major: Dict
    ) -> str:
        """Generate explanation for recommendation."""
        if predicted_score >= benchmark:
            excess = predicted_score - benchmark
            return f"Your predicted score ({predicted_score}) is {excess:.1f} points above the benchmark ({benchmark}). Strong chance of admission."

        elif predicted_score >= benchmark * 0.95:
            gap = benchmark - predicted_score
            return f"Your predicted score ({predicted_score}) is {gap:.1f} points below the benchmark ({benchmark}). Very close - possible with strong performance."

        elif predicted_score >= benchmark * 0.85:
            gap = benchmark - predicted_score
            return f"Your predicted score ({predicted_score}) is {gap:.1f} points below the benchmark ({benchmark}). Reach target - needs improvement."

        else:
            gap = benchmark - predicted_score
            return f"Your predicted score ({predicted_score}) is {gap:.1f} points below the benchmark ({benchmark}). Significant improvement needed."

    def _generate_application_strategy(self, risk_level: str) -> str:
        """Generate application strategy advice."""
        strategies = {
            'safe': "Apply with confidence. This is a strong safety option. Consider as backup plan.",
            'target': "Good match if you maintain current performance and show improvement. Consider applying.",
            'reach': "Challenging but possible with significant improvement. Only apply if showing strong upward trend."
        }
        return strategies.get(risk_level, "Consult with counselor.")

    def _generate_strategy(
        self, current_score: float, target_score: float,
        weeks_remaining: int, safe_schools: List[UniversityRecommendation]
    ) -> str:
        """Generate overall strategy."""

        if not safe_schools:
            return f"Priority: Raise predicted score from {current_score} to at least 25.0 to qualify for most universities. Focus on weak concepts and consistent practice."

        gap = target_score - current_score

        if gap <= 0:
            return f"Excellent! Your predicted score ({current_score}) meets or exceeds your target ({target_score}). Focus on maintaining performance and exploring top-tier options."

        elif gap <= 1.0:
            return f"Very close! You're within {gap} points of your target. Maintain current trajectory and focus on eliminating careless errors."

        elif gap <= 2.0:
            return f"On track! You're {gap} points from target. Intensify practice on weak concepts over the next {weeks_remaining} weeks."

        else:
            return f"Accelerated effort needed. You're {gap} points from target with {weeks_remaining} weeks remaining. Follow recovery plan closely."

    def _generate_key_recommendations(
        self, current_score: float, target_score: float,
        weeks_remaining: int, recovery_plan: RecoveryPlan
    ) -> List[str]:
        """Generate key action recommendations."""

        recommendations = []

        # Time-based recommendations
        if weeks_remaining >= 12:
            recommendations.append(f"You have {weeks_remaining} weeks - ample time for comprehensive improvement")
        elif weeks_remaining >= 8:
            recommendations.append(f"{weeks_remaining} weeks remaining - focus on weak concepts now")
        elif weeks_remaining >= 4:
            recommendations.append(f"Critical phase: {weeks_remaining} weeks left - intensive practice needed")
        else:
            recommendations.append(f"Final push: {weeks_remaining} weeks - focus on review and confidence")

        # Score-based recommendations
        gap = target_score - current_score
        if gap > 0:
            recommendations.append(f"Focus on top 3 weak concepts to close {gap:.1f} point gap")
            recommendations.append(f"Target: {recovery_plan.expected_score_improvement:.1f} point improvement by exam")

        # Daily practice recommendations
        top_concepts = recovery_plan.weak_concepts[:3]
        if top_concepts:
            recommendations.append(f"Priority concepts this week: {', '.join(top_concepts)}")

        return recommendations

    def close(self):
        """Close database connections."""
        self.recovery_generator.close()


# =====================================================
# EXAMPLE USAGE
# =====================================================

def main():
    """Example usage of the Admission Counselor."""

    from app.config import get_config

    config = get_config()
    counselor = AdmissionCounselorAgent(config.db.url)

    student_id = "student_001"

    # Generate counseling report
    print(f"\n{'='*70}")
    print(f"ADMISSION COUNSELING REPORT")
    print(f"{'='*70}\n")

    report = counselor.generate_counseling_report(student_id)

    print(f"Student: {report.student_id}")
    print(f"Generated: {report.generated_at}")
    print(f"\nCurrent Status:")
    print(f"  Predicted Score: {report.current_predicted_score}")
    print(f"  Target Score: {report.target_score}")
    print(f"  Days Until Exam: {report.days_until_exam}")

    print(f"\n{'='*70}")
    print(f"SAFE SCHOOLS (>80% probability)")
    print(f"{'='*70}")
    for school in report.safe_schools[:5]:
        print(f"\n{school.university_name} - {school.major_name}")
        print(f"  Probability: {school.admission_probability:.1f}%")
        print(f"  Gap: {school.gap_to_benchmark:+.1f}")
        print(f"  {school.recommendation_reason}")

    print(f"\n{'='*70}")
    print(f"RECOVERY PLAN")
    print(f"{'='*70}")
    print(f"Weeks Remaining: {report.recovery_plan.weeks_remaining}")
    print(f"Weak Concepts: {', '.join(report.recovery_plan.weak_concepts[:3])}")
    print(f"Expected Improvement: +{report.recovery_plan.expected_score_improvement} points")

    print(f"\n{'='*70}")
    print(f"KEY RECOMMENDATIONS")
    print(f"{'='*70}")
    for rec in report.key_recommendations:
        print(f"  • {rec}")

    print(f"\n{'='*70}")
    print(f"OVERALL STRATEGY")
    print(f"{'='*70}")
    print(report.overall_strategy)

    counselor.close()


if __name__ == '__main__':
    main()

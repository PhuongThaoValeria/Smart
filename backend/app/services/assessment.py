"""
Smart English Test-Prep Agent - Assessment Service
Phase 4: Bi-weekly Mega Test & Performance Analytics

This module handles:
1. Bi-weekly full-length mock exams (50 questions, 60 minutes)
2. Competency Map generation (Radar Chart data)
3. Performance analytics and progress tracking
4. Aggregate error data from 14-day period
5. Strength vs Weakness analysis
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
import numpy as np

from anthropic import Anthropic
import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector

from app.config import get_config
from app.services.daily_tests import DailyTestOrchestrator, SyntheticQuestionGenerator


# =====================================================
# DATA MODELS
# =====================================================

@dataclass
class CompetencyScore:
    """Score for a specific competency area."""

    area: str  # 'Grammar', 'Vocabulary', 'Reading Comprehension', 'Phonetics'
    score: float  # 0-100
    question_count: int
    correct_count: int
    improvement_needed: bool
    priority_level: str  # 'critical', 'high', 'medium', 'low'


@dataclass
class CompetencyMap:
    """
    Complete competency map for a student.
    Suitable for Radar Chart visualization.
    """

    student_id: str
    mega_test_id: str
    test_date: str

    # Four main areas (Radar Chart data)
    grammar: CompetencyScore
    vocabulary: CompetencyScore
    reading_comprehension: CompetencyScore
    phonetics: CompetencyScore

    # Overall metrics
    overall_score: float
    percentile_rank: float
    strengths: List[str]
    weaknesses: List[str]

    # Detailed breakdown
    topic_breakdown: Dict[str, Dict[str, Any]]
    improvement_recommendations: List[Dict[str, Any]]

    # Trend data
    score_trend: List[float]  # Previous mega test scores
    improvement_rate: float  # % change from previous test


@dataclass
class MegaTest:
    """Bi-weekly full-length mock exam."""

    mega_test_id: str
    student_id: str
    test_date: str
    test_sequence: int

    # Test configuration
    total_questions: int = 50
    duration_minutes: int = 60
    questions_per_topic: Dict[str, int] = None

    # Content
    questions: List[Any] = None  # Would be GeneratedQuestion objects

    # Results (after completion)
    status: str = 'pending'  # 'pending', 'in_progress', 'completed', 'abandoned'
    overall_score: Optional[float] = None
    competency_map: Optional[CompetencyMap] = None

    def __post_init__(self):
        if self.questions_per_topic is None:
            self.questions_per_topic = {
                'grammar': 12,
                'vocabulary': 10,
                'reading_comprehension': 20,
                'phonetics': 8
            }


# =====================================================
# MEGA TEST SCHEDULER
# =====================================================

class MegaTestScheduler:
    """
    Schedules and triggers bi-weekly mega tests.

    Rules:
    - Trigger every 14 days from student's start date
    - Or trigger manually by student/teacher
    - Can only have one active mega test at a time
    """

    def __init__(self, db_connection: str):
        """Initialize database connection."""
        self.conn = psycopg2.connect(db_connection)
        register_vector(self.conn)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        self.config = get_config()

    def is_mega_test_due(self, student_id: str) -> Tuple[bool, Optional[date]]:
        """
        Check if a mega test is due for a student.

        Returns:
            (is_due, due_date)
        """
        # Get last mega test date
        self.cursor.execute("""
            SELECT MAX(test_date) as last_test_date, COUNT(*) as test_count
            FROM mega_tests
            WHERE student_id = %s AND status = 'completed'
        """, (student_id,))

        result = self.cursor.fetchone()

        if not result or result['test_count'] == 0:
            # First test - due immediately
            return True, date.today()

        last_date = result['last_test_date']
        days_since_last = (date.today() - last_date).days
        interval_days = self.config.test.mega_test_interval_days

        if days_since_last >= interval_days:
            return True, date.today()
        else:
            next_due = last_date + timedelta(days=interval_days)
            return False, next_due

    def get_days_until_next_test(self, student_id: str) -> int:
        """Get number of days until next mega test is due."""
        is_due, due_date = self.is_mega_test_due(student_id)

        if is_due:
            return 0
        else:
            return (due_date - date.today()).days

    def has_active_test(self, student_id: str) -> bool:
        """Check if student has an active (in-progress) mega test."""
        self.cursor.execute("""
            SELECT COUNT(*) as count
            FROM mega_tests
            WHERE student_id = %s AND status IN ('pending', 'in_progress')
        """, (student_id,))

        return self.cursor.fetchone()['count'] > 0

    def close(self):
        """Close database connection."""
        self.conn.close()


# =====================================================
# COMPETENCY MAP GENERATOR
# =====================================================

class CompetencyMapGenerator:
    """
    Generates competency maps from mega test results.

    Aggregates data from:
    - Mega test performance
    - Last 14 days of daily tests
    - Student knowledge graph
    """

    def __init__(self, db_connection: str):
        """Initialize database connection."""
        self.conn = psycopg2.connect(db_connection)
        register_vector(self.conn)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def generate_competency_map(
        self, student_id: str, mega_test_id: str
    ) -> CompetencyMap:
        """
        Generate a complete competency map for a student.

        Args:
            student_id: Student's unique ID
            mega_test_id: The completed mega test

        Returns:
            CompetencyMap with all scores and recommendations
        """
        # Get mega test date
        self.cursor.execute("""
            SELECT test_date, test_sequence, overall_score
            FROM mega_tests
            WHERE mega_test_id = %s
        """, (mega_test_id,))

        test_info = self.cursor.fetchone()

        # Generate scores for each area
        grammar = self._calculate_area_score(student_id, mega_test_id, 'grammar')
        vocabulary = self._calculate_area_score(student_id, mega_test_id, 'vocabulary')
        reading = self._calculate_area_score(
            student_id, mega_test_id, 'reading_comprehension'
        )
        phonetics = self._calculate_area_score(student_id, mega_test_id, 'phonetics')

        # Calculate overall score
        overall = self._calculate_overall_score([grammar, vocabulary, reading, phonetics])

        # Get historical scores for trend
        score_trend = self._get_score_trend(student_id, test_info['test_sequence'])

        # Calculate improvement rate
        improvement_rate = 0.0
        if score_trend:
            improvement_rate = ((overall - score_trend[-1]) / score_trend[-1]) * 100

        # Identify strengths and weaknesses
        all_scores = [grammar, vocabulary, reading, phonetics]
        strengths = [s.area for s in all_scores if s.score >= 70.0]
        weaknesses = [s.area for s in all_scores if s.score < 60.0]

        # Generate detailed breakdown
        topic_breakdown = self._generate_topic_breakdown(student_id, mega_test_id)

        # Generate improvement recommendations
        recommendations = self._generate_recommendations(
            student_id, weaknesses, topic_breakdown
        )

        # Calculate percentile rank (simplified - would use student population in production)
        percentile = self._calculate_percentile_rank(overall)

        return CompetencyMap(
            student_id=student_id,
            mega_test_id=mega_test_id,
            test_date=test_info['test_date'].isoformat(),
            grammar=grammar,
            vocabulary=vocabulary,
            reading_comprehension=reading,
            phonetics=phonetics,
            overall_score=overall,
            percentile_rank=percentile,
            strengths=strengths,
            weaknesses=weaknesses,
            topic_breakdown=topic_breakdown,
            improvement_recommendations=recommendations,
            score_trend=score_trend,
            improvement_rate=improvement_rate
        )

    def _calculate_area_score(
        self, student_id: str, mega_test_id: str, topic_type: str
    ) -> CompetencyScore:
        """Calculate score for a specific competency area."""

        # Get questions from mega test for this topic
        self.cursor.execute("""
            SELECT
                c.topic_type,
                COUNT(*) as question_count,
                SUM(CASE WHEN mta.is_correct THEN 1 ELSE 0 END) as correct_count
            FROM mega_test_questions mtq
            JOIN question_bank qb ON mtq.question_id = qb.question_id
            JOIN concepts c ON qb.concept_id = c.concept_id
            JOIN mega_test_attempts mta ON mtq.mega_test_question_id = mta.mega_test_question_id
            WHERE mtq.mega_test_id = %s
                AND c.topic_type = %s
            GROUP BY c.topic_type
        """, (mega_test_id, topic_type))

        result = self.cursor.fetchone()

        if not result or result['question_count'] == 0:
            # No questions for this topic
            return CompetencyScore(
                area=topic_type.replace('_', ' ').title(),
                score=0.0,
                question_count=0,
                correct_count=0,
                improvement_needed=True,
                priority_level='low'
            )

        question_count = result['question_count']
        correct_count = result['correct_count']
        score = (correct_count / question_count) * 100 if question_count > 0 else 0.0

        # Determine priority level
        if score < 50:
            priority = 'critical'
            improvement_needed = True
        elif score < 60:
            priority = 'high'
            improvement_needed = True
        elif score < 70:
            priority = 'medium'
            improvement_needed = True
        else:
            priority = 'low'
            improvement_needed = False

        return CompetencyScore(
            area=topic_type.replace('_', ' ').title(),
            score=round(score, 2),
            question_count=question_count,
            correct_count=correct_count,
            improvement_needed=improvement_needed,
            priority_level=priority
        )

    def _calculate_overall_score(
        self, area_scores: List[CompetencyScore]
    ) -> float:
        """Calculate overall score from area scores."""
        if not area_scores:
            return 0.0

        # Weighted average (by question count)
        total_questions = sum(s.question_count for s in area_scores)
        if total_questions == 0:
            return 0.0

        weighted_sum = sum(s.score * s.question_count for s in area_scores)
        return round(weighted_sum / total_questions, 2)

    def _get_score_trend(self, student_id: str, current_sequence: int) -> List[float]:
        """Get historical mega test scores for trend analysis."""
        self.cursor.execute("""
            SELECT overall_score
            FROM mega_tests
            WHERE student_id = %s
                AND status = 'completed'
                AND test_sequence < %s
            ORDER BY test_sequence ASC
            LIMIT 10
        """, (student_id, current_sequence))

        return [row['overall_score'] for row in self.cursor.fetchall()]

    def _generate_topic_breakdown(
        self, student_id: str, mega_test_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """Generate detailed breakdown by sub-topic."""

        # Get performance by concept
        self.cursor.execute("""
            SELECT
                c.concept_name,
                c.topic_type,
                COUNT(*) as question_count,
                SUM(CASE WHEN mta.is_correct THEN 1 ELSE 0 END) as correct_count,
                ROUND(
                    SUM(CASE WHEN mta.is_correct THEN 1 ELSE 0 END)::DECIMAL /
                    COUNT(*) * 100, 2
                ) as accuracy
            FROM mega_test_questions mtq
            JOIN question_bank qb ON mtq.question_id = qb.question_id
            JOIN concepts c ON qb.concept_id = c.concept_id
            JOIN mega_test_attempts mta ON mtq.mega_test_question_id = mta.mega_test_question_id
            WHERE mtq.mega_test_id = %s
            GROUP BY c.concept_name, c.topic_type
            ORDER BY accuracy ASC
        """, (mega_test_id,))

        breakdown = {}
        for row in self.cursor.fetchall():
            topic = row['topic_type']
            if topic not in breakdown:
                breakdown[topic] = {}

            breakdown[topic][row['concept_name']] = {
                'accuracy': row['accuracy'],
                'question_count': row['question_count'],
                'correct_count': row['correct_count']
            }

        return breakdown

    def _generate_recommendations(
        self, student_id: str,
        weaknesses: List[str],
        topic_breakdown: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate personalized improvement recommendations."""

        recommendations = []

        # For each weak area, find the worst-performing concepts
        for weakness in weaknesses:
            weakness_key = weakness.lower().replace(' ', '_')
            concepts = topic_breakdown.get(weakness_key, {})

            # Sort by accuracy (worst first)
            sorted_concepts = sorted(
                concepts.items(),
                key=lambda x: x[1]['accuracy']
            )[:3]  # Top 3 worst concepts

            for concept_name, data in sorted_concepts:
                recommendations.append({
                    'area': weakness,
                    'concept': concept_name,
                    'current_accuracy': data['accuracy'],
                    'priority': 'high' if data['accuracy'] < 50 else 'medium',
                    'action': f'Review and practice {concept_name} rules',
                    'estimated_study_hours': max(1, int((100 - data['accuracy']) / 10))
                })

        # Sort by priority and accuracy
        recommendations.sort(key=lambda x: x['current_accuracy'])

        return recommendations[:10]  # Top 10 recommendations

    def _calculate_percentile_rank(self, overall_score: float) -> float:
        """
        Calculate percentile rank (simplified).
        In production, this would query actual student population data.
        """
        # Simplified calculation based on score ranges
        # This would be replaced with actual population data
        if overall_score >= 90:
            return 95.0
        elif overall_score >= 80:
            return 85.0
        elif overall_score >= 70:
            return 70.0
        elif overall_score >= 60:
            return 50.0
        else:
            return 30.0

    def save_competency_map(self, competency_map: CompetencyMap) -> str:
        """Save competency map to database."""
        self.cursor.execute("""
            INSERT INTO competency_maps (
                map_id, student_id, mega_test_id, generated_at,
                grammar_score, vocabulary_score, reading_comprehension_score,
                phonetics_score, topic_breakdown, strength_areas,
                weakness_areas, improvement_recommendations
            )
            VALUES (
                gen_random_uuid(), %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING map_id
        """, (
            competency_map.student_id,
            competency_map.mega_test_id,
            competency_map.test_date,
            competency_map.grammar.score,
            competency_map.vocabulary.score,
            competency_map.reading_comprehension.score,
            competency_map.phonetics.score,
            json.dumps(competency_map.topic_breakdown),
            competency_map.strengths,
            competency_map.weaknesses,
            json.dumps(competency_map.improvement_recommendations)
        ))

        self.conn.commit()
        return self.cursor.fetchone()['map_id']

    def close(self):
        """Close database connection."""
        self.conn.close()


# =====================================================
# MEGA TEST GENERATOR
# =====================================================

class MegaTestGenerator:
    """
    Generates bi-weekly mega tests.

    Uses exam trend data to create balanced tests covering all topics.
    """

    def __init__(self, db_connection: str):
        """Initialize generator."""
        self.db_connection = db_connection
        self.generator = SyntheticQuestionGenerator()
        self.conn = psycopg2.connect(db_connection)
        register_vector(self.conn)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def create_mega_test(
        self, student_id: str, test_date: date = None
    ) -> MegaTest:
        """
        Create a bi-weekly mega test for a student.

        Args:
            student_id: Student's unique ID
            test_date: Date for the test (defaults to today)

        Returns:
            MegaTest object with 50 generated questions
        """
        test_date = test_date or date.today()

        # Get test sequence
        sequence = self._get_next_test_sequence(student_id)

        # Get student's target score
        self.cursor.execute("""
            SELECT target_score FROM students WHERE student_id = %s
        """, (student_id,))

        student_info = self.cursor.fetchone()
        target_score = student_info['target_score'] if student_info else '8_plus'

        # Load concept patterns from exam trends
        concept_patterns = self._load_concept_patterns()

        # Generate questions for each topic
        questions = []
        questions_per_topic = {
            'grammar': 12,
            'vocabulary': 10,
            'reading_comprehension': 20,
            'phonetics': 8
        }

        existing_questions = self._get_student_existing_questions(student_id)

        for topic, count in questions_per_topic.items():
            topic_concepts = [
                c for c in concept_patterns
                if c['topic_type'] == topic
            ]

            # Distribute questions across concepts in this topic
            for concept in topic_concepts[:count]:  # Limit to count
                question = self.generator.generate_question_for_concept(
                    concept_name=concept['concept_name'],
                    topic_type=concept['topic_type'],
                    difficulty_level=self._determine_difficulty(target_score),
                    target_score=target_score,
                    exam_patterns=concept['example_patterns'],
                    grammar_rule=concept.get('grammar_rule'),
                    existing_questions=existing_questions
                )

                if question:
                    questions.append(question)
                    existing_questions.append(question.question_text)

                if len(questions) >= count:
                    break

        # Create mega test object
        mega_test = MegaTest(
            mega_test_id=f"mega_{student_id}_{test_date.strftime('%Y%m%d')}",
            student_id=student_id,
            test_date=test_date.isoformat(),
            test_sequence=sequence,
            total_questions=len(questions),
            duration_minutes=60,
            questions_per_topic=questions_per_topic,
            questions=questions,
            status='pending'
        )

        # Store in database
        self._store_mega_test(mega_test)

        return mega_test

    def _get_next_test_sequence(self, student_id: str) -> int:
        """Get next test sequence number."""
        self.cursor.execute("""
            SELECT COALESCE(MAX(test_sequence), 0) + 1
            FROM mega_tests
            WHERE student_id = %s
        """, (student_id,))

        return self.cursor.fetchone()[0]

    def _load_concept_patterns(self) -> List[Dict[str, Any]]:
        """Load concept patterns from exam trends."""
        self.cursor.execute("""
            SELECT
                c.concept_name,
                c.topic_type,
                etm.question_patterns,
                c.grammar_rule
            FROM exam_trend_matrix etm
            JOIN concepts c ON etm.concept_id = c.concept_id
            ORDER BY etm.question_count DESC
        """)

        return [dict(row) for row in self.cursor.fetchall()]

    def _get_student_existing_questions(self, student_id: str) -> List[str]:
        """Get questions student has already seen."""
        self.cursor.execute("""
            SELECT DISTINCT qb.question_text
            FROM question_bank qb
            JOIN mega_test_questions mtq ON qb.question_id = mtq.question_id
            JOIN mega_tests mt ON mtq.mega_test_id = mt.mega_test_id
            WHERE mt.student_id = %s
            LIMIT 200
        """, (student_id,))

        return [row['question_text'] for row in self.cursor.fetchall()]

    def _determine_difficulty(self, target_score: str) -> str:
        """Determine appropriate difficulty for target score."""
        difficulty_map = {
            '6.5_plus': 'intermediate',
            '8_plus': 'advanced',
            '8.5_plus': 'advanced',
            '9_plus': 'expert'
        }
        return difficulty_map.get(target_score, 'advanced')

    def _store_mega_test(self, mega_test: MegaTest):
        """Store mega test in database."""
        # Insert mega test record
        self.cursor.execute("""
            INSERT INTO mega_tests (
                mega_test_id, student_id, test_date, test_sequence,
                total_questions, duration_minutes, concepts_covered,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING mega_test_id
        """, (
            mega_test.mega_test_id, mega_test.student_id, mega_test.test_date,
            mega_test.test_sequence, mega_test.total_questions,
            mega_test.duration_minutes, [], mega_test.status
        ))

        self.conn.commit()

    def close(self):
        """Close database connection."""
        self.conn.close()


# =====================================================
# ASSESSMENT SERVICE (Public API)
# =====================================================

class AssessmentService:
    """
    High-level service for mega tests and competency maps.
    """

    def __init__(self, db_connection: str = None):
        """Initialize the service."""
        config = get_config()
        self.db_connection = db_connection or config.db.url

        self.scheduler = MegaTestScheduler(self.db_connection)
        self.generator = MegaTestGenerator(self.db_connection)
        self.map_generator = CompetencyMapGenerator(self.db_connection)

    def check_test_status(self, student_id: str) -> Dict[str, Any]:
        """
        Check mega test status for a student.

        Returns:
            Dict with test due info, days until next test, etc.
        """
        is_due, due_date = self.scheduler.is_mega_test_due(student_id)
        has_active = self.scheduler.has_active_test(student_id)
        days_until = self.scheduler.get_days_until_next_test(student_id)

        return {
            'is_due': is_due,
            'due_date': due_date.isoformat(),
            'has_active_test': has_active,
            'days_until_next_test': days_until,
            'can_start_new': is_due and not has_active
        }

    def create_mega_test(self, student_id: str) -> MegaTest:
        """Create a new mega test for a student."""
        return self.generator.create_mega_test(student_id)

    def generate_competency_map(
        self, student_id: str, mega_test_id: str
    ) -> CompetencyMap:
        """Generate and save competency map."""
        competency_map = self.map_generator.generate_competency_map(
            student_id, mega_test_id
        )
        self.map_generator.save_competency_map(competency_map)
        return competency_map

    def get_student_progress_summary(self, student_id: str) -> Dict[str, Any]:
        """Get comprehensive progress summary for a student."""
        # Get latest competency map
        self.map_generator.cursor.execute("""
            SELECT cm.*, mt.test_sequence
            FROM competency_maps cm
            JOIN mega_tests mt ON cm.mega_test_id = mt.mega_test_id
            WHERE cm.student_id = %s
            ORDER BY mt.test_sequence DESC
            LIMIT 1
        """, (student_id,))

        latest_map = self.map_generator.cursor.fetchone()

        if not latest_map:
            return {
                'has_completed_mega_test': False,
                'message': 'No mega tests completed yet'
            }

        return {
            'has_completed_mega_test': True,
            'test_sequence': latest_map['test_sequence'],
            'overall_score': latest_map['grammar_score'] + latest_map['vocabulary_score'] +
                           latest_map['reading_comprehension_score'] +
                           latest_map['phonetics_score'],
            'area_scores': {
                'grammar': latest_map['grammar_score'],
                'vocabulary': latest_map['vocabulary_score'],
                'reading': latest_map['reading_comprehension_score'],
                'phonetics': latest_map['phonetics_score']
            },
            'strengths': latest_map['strength_areas'],
            'weaknesses': latest_map['weakness_areas']
        }

    def close_all(self):
        """Close all database connections."""
        self.scheduler.close()
        self.generator.close()
        self.map_generator.close()


# =====================================================
# EXAMPLE USAGE
# =====================================================

def main():
    """Example usage of the Assessment Service."""

    from app.config import get_config

    config = get_config()
    service = AssessmentService(config.db.url)

    student_id = "student_001"

    # Check test status
    print(f"\n{'='*60}")
    print(f"Mega Test Status for {student_id}")
    print(f"{'='*60}")
    status = service.check_test_status(student_id)
    print(f"Is Due: {status['is_due']}")
    print(f"Days Until Next: {status['days_until_next_test']}")
    print(f"Has Active Test: {status['has_active_test']}")

    # If due, create a test
    if status['is_due'] and status['can_start_new']:
        print(f"\nCreating new mega test...")
        mega_test = service.create_mega_test(student_id)
        print(f"✓ Created: {mega_test.mega_test_id}")
        print(f"  Questions: {mega_test.total_questions}")
        print(f"  Duration: {mega_test.duration_minutes} minutes")

    # Get progress summary
    summary = service.get_student_progress_summary(student_id)
    print(f"\n{'='*60}")
    print(f"Progress Summary")
    print(f"{'='*60}")
    print(json.dumps(summary, indent=2))

    service.close_all()


if __name__ == '__main__':
    main()

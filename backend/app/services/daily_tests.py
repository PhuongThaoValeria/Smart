"""
Smart English Test-Prep Agent - Daily Adaptive Test Generator
Phase 2: Daily Adaptive Test Generator (The "15-Min Micro-Learning" Logic)

This module handles:
1. Generation of unique 15-question daily tests (Daily Sprint)
2. Synthetic data generation (no reuse of old questions)
3. Adaptive weighting: failed concepts get 40% weight increase next day
4. Streak system for engagement
5. Uses Trend Report as seed for question generation
"""

import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np

from anthropic import Anthropic

# Database imports
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

from app.config import get_config


# =====================================================
# DATA MODELS
# =====================================================

@dataclass
class GeneratedQuestion:
    """A synthetically generated question."""
    question_id: str
    question_text: str
    topic_type: str
    question_type: str
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty_level: str
    concept_id: str
    is_synthetic: bool = True


@dataclass
class DailyTest:
    """A 15-question daily test."""
    test_id: str
    student_id: str
    test_date: str
    test_sequence: int
    questions: List[GeneratedQuestion]
    concepts_covered: List[str]
    adaptive_weights: Dict[str, float]
    time_limit_minutes: int = 15
    estimated_duration_minutes: int = 12


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


# =====================================================
# SYNTHETIC QUESTION GENERATOR
# =====================================================

class SyntheticQuestionGenerator:
    """
    Generates brand new questions using AI based on exam patterns.
    Ensures NO reuse of old questions.
    """

    def __init__(self):
        config = get_config()
        # Use STEP_API_KEY if available, otherwise fall back to ANTHROPIC_API_KEY
        api_key = config.llm.get_api_key()
        if not api_key:
            raise ValueError("No API key found. Please set STEP_API_KEY or ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=api_key)
        self.embedding_model = SentenceTransformer(
            'sentence-transformers/all-MiniLM-L6-v2'
        )

    def generate_question_for_concept(
        self,
        concept_name: str,
        topic_type: str,
        difficulty_level: str,
        target_score: str,
        exam_patterns: List[str],
        grammar_rule: Optional[str] = None,
        existing_questions: List[str] = None
    ) -> GeneratedQuestion:
        """
        Generate a unique question for a specific concept.

        Args:
            concept_name: The grammatical concept (e.g., "Reported Speech")
            topic_type: grammar, vocabulary, etc.
            difficulty_level: basic, intermediate, advanced, expert
            target_score: 6.5_plus, 8_plus, 9_plus
            exam_patterns: Common patterns from exam analysis
            grammar_rule: The grammar rule explanation
            existing_questions: List of existing question texts to avoid duplication

        Returns:
            GeneratedQuestion object
        """

        existing_context = ""
        if existing_questions:
            existing_context = f"\n\nIMPORTANT: Do NOT use questions similar to these:\n" + \
                              "\n".join([f"- {q[:100]}..." for q in existing_questions[:5]])

        prompt = f"""You are an expert English test question writer for Vietnamese high school students.

Generate a UNIQUE {difficulty_level} level question on "{concept_name}" ({topic_type}).

Target score level: {target_score}

Grammar Rule: {grammar_rule or 'See common patterns below'}

Common exam patterns for this concept:
{chr(10).join(f"- {p}" for p in exam_patterns[:5])}

{existing_context}

REQUIREMENTS:
1. Create a BRAND NEW question - do not copy from existing exams or textbooks
2. Use {difficulty_level} vocabulary and sentence structures appropriate for Vietnamese high school students
3. Make it realistic for the Vietnamese National High School Graduation Exam
4. Question type: multiple choice with 4 options (A, B, C, D)
5. Include distractors that reflect common student mistakes

Return JSON with this exact structure:
{{
    "question_text": "The full question text",
    "question_type": "multiple_choice",
    "options": ["A) first option", "B) second option", "C) third option", "D) fourth option"],
    "correct_answer": "A",
    "explanation": "Clear explanation of why this is correct and why others are wrong",
    "difficulty_level": "{difficulty_level}",
    "grammar_rule_applied": "Which specific rule this question tests"
}}

Return ONLY the JSON object, nothing else."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                temperature=0.8,  # Higher temperature for more creative/unique questions
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            question_data = json.loads(response_text)

            # Generate unique ID
            question_id = f"synthetic_{concept_name.lower().replace(' ', '_')}_" + \
                          f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            return GeneratedQuestion(
                question_id=question_id,
                question_text=question_data['question_text'],
                topic_type=topic_type,
                question_type=question_data.get('question_type', 'multiple_choice'),
                options=question_data['options'],
                correct_answer=question_data['correct_answer'].upper(),
                explanation=question_data['explanation'],
                difficulty_level=difficulty_level,
                concept_id=concept_name,
                is_synthetic=True
            )

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error generating question for {concept_name}: {e}")
            return None

    def generate_batch_for_concept(
        self,
        concept_name: str,
        topic_type: str,
        count: int,
        difficulty_level: str,
        target_score: str,
        exam_patterns: List[str],
        grammar_rule: Optional[str] = None,
        existing_questions: List[str] = None
    ) -> List[GeneratedQuestion]:
        """Generate multiple questions for a concept."""
        questions = []
        attempts = 0
        max_attempts = count * 3  # Allow retries for failed generations

        while len(questions) < count and attempts < max_attempts:
            question = self.generate_question_for_concept(
                concept_name, topic_type, difficulty_level, target_score,
                exam_patterns, grammar_rule, existing_questions
            )

            if question:
                # Check for uniqueness using semantic similarity
                is_unique = self._check_uniqueness(question, existing_questions or [])
                if is_unique:
                    questions.append(question)
                    if existing_questions is not None:
                        existing_questions.append(question.question_text)

            attempts += 1

        return questions

    def _check_uniqueness(
        self,
        new_question: GeneratedQuestion,
        existing_questions: List[str],
        similarity_threshold: float = 0.85
    ) -> bool:
        """
        Check if the new question is semantically different from existing ones.
        Uses sentence embeddings to detect similarity.
        """
        if not existing_questions:
            return True

        # Generate embedding for new question
        new_embedding = self.embedding_model.encode(
            new_question.question_text,
            normalize_embeddings=True
        )

        # Generate embeddings for existing questions
        existing_embeddings = self.embedding_model.encode(
            existing_questions[:50],  # Check against recent 50
            normalize_embeddings=True
        )

        # Calculate cosine similarities
        similarities = np.dot(existing_embeddings, new_embedding)

        # If any existing question is too similar, reject
        if np.max(similarities) > similarity_threshold:
            return False

        return True


# =====================================================
# ADAPTIVE WEIGHTING ENGINE
# =====================================================

class AdaptiveWeightingEngine:
    """
    Manages adaptive weighting for concepts based on student performance.
    Failed concepts get 40% weight increase for the next day.
    """

    def __init__(self, db_connection: str):
        """Initialize database connection."""
        self.conn = psycopg2.connect(db_connection)
        register_vector(self.conn)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def get_student_learning_state(self, student_id: str) -> StudentLearningState:
        """
        Retrieve student's current learning state from knowledge graph.

        Returns:
            StudentLearningState with weak/strong concepts and streak info
        """
        # Get weak concepts (prioritize recent failures)
        self.cursor.execute("""
            SELECT
                c.concept_name,
                skg.mastery_level,
                skg.weakness_score,
                skg.adaptive_weight,
                skg.streak_incorrect,
                skg.last_attempt_at
            FROM student_knowledge_graph skg
            JOIN concepts c ON skg.concept_id = c.concept_id
            WHERE skg.student_id = %s
            ORDER BY
                skg.streak_incorrect DESC,
                skg.weakness_score DESC,
                skg.last_attempt_at DESC NULLS LAST
            LIMIT 20
        """, (student_id,))

        weak_concepts = [
            (row['concept_name'], row['weakness_score'])
            for row in self.cursor.fetchall()
        ]

        # Get strong concepts
        self.cursor.execute("""
            SELECT
                c.concept_name,
                skg.mastery_level
            FROM student_knowledge_graph skg
            JOIN concepts c ON skg.concept_id = c.concept_id
            WHERE skg.student_id = %s AND skg.mastery_level >= 70.0
            ORDER BY skg.mastery_level DESC
            LIMIT 10
        """, (student_id,))

        strong_concepts = [
            (row['concept_name'], row['mastery_level'])
            for row in self.cursor.fetchall()
        ]

        # Get student info
        self.cursor.execute("""
            SELECT current_streak, target_score,
                   COALESCE(overall_accuracy, 0) as overall_mastery
            FROM students
            WHERE student_id = %s
        """, (student_id,))

        student_info = self.cursor.fetchone()

        # Get last test date
        self.cursor.execute("""
            SELECT test_date
            FROM daily_tests
            WHERE student_id = %s AND status = 'completed'
            ORDER BY test_date DESC
            LIMIT 1
        """, (student_id,))

        last_test = self.cursor.fetchone()
        last_test_date = last_test['test_date'] if last_test else None

        return StudentLearningState(
            student_id=student_id,
            weak_concepts=weak_concepts,
            strong_concepts=strong_concepts,
            current_streak=student_info['current_streak'],
            last_test_date=last_test_date,
            target_score=student_info['target_score'],
            overall_mastery=float(student_info['overall_mastery'])
        )

    def calculate_adaptive_weights(
        self, learning_state: StudentLearningState
    ) -> Dict[str, float]:
        """
        Calculate adaptive weights for concept selection.

        Rules:
        - Concepts with recent failures: weight * 1.4
        - Concepts with mastery > 80%: weight * 0.5
        - Base weight: 1.0
        """
        weights = {}

        for concept_name, weakness_score in learning_state.weak_concepts:
            # Higher weakness = higher weight
            # Recent failures get 40% boost
            base_weight = 1.0 + (weakness_score / 100.0)
            weights[concept_name] = min(base_weight * 1.4, 3.0)  # Cap at 3.0

        for concept_name, mastery_level in learning_state.strong_concepts:
            # Reduce weight for mastered concepts
            if mastery_level >= 80:
                weights[concept_name] = 0.5
            else:
                weights[concept_name] = 0.7

        return weights

    def get_existing_student_questions(
        self, student_id: str, limit: int = 100
    ) -> List[str]:
        """Get list of questions the student has already seen."""
        self.cursor.execute("""
            SELECT DISTINCT qb.question_text
            FROM question_bank qb
            JOIN daily_test_questions dtq ON qb.question_id = dtq.question_id
            JOIN daily_tests dt ON dtq.test_id = dt.test_id
            WHERE dt.student_id = %s
            ORDER BY qb.question_text
            LIMIT %s
        """, (student_id, limit))

        return [row['question_text'] for row in self.cursor.fetchall()]

    def close(self):
        """Close database connection."""
        self.conn.close()


# =====================================================
# DAILY TEST ORCHESTRATOR
# =====================================================

class DailyTestOrchestrator:
    """
    Orchestrates the creation of personalized daily tests.
    Combines adaptive learning with synthetic generation.
    """

    def __init__(self, db_connection: str):
        """Initialize components."""
        self.db_connection = db_connection
        self.generator = SyntheticQuestionGenerator()
        self.weighting_engine = AdaptiveWeightingEngine(db_connection)

        # Database connection for storing tests
        self.conn = psycopg2.connect(db_connection)
        register_vector(self.conn)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def create_daily_test(
        self, student_id: str, test_date: Optional[str] = None
    ) -> DailyTest:
        """
        Create a personalized 15-question daily test.

        Args:
            student_id: Student's unique identifier
            test_date: Date for the test (defaults to today)

        Returns:
            DailyTest object with 15 generated questions
        """
        test_date = test_date or datetime.now().date()

        # Get student's learning state
        learning_state = self.weighting_engine.get_student_learning_state(student_id)

        # Calculate adaptive weights
        adaptive_weights = self.weighting_engine.calculate_adaptive_weights(learning_state)

        # Get exam trend data (from previous RAG analysis)
        concept_patterns = self._load_concept_patterns()

        # Select concepts for today's test
        selected_concepts = self._select_concepts_adaptive(
            learning_state, adaptive_weights, concept_patterns, count=15
        )

        # Get existing questions to avoid duplication
        existing_questions = self.weighting_engine.get_existing_student_questions(student_id)

        # Generate questions for each concept
        questions = []
        for concept_name, weight in selected_concepts:
            pattern = concept_patterns.get(concept_name, {})

            question = self.generator.generate_question_for_concept(
                concept_name=concept_name,
                topic_type=pattern.get('topic_type', 'grammar'),
                difficulty_level=self._determine_difficulty(
                    learning_state, concept_name, adaptive_weights
                ),
                target_score=learning_state.target_score,
                exam_patterns=pattern.get('example_patterns', []),
                grammar_rule=pattern.get('grammar_rule'),
                existing_questions=existing_questions
            )

            if question:
                questions.append(question)
                existing_questions.append(question.question_text)

        # Create test object
        test_sequence = self._get_next_test_sequence(student_id)

        daily_test = DailyTest(
            test_id=f"daily_{student_id}_{test_date.strftime('%Y%m%d')}",
            student_id=student_id,
            test_date=test_date.isoformat(),
            test_sequence=test_sequence,
            questions=questions[:15],  # Ensure exactly 15
            concepts_covered=[c[0] for c in selected_concepts],
            adaptive_weights=adaptive_weights,
            time_limit_minutes=15
        )

        # Store test in database
        self._store_daily_test(daily_test)

        return daily_test

    def _select_concepts_adaptive(
        self,
        learning_state: StudentLearningState,
        adaptive_weights: Dict[str, float],
        concept_patterns: Dict[str, Any],
        count: int = 15
    ) -> List[Tuple[str, float]]:
        """
        Select concepts for today's test using adaptive weighted sampling.

        Strategy:
        - 60% weak concepts (high adaptive weight)
        - 30% reinforcement (medium mastery)
        - 10% new/challenge topics
        """
        # Weighted sampling based on adaptive weights
        weighted_concepts = []

        for concept, weight in adaptive_weights.items():
            weighted_concepts.append((concept, weight))

        # Sort by weight (descending)
        weighted_concepts.sort(key=lambda x: x[1], reverse=True)

        # Select according to strategy
        selected = []

        # 60% weak concepts (9 questions)
        weak_count = int(count * 0.6)
        selected.extend(weighted_concepts[:weak_count])

        # 30% reinforcement (4 questions)
        reinforce_count = int(count * 0.3)
        if len(weighted_concepts) > weak_count:
            selected.extend(weighted_concepts[weak_count:weak_count + reinforce_count])

        # 10% challenge/new (2 questions)
        remaining = count - len(selected)
        # Add concepts not in student's history yet
        for concept in concept_patterns.keys():
            if concept not in adaptive_weights and remaining > 0:
                selected.append((concept, 1.0))
                remaining -= 1

        return selected

    def _determine_difficulty(
        self, learning_state: StudentLearningState,
        concept_name: str, adaptive_weights: Dict[str, float]
    ) -> str:
        """
        Determine appropriate difficulty for a concept.

        Rules:
        - High weight (failed recently): Start at basic, work up
        - Medium mastery: Intermediate
        - High mastery: Advanced
        """
        weight = adaptive_weights.get(concept_name, 1.0)

        if weight >= 2.0:  # Recently failed, struggling
            return 'basic'
        elif weight >= 1.4:  # Some difficulty
            return 'intermediate'
        elif weight >= 1.0:  # Normal
            return 'intermediate'
        else:  # Mastered - challenge them
            return 'advanced'

    def _load_concept_patterns(self) -> Dict[str, Any]:
        """Load concept patterns from exam trend analysis."""
        self.cursor.execute("""
            SELECT
                c.concept_name,
                c.topic_type,
                etm.question_patterns,
                c.grammar_rule
            FROM exam_trend_matrix etm
            JOIN concepts c ON etm.concept_id = c.concept_id
            ORDER BY etm.question_count DESC
            LIMIT 30
        """)

        patterns = {}
        for row in self.cursor.fetchall():
            patterns[row['concept_name']] = {
                'topic_type': row['topic_type'],
                'example_patterns': json.loads(row['question_patterns']) if row['question_patterns'] else [],
                'grammar_rule': row['grammar_rule']
            }

        return patterns

    def _get_next_test_sequence(self, student_id: str) -> int:
        """Get the next test sequence number for a student."""
        self.cursor.execute("""
            SELECT COALESCE(MAX(test_sequence), 0) + 1
            FROM daily_tests
            WHERE student_id = %s
        """, (student_id,))

        return self.cursor.fetchone()[0]

    def _store_daily_test(self, test: DailyTest):
        """Store the generated test in the database."""
        # Insert daily test record
        self.cursor.execute("""
            INSERT INTO daily_tests (
                test_id, student_id, test_date, test_sequence,
                total_questions, duration_minutes, concepts_covered,
                adaptive_weights, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (student_id, test_date) DO UPDATE SET
                questions = EXCLUDED.questions,
                adaptive_weights = EXCLUDED.adaptive_weights
            RETURNING test_id
        """, (
            test.test_id, test.student_id, test.test_date, test.test_sequence,
            len(test.questions), test.time_limit_minutes,
            test.concepts_covered, json.dumps(test.adaptive_weights), 'pending'
        ))

        self.conn.commit()

    def close(self):
        """Close database connections."""
        self.conn.close()
        self.weighting_engine.close()


# =====================================================
# STREAK MANAGER (Gamification)
# =====================================================

class StreakManager:
    """
    Manages student engagement streaks.

    Rules:
    - Complete test on consecutive days: streak increases
    - Miss a day: streak resets to 0
    - Streak bonuses: extra points, badges, etc.
    """

    def __init__(self, db_connection: str):
        self.conn = psycopg2.connect(db_connection)
        self.cursor = self.conn.cursor()

    def update_streak(self, student_id: str, test_date: str):
        """Update streak based on test completion."""
        # Get last test date
        self.cursor.execute("""
            SELECT MAX(test_date) as last_date, current_streak
            FROM daily_tests
            WHERE student_id = %s AND status = 'completed'
            GROUP BY student_id
        """, (student_id,))

        result = self.cursor.fetchone()

        if not result:
            # First test
            new_streak = 1
        else:
            last_date = result[0]
            current_streak = result[1] or 0

            # Check if consecutive day
            last_dt = datetime.strptime(last_date, '%Y-%m-%d').date()
            current_dt = datetime.strptime(test_date, '%Y-%m-%d').date()

            if (current_dt - last_dt).days == 1:
                new_streak = current_streak + 1
            elif (current_dt - last_dt).days == 0:
                new_streak = current_streak  # Same day, no change
            else:
                new_streak = 1  # Streak broken

        # Update student record
        self.cursor.execute("""
            UPDATE students
            SET current_streak = %s,
                longest_streak = GREATEST(longest_streak, %s)
            WHERE student_id = %s
        """, (new_streak, new_streak, student_id))

        self.conn.commit()

        return new_streak

    def get_streak_milestone_rewards(self, streak: int) -> Dict[str, Any]:
        """Get rewards for streak milestones."""
        milestones = {
            7: {"badge": "Week Warrior", "bonus_points": 50},
            14: {"badge": "Fortnight Fighter", "bonus_points": 100},
            30: {"badge": "Monthly Master", "bonus_points": 250},
            60: {"badge": "Double Diamond", "bonus_points": 500},
            100: {"badge": "Centurion", "bonus_points": 1000}
        }

        return milestones.get(streak, {"badge": None, "bonus_points": 0})

    def close(self):
        """Close database connection."""
        self.conn.close()


# =====================================================
# EXAMPLE USAGE
# =====================================================

def main():
    """Example usage of the Daily Test Generator."""

    # Configuration
    DB_CONNECTION = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5432/english_testprep'
    )
    STUDENT_ID = "student_123"

    # Initialize orchestrator
    orchestrator = DailyTestOrchestrator(DB_CONNECTION)
    streak_manager = StreakManager(DB_CONNECTION)

    # Generate today's test
    print("Generating personalized daily test...")
    daily_test = orchestrator.create_daily_test(STUDENT_ID)

    print(f"\n{'='*60}")
    print(f"Daily Test Generated - Day {daily_test.test_sequence}")
    print(f"{'='*60}")
    print(f"Student: {daily_test.student_id}")
    print(f"Date: {daily_test.test_date}")
    print(f"Questions: {len(daily_test.questions)}")
    print(f"Time Limit: {daily_test.time_limit_minutes} minutes")
    print(f"\nConcepts Covered:")
    for i, concept in enumerate(daily_test.concepts_covered, 1):
        weight = daily_test.adaptive_weights.get(concept, 1.0)
        print(f"  {i}. {concept} (weight: {weight:.2f})")

    print(f"\nFirst Question Preview:")
    if daily_test.questions:
        q = daily_test.questions[0]
        print(f"  Q: {q.question_text}")
        print(f"  Options: {q.options}")
        print(f"  Answer: {q.correct_answer}")

    # Simulate completion and update streak
    streak = streak_manager.update_streak(STUDENT_ID, daily_test.test_date)
    print(f"\nCurrent Streak: {streak} days")

    rewards = streak_manager.get_streak_milestone_rewards(streak)
    if rewards['badge']:
        print(f"🏆 Badge Earned: {rewards['badge']}!")
        print(f"   Bonus Points: +{rewards['bonus_points']}")

    # Cleanup
    orchestrator.close()
    streak_manager.close()

    print("\n✓ Test generation complete!")


if __name__ == '__main__':
    main()

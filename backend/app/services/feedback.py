"""
Smart English Test-Prep Agent - Feedback & Pedagogy Engine
Phase 3: Real-time Feedback & Pedagogy (The "Virtual Tutor" Logic)

This module handles:
1. Immediate, empathetic feedback for incorrect answers
2. Deep-dive explanations (why wrong, grammar rule, mini-examples)
3. Root cause analysis using Student Knowledge Graph
4. Vietnamese explanations for better comprehension
5. Personalized learning path recommendations
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from anthropic import Anthropic
import psycopg2
from psycopg2.extras import RealDictCursor
from pgvector.psycopg2 import register_vector

from app.config import get_config


# =====================================================
# DATA MODELS
# =====================================================

@dataclass
class RootCauseAnalysis:
    """Analysis of why a student got a question wrong."""

    concept_id: str
    concept_name: str
    root_cause: str  # e.g., "Confused Gerund with To-Infinitive"
    misconception_pattern: str  # The specific mistake pattern
    related_concepts: List[str]  # Concepts that might help
    priority_score: float  # How urgent this is to fix


@dataclass
class FeedbackResponse:
    """Complete feedback response for a question attempt."""

    question_id: str
    student_id: str
    is_correct: bool

    # Explanation fields
    explanation_vn: str  # Vietnamese explanation
    explanation_en: str  # English explanation
    grammar_rule: str  # The grammar rule that applies

    # Learning reinforcement
    quick_recap_examples: List[Dict[str, str]]  # 2-3 mini examples

    # Optional fields
    why_wrong: Optional[str] = None  # Why the wrong answer is incorrect
    alternative_explanation: Optional[str] = None
    memory_hook: Optional[str] = None  # Mnemonic or memory trick

    # Root cause analysis (if incorrect)
    root_cause: Optional[RootCauseAnalysis] = None

    # Personalized recommendations
    recommended_practice: Optional[List[str]] = None
    follow_up_concepts: Optional[List[str]] = None

    # Metadata
    response_time_seconds: float = 0.0
    confidence_score: float = 0.0  # AI's confidence in this feedback


# =====================================================
# ROOT CAUSE ANALYZER
# =====================================================

class RootCauseAnalyzer:
    """
    Analyzes why a student got a question wrong.
    Uses Student Knowledge Graph to identify patterns.
    """

    def __init__(self, db_connection: str):
        """Initialize database connection."""
        self.conn = psycopg2.connect(db_connection)
        register_vector(self.conn)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def analyze_incorrect_answer(
        self,
        student_id: str,
        question_id: str,
        concept_id: str,
        selected_answer: str,
        correct_answer: str
    ) -> RootCauseAnalysis:
        """
        Analyze why the student got this question wrong.

        Returns:
            RootCauseAnalysis with diagnosis
        """
        # Get concept details
        self.cursor.execute("""
            SELECT concept_name, topic_type, description, grammar_rule
            FROM concepts
            WHERE concept_id = %s
        """, (concept_id,))

        concept = self.cursor.fetchone()

        # Get student's history with this concept
        self.cursor.execute("""
            SELECT
                mastery_level,
                incorrect_attempts,
                streak_incorrect,
                last_attempt_at
            FROM student_knowledge_graph
            WHERE student_id = %s AND concept_id = %s
        """, (student_id, concept_id))

        history = self.cursor.fetchone()

        # Analyze the mistake pattern
        if history and history['incorrect_attempts'] > 2:
            # Recurring mistake - deeper issue
            root_cause = self._identify_recurring_mistake(
                concept, history, selected_answer, correct_answer
            )
            priority = 0.9  # High priority
        elif history and history['streak_incorrect'] > 0:
            # Recent mistake - needs immediate attention
            root_cause = self._identify_recent_mistake(
                concept, history, selected_answer, correct_answer
            )
            priority = 0.7
        else:
            # First-time mistake - might be careless
            root_cause = self._identify_first_time_mistake(
                concept, selected_answer, correct_answer
            )
            priority = 0.5

        # Get related concepts for learning support
        related = self._get_related_concepts(concept_id)

        return RootCauseAnalysis(
            concept_id=concept_id,
            concept_name=concept['concept_name'],
            root_cause=root_cause,
            misconception_pattern=self._extract_misconception(
                concept, selected_answer, correct_answer
            ),
            related_concepts=related,
            priority_score=priority
        )

    def _identify_recurring_mistake(
        self, concept: Dict, history: Dict,
        selected_answer: str, correct_answer: str
    ) -> str:
        """Identify why a student keeps making this mistake."""
        return (
            f"Recurring difficulty with {concept['concept_name']}. "
            f"You've gotten this wrong {history['incorrect_attempts']} times. "
            f"This suggests a gap in understanding the underlying rule. "
            f"Let's rebuild this from the basics."
        )

    def _identify_recent_mistake(
        self, concept: Dict, history: Dict,
        selected_answer: str, correct_answer: str
    ) -> str:
        """Identify why a recent mistake occurred."""
        return (
            f"Recent struggle with {concept['concept_name']}. "
            f"You're on a {history['streak_incorrect']}-question streak with this. "
            f"This usually happens when you're close to mastering it but keep "
            f"making the same small error. Let's fix that pattern."
        )

    def _identify_first_time_mistake(
        self, concept: Dict,
        selected_answer: str, correct_answer: str
    ) -> str:
        """Identify why a first-time mistake occurred."""
        return (
            f"First encounter with {concept['concept_name']} in a while. "
            f"This might be a review concept you haven't practiced recently. "
            f"Let's refresh your memory."
        )

    def _extract_misconception(
        self, concept: Dict,
        selected_answer: str, correct_answer: str
    ) -> str:
        """Extract the specific misconception pattern."""
        return (
            f"Selected {selected_answer} instead of {correct_answer} "
            f"in {concept['topic_type']}. This indicates confusion about "
            f"when to apply this specific rule."
        )

    def _get_related_concepts(self, concept_id: str) -> List[str]:
        """Get related concepts that might help."""
        self.cursor.execute("""
            SELECT related_concepts
            FROM concepts
            WHERE concept_id = %s
        """, (concept_id,))

        result = self.cursor.fetchone()
        if result and result['related_concepts']:
            # Fetch the names of related concepts
            related_ids = result['related_concepts']
            if related_ids:
                self.cursor.execute("""
                    SELECT concept_name
                    FROM concepts
                    WHERE concept_id = ANY(%s)
                    LIMIT 5
                """, (related_ids,))
                return [r['concept_name'] for r in self.cursor.fetchall()]

        return []

    def close(self):
        """Close database connection."""
        self.conn.close()


# =====================================================
# FEEDBACK AGENT (The Virtual Tutor)
# =====================================================

class FeedbackAgent:
    """
    The Virtual Tutor - provides empathetic, educational feedback.

    For each incorrect answer:
    1. Explains WHY it's wrong
    2. Provides the Grammar Rule
    3. Gives 2-3 mini-examples for reinforcement
    4. Analyzes root cause
    5. Recommends next steps
    """

    def __init__(self, db_connection: str):
        """Initialize the feedback agent."""
        self.config = get_config()
        # Use STEP_API_KEY if available, otherwise fall back to ANTHROPIC_API_KEY
        api_key = self.config.llm.get_api_key()
        if not api_key:
            raise ValueError("No API key found. Please set STEP_API_KEY or ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=api_key)
        self.analyzer = RootCauseAnalyzer(db_connection)

        # Database connection for question data
        self.conn = psycopg2.connect(db_connection)
        register_vector(self.conn)
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def generate_feedback(
        self,
        student_id: str,
        question_id: str,
        selected_answer: str,
        time_spent_seconds: int = 0
    ) -> FeedbackResponse:
        """
        Generate comprehensive feedback for a question attempt.

        Args:
            student_id: Student's unique ID
            question_id: The question that was attempted
            selected_answer: The answer the student chose
            time_spent_seconds: How long the student took

        Returns:
            FeedbackResponse with complete educational feedback
        """
        start_time = datetime.now()

        # Get question details
        self.cursor.execute("""
            SELECT
                qb.question_id,
                qb.question_text,
                qb.options,
                qb.correct_answer,
                qb.explanation,
                qb.difficulty_level,
                c.concept_id,
                c.concept_name,
                c.topic_type,
                c.grammar_rule
            FROM question_bank qb
            JOIN concepts c ON qb.concept_id = c.concept_id
            WHERE qb.question_id = %s
        """, (question_id,))

        question = self.cursor.fetchone()

        if not question:
            raise ValueError(f"Question {question_id} not found")

        is_correct = selected_answer.upper() == question['correct_answer'].upper()

        if is_correct:
            # Correct answer - positive reinforcement
            feedback = self._generate_correct_feedback(question, time_spent_seconds)
        else:
            # Incorrect answer - deep learning feedback
            feedback = self._generate_incorrect_feedback(
                student_id, question, selected_answer, time_spent_seconds
            )

        # Calculate response time
        response_time = (datetime.now() - start_time).total_seconds()
        feedback.response_time_seconds = response_time

        return feedback

    def _generate_correct_feedback(
        self, question: Dict, time_spent_seconds: int
    ) -> FeedbackResponse:
        """Generate feedback for a correct answer."""

        # Use AI to generate encouraging, educational feedback
        prompt = f"""Generate encouraging feedback for a correct answer.

Question: {question['question_text']}
Correct Answer: {question['correct_answer']}
Concept: {question['concept_name']}
Grammar Rule: {question['grammar_rule']}

The student got this RIGHT! Provide feedback that:
1. Congratulates them warmly
2. Briefly reinforces why this is correct
3. Gives ONE quick tip or insight about this rule
4. Is encouraging and motivating

Return JSON with:
{{
    "explanation_vn": "Vietnamese explanation",
    "explanation_en": "English explanation",
    "quick_tip": "A quick insight about this rule",
    "memory_hook": "A mnemonic or memory trick"
}}

Keep it short and positive. Return ONLY JSON."""

        try:
            message = self.client.messages.create(
                model=self.config.llm.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_data = json.loads(message.content[0].text)

            return FeedbackResponse(
                question_id=question['question_id'],
                student_id="",  # Will be filled by caller
                is_correct=True,
                explanation_vn=response_data.get('explanation_vn', ''),
                explanation_en=response_data.get('explanation_en', ''),
                grammar_rule=question['grammar_rule'],
                quick_recap_examples=[],
                memory_hook=response_data.get('memory_hook'),
                confidence_score=0.95
            )

        except Exception as e:
            # Fallback if AI fails
            return FeedbackResponse(
                question_id=question['question_id'],
                student_id="",
                is_correct=True,
                explanation_vn="Chính xác! Bạn đã làm tốt.",
                explanation_en=f"Correct! You applied {question['concept_name']} correctly.",
                grammar_rule=question['grammar_rule'],
                quick_recap_examples=[],
                confidence_score=0.8
            )

    def _generate_incorrect_feedback(
        self, student_id: str, question: Dict,
        selected_answer: str, time_spent_seconds: int
    ) -> FeedbackResponse:
        """Generate deep learning feedback for an incorrect answer."""

        # Analyze root cause
        root_cause = self.analyzer.analyze_incorrect_answer(
            student_id, question['question_id'], question['concept_id'],
            selected_answer, question['correct_answer']
        )

        # Generate comprehensive feedback using AI
        prompt = f"""Generate empathetic, educational feedback for an INCORRECT answer.

Question: {question['question_text']}
Student's Answer: {selected_answer}
Correct Answer: {question['correct_answer']}
Concept: {question['concept_name']}
Topic: {question['topic_type']}
Grammar Rule: {question['grammar_rule']}
Root Cause: {root_cause.root_cause}
Misconception: {root_cause.misconception_pattern}

Provide feedback that:
1. Is empathetic and non-judgmental (learning is a process!)
2. Explains WHY their answer is incorrect in simple terms
3. States the grammar rule clearly
4. Gives 2-3 quick mini-examples to reinforce understanding
5. Provides a memory hook or mnemonic to remember this rule
6. Suggests what to practice next

Return JSON with:
{{
    "explanation_vn": "Vietnamese explanation (warm, encouraging)",
    "explanation_en": "English explanation",
    "why_wrong": "Why their specific answer choice is incorrect",
    "grammar_rule": "The rule explained simply",
    "quick_recap_examples": [
        {{"example": "example 1", "explanation": "why this follows the rule"}},
        {{"example": "example 2", "explanation": "why this follows the rule"}}
    ],
    "memory_hook": "A mnemonic or memory trick",
    "recommended_practice": ["suggestion 1", "suggestion 2"]
}}

Be specific, educational, and encouraging. Return ONLY JSON."""

        try:
            message = self.client.messages.create(
                model=self.config.llm.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_data = json.loads(message.content[0].text)

            return FeedbackResponse(
                question_id=question['question_id'],
                student_id=student_id,
                is_correct=False,
                explanation_vn=response_data.get('explanation_vn', ''),
                explanation_en=response_data.get('explanation_en', ''),
                grammar_rule=response_data.get('grammar_rule', question['grammar_rule']),
                why_wrong=response_data.get('why_wrong'),
                quick_recap_examples=response_data.get('quick_recap_examples', []),
                memory_hook=response_data.get('memory_hook'),
                root_cause=root_cause,
                recommended_practice=response_data.get('recommended_practice', []),
                follow_up_concepts=root_cause.related_concepts,
                confidence_score=0.90
            )

        except Exception as e:
            print(f"Error generating AI feedback: {e}")
            # Fallback feedback
            return FeedbackResponse(
                question_id=question['question_id'],
                student_id=student_id,
                is_correct=False,
                explanation_vn=f"Chưa chính xác. Đáp án đúng là {question['correct_answer']}.",
                explanation_en=f"Not quite. The correct answer is {question['correct_answer']}.",
                grammar_rule=question['grammar_rule'],
                why_wrong=f"You selected {selected_answer}, but the correct answer is {question['correct_answer']}.",
                quick_recap_examples=[
                    {
                        "example": f"The correct form uses {question['concept_name']}",
                        "explanation": f"Apply the rule: {question['grammar_rule']}"
                    }
                ],
                root_cause=root_cause,
                confidence_score=0.7
            )

    def close(self):
        """Close database connections."""
        self.conn.close()
        self.analyzer.close()


# =====================================================
# FEEDBACK SERVICE (Public API)
# =====================================================

class FeedbackService:
    """
    High-level service for generating feedback.
    Integrates with DailyTestGenerator.
    """

    def __init__(self, db_connection: str = None):
        """Initialize the service."""
        config = get_config()
        self.db_connection = db_connection or config.db.url
        self.agent = FeedbackAgent(self.db_connection)

    def get_feedback_for_attempt(
        self,
        student_id: str,
        question_id: str,
        selected_answer: str,
        time_spent_seconds: int = 0
    ) -> Dict[str, Any]:
        """
        Get feedback for a question attempt.

        Args:
            student_id: Student's unique ID
            question_id: The question attempted
            selected_answer: The answer the student chose
            time_spent_seconds: How long they took

        Returns:
            Dictionary with feedback data
        """
        feedback = self.agent.generate_feedback(
            student_id, question_id, selected_answer, time_spent_seconds
        )

        return asdict(feedback)

    def batch_feedback(
        self,
        student_id: str,
        attempts: List[Dict[str, Any]]
    ) -> List[FeedbackResponse]:
        """
        Generate feedback for multiple attempts at once.

        Args:
            student_id: Student's unique ID
            attempts: List of attempt dictionaries with:
                - question_id
                - selected_answer
                - time_spent_seconds

        Returns:
            List of FeedbackResponse objects
        """
        feedbacks = []

        for attempt in attempts:
            feedback = self.agent.generate_feedback(
                student_id,
                attempt['question_id'],
                attempt['selected_answer'],
                attempt.get('time_spent_seconds', 0)
            )
            feedbacks.append(feedback)

        return feedbacks

    def close(self):
        """Close the service."""
        self.agent.close()


# =====================================================
# EXAMPLE USAGE
# =====================================================

def main():
    """Example usage of the Feedback Engine."""

    from app.config import get_config

    config = get_config()

    # Initialize service
    service = FeedbackService(config.db.url)

    # Example: Student answers a question incorrectly
    student_id = "student_001"
    question_id = "synthetic_reported_speech_20250122_123000"
    selected_answer = "A"  # Wrong answer
    time_spent = 45  # seconds

    # Generate feedback
    print("Generating feedback...")
    feedback = service.get_feedback_for_attempt(
        student_id, question_id, selected_answer, time_spent
    )

    print(f"\n{'='*60}")
    print(f"FEEDBACK FOR QUESTION: {feedback['question_id']}")
    print(f"{'='*60}")
    print(f"Correct: {feedback['is_correct']}")
    print(f"\nVietnamese Explanation:")
    print(f"{feedback['explanation_vn']}")
    print(f"\nEnglish Explanation:")
    print(f"{feedback['explanation_en']}")
    print(f"\nGrammar Rule:")
    print(f"{feedback['grammar_rule']}")

    if not feedback['is_correct']:
        print(f"\nWhy Your Answer Was Wrong:")
        print(f"{feedback.get('why_wrong', 'N/A')}")

        print(f"\nRoot Cause Analysis:")
        if feedback.get('root_cause'):
            rc = feedback['root_cause']
            print(f"  Concept: {rc['concept_name']}")
            print(f"  Diagnosis: {rc['root_cause']}")

        print(f"\nQuick Recap Examples:")
        for i, example in enumerate(feedback.get('quick_recap_examples', []), 1):
            print(f"  {i}. {example['example']}")
            print(f"     {example.get('explanation', '')}")

        print(f"\nMemory Hook:")
        print(f"{feedback.get('memory_hook', 'N/A')}")

        print(f"\nRecommended Practice:")
        for rec in feedback.get('recommended_practice', []):
            print(f"  - {rec}")

    print(f"\n{'='*60}\n")

    # Cleanup
    service.close()


if __name__ == '__main__':
    main()

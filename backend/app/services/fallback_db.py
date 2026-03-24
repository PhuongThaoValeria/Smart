"""
Fallback Database Service - Singleton Pattern
Uses local JSON file when PostgreSQL is unavailable
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import random


class FallbackDatabase:
    """Fallback database using local JSON file when PostgreSQL is unavailable."""

    _instance: Optional['FallbackDatabase'] = None
    _data: Optional[Dict[str, Any]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_data()
        return cls._instance

    @classmethod
    def _load_data(cls):
        """Load mock exam data from JSON file."""
        if cls._data is not None:
            return

        # Path to mock data file
        mock_file = Path(__file__).parent.parent.parent / 'data' / 'mock_exams.json'

        if not mock_file.exists():
            print(f"Warning: Mock exam file not found at {mock_file}")
            cls._data = {"questions": [], "exam_years": []}
            return

        try:
            with open(mock_file, 'r', encoding='utf-8') as f:
                cls._data = json.load(f)
            print(f"Loaded {len(cls._data.get('questions', []))} mock questions from {mock_file}")
        except Exception as e:
            print(f"Error loading mock data: {e}")
            cls._data = {"questions": [], "exam_years": []}

    @classmethod
    def get_instance(cls) -> 'FallbackDatabase':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_questions_by_concept(
        self,
        concept_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get questions for a specific concept."""
        if not self._data:
            return []

        questions = [
            q for q in self._data.get('questions', [])
            if q.get('concept_id') == concept_id
        ]
        return questions[:limit]

    def get_all_questions(self) -> List[Dict[str, Any]]:
        """Get all available questions."""
        return self._data.get('questions', []) if self._data else []

    def get_concepts(self) -> List[Dict[str, Any]]:
        """Get all available concepts."""
        if not self._data:
            return []

        concepts = []
        for exam_year in self._data.get('exam_years', []):
            concepts.extend(exam_year.get('concepts', []))
        return concepts

    def get_concept_by_name(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """Get concept information by name."""
        concepts = self.get_concepts()
        for concept in concepts:
            if concept.get('concept_name') == concept_name:
                return concept
        return None

    def get_student_learning_state(self, student_id: str) -> Dict[str, Any]:
        """Get student's learning state (mock data for guest users)."""
        # For guest users, return a default state that triggers balanced question selection
        concepts = self.get_concepts()
        weak_concepts = [
            (c.get('concept_name', ''), c.get('frequency', 5) / 10.0)
            for c in concepts[:5]
        ]

        return {
            'student_id': student_id,
            'weak_concepts': weak_concepts,
            'strong_concepts': [],
            'current_streak': 0,
            'last_test_date': None,
            'target_score': '8_plus',
            'overall_mastery': 50.0
        }

    def get_random_questions(
        self,
        count: int = 15,
        exclude_ids: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get random questions from the mock database."""
        all_questions = self.get_all_questions()
        exclude_ids = exclude_ids or []

        # Filter out excluded questions
        available = [
            q for q in all_questions
            if q.get('question_id') not in exclude_ids
        ]

        # Shuffle and return requested count
        random.shuffle(available)
        return available[:count]

    def get_questions_by_topic(
        self,
        topic_type: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """Get questions by topic type (grammar, vocabulary, etc.)."""
        all_questions = self.get_all_questions()
        questions = [
            q for q in all_questions
            if q.get('topic_type') == topic_type
        ]
        random.shuffle(questions)
        return questions[:count]

    def get_adaptive_weights(self, student_id: str) -> Dict[str, float]:
        """
        Get adaptive weights for a student.
        For guest users, returns balanced weights with slight variations.
        """
        concepts = self.get_concepts()
        weights = {}

        # Create weights based on concept frequency from exam data
        for i, concept in enumerate(concepts[:10]):
            concept_name = concept.get('concept_name')
            frequency = concept.get('frequency', 5)

            # Higher frequency = slightly higher weight for important concepts
            # But keep it balanced (0.9 to 1.3 range)
            base_weight = 0.9 + (frequency / 20.0)
            weights[concept_name] = round(base_weight, 2)

        return weights

    def get_reasoning(self, adaptive_weights: Dict[str, float]) -> str:
        """Generate reasoning for why questions were chosen."""
        if not adaptive_weights:
            return "Using 2025 High School Graduation Exam trend analysis.\nThis balanced test covers the most frequently tested concepts."

        # Sort by weight and get top concepts
        weighted_concepts = sorted(
            adaptive_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )

        reasoning_parts = ["Based on 2019-2025 exam trend analysis:"]
        for concept, weight in weighted_concepts[:5]:
            if weight >= 1.2:
                reasoning_parts.append(
                    f"• {concept}: Frequently tested ({int(weight * 100)}% priority)"
                )
            elif weight >= 1.0:
                reasoning_parts.append(
                    f"• {concept}: Regular appearance in exams"
                )
            else:
                reasoning_parts.append(
                    f"• {concept}: Review for comprehensive coverage"
                )

        reasoning_parts.append("\nThis test uses actual exam patterns from 2019-2025.")
        return "\n".join(reasoning_parts)

    def is_available(self) -> bool:
        """Check if fallback database has data."""
        return bool(self._data and self._data.get('questions'))

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the mock database."""
        if not self._data:
            return {
                'total_questions': 0,
                'total_concepts': 0,
                'years_covered': [],
                'is_available': False
            }

        questions = self._data.get('questions', [])
        concepts = self.get_concepts()
        years = list(set(q.get('year', 2025) for q in questions))

        return {
            'total_questions': len(questions),
            'total_concepts': len(concepts),
            'years_covered': sorted(years),
            'is_available': True,
            'topics': list(set(q.get('topic_type') for q in questions))
        }


# Global instance
_fallback_db: Optional[FallbackDatabase] = None


def get_fallback_db() -> FallbackDatabase:
    """Get the fallback database instance (lazy loading)."""
    global _fallback_db
    if _fallback_db is None:
        _fallback_db = FallbackDatabase.get_instance()
    return _fallback_db


def is_fallback_mode() -> bool:
    """Check if we're running in fallback mode (PostgreSQL unavailable)."""
    try:
        from psycopg2 import OperationalError
        # Try to import and check if PostgreSQL is available
        import os
        db_url = os.getenv('DATABASE_URL', '')
        if not db_url or 'localhost' in db_url:
            # In development, check if we can connect
            try:
                import psycopg2
                conn = psycopg2.connect(db_url, connect_timeout=2)
                conn.close()
                return False
            except:
                return True
        return False
    except:
        return True

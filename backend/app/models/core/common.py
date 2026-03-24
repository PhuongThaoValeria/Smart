"""
Core Enums and Shared Data Structures
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


# =====================================================
# ENUMS
# =====================================================

class TargetScoreLevel(str, Enum):
    """Target score levels for exam preparation."""
    SIX_FIVE_PLUS = "6.5_plus"
    EIGHT_PLUS = "8_plus"
    EIGHT_FIVE_PLUS = "8.5_plus"
    NINE_PLUS = "9_plus"


class TopicType(str, Enum):
    """English exam topic categories."""
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    READING_COMPREHENSION = "reading_comprehension"
    PHONETICS = "phonetics"


class DifficultyLevel(str, Enum):
    """Difficulty levels for questions."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class QuestionType(str, Enum):
    """Types of questions."""
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    SENTENCE_CORRECTION = "sentence_correction"
    READING_PASSAGE = "reading_passage"


class TestStatus(str, Enum):
    """Status of tests."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class AttemptStatus(str, Enum):
    """Status of question attempts."""
    CORRECT = "correct"
    INCORRECT = "incorrect"
    SKIPPED = "skipped"


# =====================================================
# BASE MODELS
# =====================================================

class TimestampedModel:
    """Mixin for models with timestamps."""
    created_at: datetime
    updated_at: Optional[datetime] = None


class ErrorResponse:
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = None

    def __init__(self, error: str, detail: str = None, timestamp: datetime = None):
        self.error = error
        self.detail = detail
        self.timestamp = timestamp or datetime.now()


# =====================================================
# TYPE ALIASES
# =====================================================

# Topic weights mapping
ConceptWeights = Dict[str, float]  # concept_name -> weight

# Score mapping
TopicScores = Dict[str, float]  # topic -> score

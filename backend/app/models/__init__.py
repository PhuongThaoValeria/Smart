"""
Models Package
Organized Pydantic models for API, database, and core data structures
"""

from app.models.core.common import (
    TargetScoreLevel,
    TopicType,
    DifficultyLevel,
    QuestionType,
    TestStatus,
    AttemptStatus,
)

from app.models.db.exam import (
    ExamQuestion,
    ConceptPattern,
    TrendReport,
    GeneratedQuestion,
)

from app.models.db.student import (
    StudentLearningState,
    UniversityBenchmark,
    UniversityRecommendation,
    RecoveryPlan,
)

from app.models.db.learning import (
    RootCauseAnalysis,
    FeedbackResponse,
    DailyTest,
    CompetencyScore,
    CompetencyMap,
    MegaTest,
)

__all__ = [
    # Enums
    "TargetScoreLevel",
    "TopicType",
    "DifficultyLevel",
    "QuestionType",
    "TestStatus",
    "AttemptStatus",
    # Database Models
    "ExamQuestion",
    "ConceptPattern",
    "TrendReport",
    "GeneratedQuestion",
    "StudentLearningState",
    "UniversityBenchmark",
    "UniversityRecommendation",
    "RecoveryPlan",
    "RootCauseAnalysis",
    "FeedbackResponse",
    "DailyTest",
    "CompetencyScore",
    "CompetencyMap",
    "MegaTest",
]

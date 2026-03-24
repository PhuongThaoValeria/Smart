"""
Smart English Test-Prep Agent - RAG Engine
Phase 1: Knowledge Base & Trend Analysis (RAG Engine)

This module handles:
1. Ingestion and parsing of PDF/Text exam data from 2019-2025
2. Analysis of topic distribution (Grammar, Vocabulary, Reading Comprehension, Phonetics)
3. Difficulty level classification for target scores (6.5+, 8+, 9+)
4. Generation of structured Trend Report
5. Vector embedding storage for semantic similarity
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np
from dataclasses import dataclass, asdict

import PyPDF2
import pandas as pd
from sentence_transformers import SentenceTransformer
from anthropic import Anthropic

# Database imports
import psycopg2
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector


# =====================================================
# DATA MODELS
# =====================================================

@dataclass
class ExamQuestion:
    """Represents a single exam question."""
    question_id: str
    question_text: str
    topic_type: str  # 'grammar', 'vocabulary', 'reading_comprehension', 'phonetics'
    question_type: str  # 'multiple_choice', 'fill_blank', 'sentence_correction', 'reading_passage'
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    difficulty_level: str = 'intermediate'  # 'basic', 'intermediate', 'advanced', 'expert'
    target_score_level: str = '8_plus'  # '6.5_plus', '8_plus', '9_plus'
    year: int = 2024


@dataclass
class ConceptPattern:
    """Represents patterns observed for a specific concept."""
    concept_name: str
    topic_type: str
    frequency: int
    difficulty_distribution: Dict[str, int]  # {'basic': 5, 'intermediate': 3, ...}
    target_score_relevance: Dict[str, float]  # {'6.5_plus': 0.3, '8_plus': 0.5, ...}
    example_patterns: List[str]
    grammar_rule: Optional[str] = None
    common_mistakes: List[str] = None


@dataclass
class TrendReport:
    """Comprehensive trend analysis report."""
    year: int
    total_questions: int
    topic_distribution: Dict[str, int]  # {'grammar': 20, 'vocabulary': 15, ...}
    concept_patterns: List[ConceptPattern]
    difficulty_analysis: Dict[str, Any]
    target_score_guidance: Dict[str, List[str]]
    synthetic_generation_seed: Dict[str, Any]
    generated_at: str


# =====================================================
# PDF PARSER
# =====================================================

class ExamPDFParser:
    """Parses Vietnamese high school English exam PDFs."""

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract raw text from PDF file."""
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    def parse_questions(self, text: str, year: int) -> List[ExamQuestion]:
        """
        Parse exam questions from extracted text using Claude for intelligent parsing.
        """
        prompt = f"""You are an expert at parsing Vietnamese high school English exams.

Parse the following exam text and extract all questions. Return a JSON array where each question has:
- question_number: integer
- question_text: the full question text
- topic_type: one of ['grammar', 'vocabulary', 'reading_comprehension', 'phonetics']
- question_type: one of ['multiple_choice', 'fill_blank', 'sentence_correction', 'reading_passage']
- options: array of 4 strings ["A) option1", "B) option2", "C) option3", "D) option4"]
- correct_answer: single letter "A", "B", "C", or "D"
- difficulty_level: one of ['basic', 'intermediate', 'advanced', 'expert']
- target_score_level: one of ['6.5_plus', '8_plus', '9_plus'] (which score level would need to know this)

Exam text:
{text[:8000]}  # Limit to avoid token limits

Return ONLY the JSON array, no other text."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            questions_data = json.loads(message.content[0].text)
            questions = []

            for q_data in questions_data:
                question = ExamQuestion(
                    question_id=f"{year}_q{q_data['question_number']}",
                    question_text=q_data['question_text'],
                    topic_type=q_data['topic_type'],
                    question_type=q_data['question_type'],
                    options=q_data['options'],
                    correct_answer=q_data['correct_answer'],
                    difficulty_level=q_data.get('difficulty_level', 'intermediate'),
                    target_score_level=q_data.get('target_score_level', '8_plus'),
                    year=year
                )
                questions.append(question)

            return questions

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing Claude response: {e}")
            return []

    def process_exam_pdf(self, pdf_path: str, year: int) -> List[ExamQuestion]:
        """Process a single exam PDF file."""
        print(f"Processing {pdf_path} for year {year}...")

        # Extract text
        text = self.extract_text_from_pdf(pdf_path)

        # Parse questions
        questions = self.parse_questions(text, year)

        print(f"Extracted {len(questions)} questions from {pdf_path}")
        return questions


# =====================================================
# EMBEDDING GENERATOR
# =====================================================

class EmbeddingGenerator:
    """Generates vector embeddings for semantic similarity."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize the sentence transformer model."""
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        return self.model.encode(text, normalize_embeddings=True)

    def generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts."""
        return self.model.encode(texts, normalize_embeddings=True)


# =====================================================
# TREND ANALYZER
# =====================================================

class TrendAnalyzer:
    """Analyzes exam patterns and generates trend reports."""

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    def analyze_topic_distribution(self, questions: List[ExamQuestion]) -> Dict[str, int]:
        """Analyze distribution of topics in the exam."""
        distribution = {
            'grammar': 0,
            'vocabulary': 0,
            'reading_comprehension': 0,
            'phonetics': 0
        }

        for question in questions:
            distribution[question.topic_type] += 1

        return distribution

    def analyze_difficulty_by_target_score(
        self, questions: List[ExamQuestion]
    ) -> Dict[str, Dict[str, int]]:
        """Analyze difficulty levels for each target score."""
        analysis = {
            '6.5_plus': {'basic': 0, 'intermediate': 0, 'advanced': 0, 'expert': 0},
            '8_plus': {'basic': 0, 'intermediate': 0, 'advanced': 0, 'expert': 0},
            '9_plus': {'basic': 0, 'intermediate': 0, 'advanced': 0, 'expert': 0}
        }

        for question in questions:
            score_level = question.target_score_level.replace('_', '.')
            difficulty = question.difficulty_level
            analysis[score_level][difficulty] += 1

        return analysis

    def extract_concept_patterns(self, questions: List[ExamQuestion]) -> List[ConceptPattern]:
        """
        Extract concept patterns using AI analysis.
        Groups similar questions and identifies patterns.
        """
        # Group questions by topic
        by_topic = {}
        for q in questions:
            if q.topic_type not in by_topic:
                by_topic[q.topic_type] = []
            by_topic[q.topic_type].append(q)

        patterns = []

        # Use Claude to identify patterns within each topic
        for topic, topic_questions in by_topic.items():
            prompt = f"""Analyze these {topic} questions from a Vietnamese high school English exam.

Identify the main grammatical concepts or vocabulary themes. For each concept:
1. Name the concept (e.g., "Reported Speech", "Relative Clauses", "Phrasal Verbs")
2. Count how many questions test this concept
3. Classify difficulty distribution (how many are basic/intermediate/advanced/expert)
4. Assess relevance to target scores (6.5+, 8+, 9+) as decimal probabilities
5. Identify 2-3 common question patterns or sentence structures

Questions:
{self._format_questions_for_analysis(topic_questions[:20])}

Return as JSON array of concept objects."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            concepts_data = json.loads(message.content[0].text)

            for c_data in concepts_data:
                pattern = ConceptPattern(
                    concept_name=c_data['concept_name'],
                    topic_type=topic,
                    frequency=c_data['frequency'],
                    difficulty_distribution=c_data['difficulty_distribution'],
                    target_score_relevance=c_data['target_score_relevance'],
                    example_patterns=c_data['example_patterns'],
                    grammar_rule=c_data.get('grammar_rule'),
                    common_mistakes=c_data.get('common_mistakes', [])
                )
                patterns.append(pattern)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error extracting patterns for {topic}: {e}")

        return patterns

    def generate_target_score_guidance(
        self, questions: List[ExamQuestion]
    ) -> Dict[str, List[str]]:
        """
        Generate guidance on what concepts to focus on for each target score.
        """
        prompt = f"""Based on these exam questions, provide specific guidance for students targeting different scores.

For each target score level (6.5+, 8+, 9+):
- List 3-5 key concepts they MUST master
- List 2-3 concepts they can SKIP or deprioritize
- Provide a specific study strategy

Sample questions:
{self._format_questions_for_analysis(questions[:30])}

Return as JSON with keys: "6.5_plus", "8_plus", "9_plus"."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            guidance = json.loads(message.content[0].text)
            return guidance

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error generating guidance: {e}")
            return {}

    def create_synthetic_generation_seed(
        self, patterns: List[ConceptPattern], distribution: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Create seed data for synthetic question generation.
        This ensures new questions follow exam patterns.
        """
        seed = {
            'topic_weights': {
                topic: count / sum(distribution.values())
                for topic, count in distribution.items()
            },
            'concept_templates': [],
            'difficulty_ratios': {},
            'sentence_patterns': []
        }

        for pattern in patterns:
            seed['concept_templates'].append({
                'concept': pattern.concept_name,
                'topic': pattern.topic_type,
                'frequency': pattern.frequency,
                'target_relevance': pattern.target_score_relevance,
                'example_patterns': pattern.example_patterns,
                'grammar_rule': pattern.grammar_rule
            })

        return seed

    def _format_questions_for_analysis(self, questions: List[ExamQuestion]) -> str:
        """Format questions for AI analysis."""
        formatted = []
        for i, q in enumerate(questions, 1):
            formatted.append(
                f"Q{i}: {q.question_text}\n"
                f"Topic: {q.topic_type} | Difficulty: {q.difficulty_level} | "
                f"Target: {q.target_score_level} | Answer: {q.correct_answer}"
            )
        return "\n\n".join(formatted)


# =====================================================
# DATABASE MANAGER
# =====================================================

class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, connection_string: str):
        """Initialize database connection."""
        self.conn = psycopg2.connect(connection_string)
        register_vector(self.conn)
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def store_exam_year(self, year: int, exam_code: str = None) -> str:
        """Store exam year metadata."""
        exam_id = f"exam_{year}"

        self.cursor.execute("""
            INSERT INTO exam_years (exam_year_id, year, exam_code, total_questions, duration_minutes)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (year) DO UPDATE SET exam_code = EXCLUDED.exam_code
            RETURNING exam_year_id
        """, (exam_id, year, exam_code, 50, 60))

        return self.cursor.fetchone()[0]

    def store_concept(
        self, concept_name: str, topic_type: str, description: str,
        grammar_rule: str = None, embedding: np.ndarray = None
    ) -> str:
        """Store a concept with its embedding."""
        concept_id = f"concept_{concept_name.lower().replace(' ', '_')}"

        self.cursor.execute("""
            INSERT INTO concepts (concept_id, concept_name, topic_type, description, grammar_rule, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (concept_name) DO UPDATE SET
                description = EXCLUDED.description,
                grammar_rule = EXCLUDED.grammar_rule,
                embedding = EXCLUDED.embedding
            RETURNING concept_id
        """, (concept_id, concept_name, topic_type, description, grammar_rule, embedding))

        self.conn.commit()
        return concept_id

    def store_question(
        self, question: ExamQuestion, concept_id: str, exam_year_id: str,
        embedding: np.ndarray
    ) -> str:
        """Store a question in the question bank."""
        self.cursor.execute("""
            INSERT INTO question_bank (
                question_id, concept_id, exam_year_id, question_text, question_type,
                options, correct_answer, difficulty_level, target_score_level, embedding
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING question_id
        """, (
            question.question_id, concept_id, exam_year_id,
            question.question_text, question.question_type,
            json.dumps(question.options), question.correct_answer,
            question.difficulty_level, question.target_score_level, embedding
        ))

        return self.cursor.fetchone()[0]

    def store_trend_matrix(
        self, exam_year_id: str, concept_id: str, topic_type: str,
        pattern: ConceptPattern, embedding: np.ndarray = None
    ):
        """Store trend analysis data."""
        self.cursor.execute("""
            INSERT INTO exam_trend_matrix (
                exam_year_id, concept_id, topic_type, question_count,
                difficulty_distribution, target_score_relevance,
                question_patterns, embedding
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (exam_year_id, concept_id) DO UPDATE SET
                question_count = EXCLUDED.question_count,
                difficulty_distribution = EXCLUDED.difficulty_distribution,
                target_score_relevance = EXCLUDED.target_score_relevance,
                question_patterns = EXCLUDED.question_patterns
        """, (
            exam_year_id, concept_id, topic_type, pattern.frequency,
            json.dumps(pattern.difficulty_distribution),
            json.dumps(pattern.target_score_relevance),
            json.dumps(pattern.example_patterns), embedding
        ))

        self.conn.commit()

    def commit(self):
        """Commit transactions."""
        self.conn.commit()

    def rollback(self):
        """Rollback transactions."""
        self.conn.rollback()


# =====================================================
# MAIN RAG ENGINE ORCHESTRATOR
# =====================================================

class RAGEngine:
    """Main orchestrator for the RAG-based exam analysis system."""

    def __init__(self, db_connection_string: str):
        """Initialize all components."""
        self.parser = ExamPDFParser()
        self.embedding_generator = EmbeddingGenerator()
        self.trend_analyzer = TrendAnalyzer()

        self.db = DatabaseManager(db_connection_string)

    def ingest_exam_data(
        self, pdf_paths: List[Tuple[str, int]]
    ) -> List[TrendReport]:
        """
        Ingest exam data from multiple PDF files.

        Args:
            pdf_paths: List of tuples (pdf_path, year)

        Returns:
            List of TrendReport objects
        """
        all_reports = []

        for pdf_path, year in pdf_paths:
            print(f"\n{'='*60}")
            print(f"Processing Year {year}")
            print(f"{'='*60}")

            # Parse questions from PDF
            questions = self.parser.process_exam_pdf(pdf_path, year)

            if not questions:
                print(f"No questions extracted from {pdf_path}")
                continue

            # Store exam year
            exam_year_id = self.db.store_exam_year(year)

            # Generate embeddings for all questions
            question_texts = [q.question_text for q in questions]
            embeddings = self.embedding_generator.generate_embeddings_batch(question_texts)

            # Analyze trends
            topic_distribution = self.trend_analyzer.analyze_topic_distribution(questions)
            concept_patterns = self.trend_analyzer.extract_concept_patterns(questions)
            target_guidance = self.trend_analyzer.generate_target_score_guidance(questions)
            synthetic_seed = self.trend_analyzer.create_synthetic_generation_seed(
                concept_patterns, topic_distribution
            )

            # Store concepts and questions
            concept_map = {}
            for pattern in concept_patterns:
                # Generate embedding for concept description
                concept_desc = f"{pattern.concept_name}: {pattern.topic_type}"
                concept_emb = self.embedding_generator.generate_embedding(concept_desc)

                concept_id = self.db.store_concept(
                    concept_name=pattern.concept_name,
                    topic_type=pattern.topic_type,
                    description=f"English concept: {pattern.concept_name}",
                    grammar_rule=pattern.grammar_rule,
                    embedding=concept_emb
                )
                concept_map[pattern.concept_name] = concept_id

            # Store questions
            for question, embedding in zip(questions, embeddings):
                # Find matching concept (simplified - would use semantic search in production)
                concept_id = list(concept_map.values())[0]  # Default to first concept

                self.db.store_question(
                    question=question,
                    concept_id=concept_id,
                    exam_year_id=exam_year_id,
                    embedding=embedding
                )

            # Store trend matrix
            for pattern in concept_patterns:
                concept_id = concept_map.get(pattern.concept_name)
                if concept_id:
                    trend_emb = self.embedding_generator.generate_embedding(
                        f"{pattern.concept_name} {pattern.topic_type} exam pattern"
                    )
                    self.db.store_trend_matrix(
                        exam_year_id=exam_year_id,
                        concept_id=concept_id,
                        topic_type=pattern.topic_type,
                        pattern=pattern,
                        embedding=trend_emb
                    )

            # Create trend report
            report = TrendReport(
                year=year,
                total_questions=len(questions),
                topic_distribution=topic_distribution,
                concept_patterns=concept_patterns,
                difficulty_analysis=self.trend_analyzer.analyze_difficulty_by_target_score(questions),
                target_score_guidance=target_guidance,
                synthetic_generation_seed=synthetic_seed,
                generated_at=datetime.now().isoformat()
            )

            all_reports.append(report)

            self.db.commit()
            print(f"\n✓ Completed processing for year {year}")
            print(f"  - Questions: {len(questions)}")
            print(f"  - Concepts identified: {len(concept_patterns)}")
            print(f"  - Topic distribution: {topic_distribution}")

        return all_reports

    def generate_comprehensive_report(self, reports: List[TrendReport]) -> str:
        """Generate a comprehensive trend report across all years."""
        summary = {
            'years_analyzed': [r.year for r in reports],
            'total_questions': sum(r.total_questions for r in reports),
            'overall_topic_distribution': {},
            'key_insights': [],
            'recommendations': {}
        }

        # Aggregate topic distributions
        for topic in ['grammar', 'vocabulary', 'reading_comprehension', 'phonetics']:
            summary['overall_topic_distribution'][topic] = sum(
                r.topic_distribution.get(topic, 0) for r in reports
            )

        # Generate insights
        summary['key_insights'] = [
            f"Analyzed {len(reports)} years of exam data",
            f"Total questions processed: {summary['total_questions']}",
            f"Most common topic: {max(summary['overall_topic_distribution'], key=summary['overall_topic_distribution'].get)}"
        ]

        return json.dumps(summary, indent=2)


# =====================================================
# EXAMPLE USAGE
# =====================================================

def main():
    """Example usage of the RAG Engine."""

    # Configuration
    DB_CONNECTION = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5432/english_testprep'
    )

    # PDF files to process (path, year)
    PDF_FILES = [
        ('./data/exams/2024_exam.pdf', 2024),
        ('./data/exams/2023_exam.pdf', 2023),
        # Add more years...
    ]

    # Initialize RAG Engine
    rag_engine = RAGEngine(DB_CONNECTION)

    # Ingest exam data
    print("Starting exam data ingestion...")
    trend_reports = rag_engine.ingest_exam_data(PDF_FILES)

    # Generate comprehensive report
    comprehensive_report = rag_engine.generate_comprehensive_report(trend_reports)

    # Save reports
    output_dir = Path('./output/trend_reports')
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / 'comprehensive_report.json', 'w') as f:
        f.write(comprehensive_report)

    for report in trend_reports:
        report_file = output_dir / f'trend_report_{report.year}.json'
        with open(report_file, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)

    print(f"\n✓ Analysis complete!")
    print(f"  - Processed {len(trend_reports)} years")
    print(f"  - Reports saved to {output_dir}")


if __name__ == '__main__':
    main()

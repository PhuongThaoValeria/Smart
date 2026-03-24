-- =====================================================
-- Smart English Test-Prep Agent Database Schema
-- Target: Vietnamese High School Students (THPT)
-- PostgreSQL with PGVector Extension
-- =====================================================

-- Enable PGVector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================
-- DOMAIN: Enumerations
-- =====================================================

CREATE TYPE target_score_level AS ENUM ('6.5_plus', '8_plus', '9_plus');
CREATE TYPE topic_type AS ENUM ('grammar', 'vocabulary', 'reading_comprehension', 'phonetics');
CREATE TYPE difficulty_level AS ENUM ('basic', 'intermediate', 'advanced', 'expert');
CREATE TYPE question_type AS ENUM ('multiple_choice', 'fill_blank', 'sentence_correction', 'reading_passage');
CREATE TYPE attempt_status AS ENUM ('correct', 'incorrect', 'skipped');
CREATE TYPE test_frequency AS ENUM ('daily', 'bi_weekly', 'custom');

-- =====================================================
-- CORE: Students & Authentication
-- =====================================================

CREATE TABLE students (
    student_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    current_grade INTEGER CHECK (current_grade BETWEEN 10 AND 12),
    target_score target_score_level NOT NULL DEFAULT '8_plus',
    exam_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    total_questions_attempted INTEGER DEFAULT 0,
    overall_accuracy DECIMAL(5,2) DEFAULT 0.00
);

-- =====================================================
-- KNOWLEDGE: Concepts & Grammar Rules
-- =====================================================

CREATE TABLE concepts (
    concept_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_name VARCHAR(255) UNIQUE NOT NULL,
    topic_type topic_type NOT NULL,
    description TEXT,
    grammar_rule TEXT,
    examples JSONB, -- Array of example sentences
    related_concepts UUID[] DEFAULT ARRAY[]::UUID[],
    embedding vector(1536), -- For semantic similarity
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- EXAM DATA: Trend Matrix (2019-2025)
-- =====================================================

CREATE TABLE exam_years (
    exam_year_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    year INTEGER UNIQUE NOT NULL CHECK (year BETWEEN 2019 AND 2025),
    exam_code VARCHAR(50) UNIQUE,
    total_questions INTEGER DEFAULT 50,
    duration_minutes INTEGER DEFAULT 60,
    exam_date DATE,
    data_source TEXT, -- PDF path or API source
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE exam_trend_matrix (
    trend_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_year_id UUID REFERENCES exam_years(exam_year_id),
    concept_id UUID REFERENCES concepts(concept_id),
    topic_type topic_type NOT NULL,
    question_count INTEGER DEFAULT 0,
    difficulty_distribution JSONB, -- {"basic": 5, "intermediate": 3, "advanced": 2}
    target_score_relevance JSONB, -- {"6.5_plus": 0.3, "8_plus": 0.5, "9_plus": 0.8}
    question_patterns JSONB, -- Common patterns observed
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exam_year_id, concept_id)
);

-- =====================================================
-- QUESTION BANK: Original & Synthetic
-- =====================================================

CREATE TABLE question_bank (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_id UUID REFERENCES concepts(concept_id),
    exam_year_id UUID REFERENCES exam_years(exam_year_id), -- NULL for synthetic questions
    question_text TEXT NOT NULL,
    question_type question_type NOT NULL,
    options JSONB, -- ["A: option1", "B: option2", "C: option3", "D: option4"]
    correct_answer VARCHAR(10) CHECK (correct_answer IN ('A', 'B', 'C', 'D')),
    explanation TEXT,
    difficulty_level difficulty_level NOT NULL,
    target_score_level target_score_level,
    is_synthetic BOOLEAN DEFAULT FALSE,
    source_year INTEGER, -- Original year if not synthetic
    embedding vector(1536), -- For similarity detection
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- STUDENT KNOWLEDGE GRAPH: Mastery Tracking
-- =====================================================

CREATE TABLE student_knowledge_graph (
    graph_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(student_id),
    concept_id UUID REFERENCES concepts(concept_id),
    mastery_level DECIMAL(5,2) DEFAULT 0.00 CHECK (mastery_level BETWEEN 0 AND 100),
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    incorrect_attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    streak_correct INTEGER DEFAULT 0,
    streak_incorrect INTEGER DEFAULT 0,
    adaptive_weight DECIMAL(5,2) DEFAULT 1.00, -- Increases by 40% after failure
    priority_score DECimal(5,2) DEFAULT 0.00, -- For concept selection
    weakness_score DECIMAL(5,2) DEFAULT 0.00, -- Higher = weaker
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, concept_id)
);

-- Index for adaptive learning queries
CREATE INDEX idx_student_knowledge_mastery ON student_knowledge_graph(student_id, weakness_score DESC, adaptive_weight DESC);
CREATE INDEX idx_student_knowledge_concept ON student_knowledge_graph(concept_id);

-- =====================================================
-- DAILY TESTS: 15-Minute Micro-Learning
-- =====================================================

CREATE TABLE daily_tests (
    test_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(student_id),
    test_date DATE NOT NULL DEFAULT CURRENT_DATE,
    test_sequence INTEGER DEFAULT 1, -- Day 1, Day 2, etc.
    total_questions INTEGER DEFAULT 15,
    duration_minutes INTEGER DEFAULT 15,
    concepts_covered UUID[] DEFAULT ARRAY[]::UUID[],
    adaptive_weights JSONB, -- {"concept_id": 1.4} for failed concepts
    time_remaining_seconds INTEGER DEFAULT 900, -- 15 minutes
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'abandoned')),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    streak_bonus_applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, test_date)
);

CREATE TABLE daily_test_questions (
    test_question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID REFERENCES daily_tests(test_id),
    question_id UUID REFERENCES question_bank(question_id),
    question_order INTEGER NOT NULL,
    is_synthetic BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(test_id, question_order)
);

CREATE TABLE daily_test_attempts (
    attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_question_id UUID REFERENCES daily_test_questions(test_question_id),
    student_id UUID REFERENCES students(student_id),
    selected_answer VARCHAR(10),
    is_correct BOOLEAN,
    time_spent_seconds INTEGER,
    attempt_status attempt_status NOT NULL,
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- MEGA TESTS: Bi-weekly Full-length Mock Exams
-- =====================================================

CREATE TABLE mega_tests (
    mega_test_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(student_id),
    test_date DATE NOT NULL DEFAULT CURRENT_DATE,
    test_sequence INTEGER DEFAULT 1, -- Mega Test 1, 2, 3, etc.
    total_questions INTEGER DEFAULT 50,
    duration_minutes INTEGER DEFAULT 60,
    concepts_covered UUID[] DEFAULT ARRAY[]::UUID[],
    time_remaining_seconds INTEGER DEFAULT 3600, -- 60 minutes
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'abandoned')),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    overall_score DECIMAL(5,2),
    percentile_rank DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mega_test_questions (
    mega_test_question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mega_test_id UUID REFERENCES mega_tests(mega_test_id),
    question_id UUID REFERENCES question_bank(question_id),
    question_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mega_test_id, question_order)
);

CREATE TABLE mega_test_attempts (
    attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mega_test_question_id UUID REFERENCES mega_test_questions(mega_test_question_id),
    student_id UUID REFERENCES students(student_id),
    selected_answer VARCHAR(10),
    is_correct BOOLEAN,
    time_spent_seconds INTEGER,
    attempt_status attempt_status NOT NULL,
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- ANALYTICS: Competency Maps & Performance
-- =====================================================

CREATE TABLE competency_maps (
    map_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(student_id),
    mega_test_id UUID REFERENCES mega_tests(mega_test_id),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Radar chart data for 4 main topics
    grammar_score DECIMAL(5,2) DEFAULT 0.00,
    vocabulary_score DECIMAL(5,2) DEFAULT 0.00,
    reading_comprehension_score DECIMAL(5,2) DEFAULT 0.00,
    phonetics_score DECIMAL(5,2) DEFAULT 0.00,
    -- Detailed breakdown
    topic_breakdown JSONB, -- Detailed scores per sub-concept
    strength_areas TEXT[] DEFAULT ARRAY[]::TEXT[],
    weakness_areas TEXT[] DEFAULT ARRAY[]::TEXT[],
    improvement_recommendations JSONB
);

-- =====================================================
-- UNIVERSITY ADMISSION DATA
-- =====================================================

CREATE TABLE universities (
    university_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_name VARCHAR(255) NOT NULL,
    university_code VARCHAR(50) UNIQUE,
    province VARCHAR(100),
    university_type VARCHAR(100), -- Public, Private, International
    ranking_national INTEGER,
    website_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE majors (
    major_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID REFERENCES universities(university_id),
    major_name VARCHAR(255) NOT NULL,
    major_code VARCHAR(50),
    required_subjects TEXT[], -- ["Math", "Literature", "English"]
    english_weight DECIMAL(5,2) DEFAULT 0.0, -- How much English counts
    duration_years INTEGER DEFAULT 4,
    tuition_fee VARCHAR(50),
    career_prospects TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admission_benchmarks (
    benchmark_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    major_id UUID REFERENCES majors(major_id),
    year INTEGER NOT NULL,
    benchmark_score DECIMAL(5,2) NOT NULL, -- Minimum score for admission
    admission_quota INTEGER,
    successful_applicants INTEGER,
    competition_ratio DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(major_id, year)
);

-- =====================================================
-- COUNSELING: Recovery Plans & Recommendations
-- =====================================================

CREATE TABLE recovery_plans (
    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(student_id),
    competency_map_id UUID REFERENCES competency_maps(map_id),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    target_exam_date DATE,
    weeks_remaining INTEGER,
    -- Plan details
    weak_concepts UUID[], -- Array of concept IDs to focus on
    study_schedule JSONB, -- Weekly breakdown
    daily_practice_recommendations JSONB,
    expected_score_improvement DECIMAL(5,2),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused'))
);

CREATE TABLE university_recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(student_id),
    recovery_plan_id UUID REFERENCES recovery_plans(plan_id),
    major_id UUID REFERENCES majors(major_id),
    predicted_score DECIMAL(5,2),
    admission_probability DECIMAL(5,2), -- > 70% threshold
    match_score DECIMAL(5,2), -- How well student matches
    gap_to_benchmark DECIMAL(5,2), -- Points needed
    recommendation_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- FEEDBACK: Real-time Explanations & Examples
-- =====================================================

CREATE TABLE feedback_explanations (
    explanation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_id UUID REFERENCES concepts(concept_id),
    question_id UUID REFERENCES question_bank(question_id),
    incorrect_answer VARCHAR(10),
    explanation_text TEXT NOT NULL,
    grammar_rule_explanation TEXT,
    mini_examples JSONB, -- 2 reinforcing examples
    alternative_approach TEXT,
    difficulty_guidance TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Vector similarity searches
CREATE INDEX idx_question_embeddings ON question_bank USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_concept_embeddings ON concepts USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_trend_embeddings ON exam_trend_matrix USING ivfflat (embedding vector_cosine_ops);

-- Common queries
CREATE INDEX idx_daily_tests_student ON daily_tests(student_id, test_date DESC);
CREATE INDEX idx_mega_tests_student ON mega_tests(student_id, test_date DESC);
CREATE INDEX idx_student_knowledge ON student_knowledge_graph(student_id, mastery_level ASC);
CREATE INDEX idx_benchmarks_year ON admission_benchmarks(year, benchmark_score);

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Student Progress Summary
CREATE OR REPLACE VIEW student_progress_summary AS
SELECT
    s.student_id,
    s.full_name,
    s.target_score,
    s.current_streak,
    COUNT(DISTINCT dt.test_id) as daily_tests_completed,
    COUNT(DISTINCT mt.mega_test_id) as mega_tests_completed,
    AVG(skg.mastery_level) as avg_mastery_level,
    s.overall_accuracy
FROM students s
LEFT JOIN daily_tests dt ON s.student_id = dt.student_id AND dt.status = 'completed'
LEFT JOIN mega_tests mt ON s.student_id = mt.student_id AND mt.status = 'completed'
LEFT JOIN student_knowledge_graph skg ON s.student_id = skg.student_id
GROUP BY s.student_id, s.full_name, s.target_score, s.current_streak, s.overall_accuracy;

-- Concept Mastery for Adaptive Learning
CREATE OR REPLACE VIEW adaptive_concept_selection AS
SELECT
    skg.student_id,
    skg.concept_id,
    c.concept_name,
    c.topic_type,
    skg.mastery_level,
    skg.weakness_score,
    skg.adaptive_weight,
    skg.priority_score,
    (skg.weakness_score * skg.adaptive_weight) as selection_score
FROM student_knowledge_graph skg
JOIN concepts c ON skg.concept_id = c.concept_id
ORDER BY selection_score DESC;

-- =====================================================
-- TRIGGERS FOR AUTO-UPDATES
-- =====================================================

-- Update student overall accuracy after each attempt
CREATE OR REPLACE FUNCTION update_student_accuracy()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE students
    SET overall_accuracy = (
        SELECT ROUND(COUNT(*) FILTER (WHERE is_correct = TRUE)::DECIMAL / COUNT(*) * 100, 2)
        FROM daily_test_attempts
        WHERE student_id = NEW.student_id
    ),
    total_questions_attempted = total_questions_attempted + 1,
    last_active_at = CURRENT_TIMESTAMP
    WHERE student_id = NEW.student_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_accuracy
AFTER INSERT ON daily_test_attempts
FOR EACH ROW
EXECUTE FUNCTION update_student_accuracy();

-- Update knowledge graph after each attempt
CREATE OR REPLACE FUNCTION update_knowledge_graph()
RETURNS TRIGGER AS $$
DECLARE
    v_concept_id UUID;
BEGIN
    -- Get concept_id from question
    SELECT c.concept_id INTO v_concept_id
    FROM question_bank qb
    JOIN concepts c ON qb.concept_id = c.concept_id
    JOIN daily_test_questions dtq ON qb.question_id = dtq.question_id
    WHERE dtq.test_question_id = NEW.test_question_id;

    -- Update or insert knowledge graph entry
    INSERT INTO student_knowledge_graph (
        student_id, concept_id, total_attempts,
        correct_attempts, incorrect_attempts, mastery_level,
        last_attempt_at, streak_correct, streak_incorrect,
        adaptive_weight, weakness_score, updated_at
    )
    VALUES (
        NEW.student_id, v_concept_id, 1,
        CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
        CASE WHEN NOT NEW.is_correct THEN 1 ELSE 0 END,
        CASE WHEN NEW.is_correct THEN 100.0 ELSE 0.0 END,
        CURRENT_TIMESTAMP,
        CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
        CASE WHEN NOT NEW.is_correct THEN 1 ELSE 0 END,
        1.0, 0.0, CURRENT_TIMESTAMP
    )
    ON CONFLICT (student_id, concept_id) DO UPDATE SET
        total_attempts = student_knowledge_graph.total_attempts + 1,
        correct_attempts = student_knowledge_graph.correct_attempts +
            CASE WHEN NEW.is_correct THEN 1 ELSE 0 END,
        incorrect_attempts = student_knowledge_graph.incorrect_attempts +
            CASE WHEN NOT NEW.is_correct THEN 1 ELSE 0 END,
        mastery_level = ROUND(
            (student_knowledge_graph.correct_attempts +
                CASE WHEN NEW.is_correct THEN 1 ELSE 0 END)::DECIMAL /
            (student_knowledge_graph.total_attempts + 1) * 100, 2
        ),
        last_attempt_at = CURRENT_TIMESTAMP,
        streak_correct = CASE
            WHEN NEW.is_correct THEN student_knowledge_graph.streak_correct + 1
            ELSE 0
        END,
        streak_incorrect = CASE
            WHEN NOT NEW.is_correct THEN student_knowledge_graph.streak_incorrect + 1
            ELSE 0
        END,
        adaptive_weight = CASE
            WHEN NOT NEW.is_correct THEN LEAST(student_knowledge_graph.adaptive_weight * 1.4, 3.0)
            ELSE GREATEST(student_knowledge_graph.adaptive_weight * 0.9, 1.0)
        END,
        weakness_score = ROUND(
            (1 - (student_knowledge_graph.correct_attempts +
                CASE WHEN NEW.is_correct THEN 1 ELSE 0 END)::DECIMAL /
            (student_knowledge_graph.total_attempts + 1)) * 100, 2
        ),
        updated_at = CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_knowledge_graph
AFTER INSERT ON daily_test_attempts
FOR EACH ROW
EXECUTE FUNCTION update_knowledge_graph();

-- =====================================================
-- SAMPLE DATA FOR TESTING
-- =====================================================

-- Insert sample concepts
INSERT INTO concepts (concept_name, topic_type, description) VALUES
('Reported Speech', 'grammar', 'Converting direct speech to indirect speech'),
('Relative Clauses', 'grammar', 'Using who, which, that, whose in relative clauses'),
('Passive Voice', 'grammar', 'Passive voice transformations'),
('Conditionals', 'grammar', 'Zero, first, second, third conditionals'),
('Phrasal Verbs', 'vocabulary', 'Common phrasal verbs and their meanings');

-- =====================================================
-- END OF SCHEMA
-- =====================================================

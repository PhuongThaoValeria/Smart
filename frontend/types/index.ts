// Types matching Backend Pydantic models

export interface Student {
  id: string;
  email: string;
  full_name: string;
  target_score: number;
  target_score_level: 'basic' | 'competent' | 'advanced' | 'excellent';
  exam_date: string;
  created_at: string;
}

export interface ConceptPattern {
  concept: string;
  topic: 'grammar' | 'vocabulary' | 'reading' | 'phonetics';
  difficulty: 'basic' | 'intermediate' | 'advanced';
  patterns: string[];
  grammar_rule: string;
  exam_frequency: number;
}

export interface ExamQuestion {
  question_id: string;
  concept_name: string;
  topic_type: 'grammar' | 'vocabulary' | 'reading_comprehension' | 'phonetics';
  difficulty: 'basic' | 'intermediate' | 'advanced' | 'expert';
  question_text: string;
  options: string[];
  explanation?: string;
  correct_answer: string;
  is_synthetic: boolean;
}

export interface DailyTest {
  test_id: string;
  student_id: string;
  test_date: string;
  test_sequence: number;
  total_questions: number;
  duration_minutes: number;
  concepts_covered: string[];
  adaptive_weights: Record<string, number>;
  reasoning?: string;  // AI explanation for why these questions were chosen
  status: 'pending' | 'in_progress' | 'completed';
  questions: ExamQuestion[];
  created_at: string;
}

export interface TestAttempt {
  id: string;
  test_id: string;
  question_id: string;
  selected_answer: string;
  is_correct: boolean;
  time_spent_seconds: number;
  timestamp: string;
}

export interface FeedbackResponse {
  question_id: string;
  is_correct: boolean;
  explanation_vn: string;
  explanation_en: string;
  grammar_rule: string;
  recap_rule?: string;  // Quick recap of the rule
  why_wrong?: string;
  quick_recap_examples: Array<{ example: string; explanation: string }>;
  memory_hook?: string;
  root_cause?: {
    concept_id: string;
    concept_name: string;
    root_cause: string;
    misconception_pattern: string;
    related_concepts: string[];
    priority_score: number;
  };
  recommended_practice?: string[];
}

export interface CompetencyMap {
  student_id: string;
  test_date: string;
  grammar_score: number;
  vocabulary_score: number;
  reading_score: number;
  phonetics_score: number;
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  created_at: string;
}

export interface MegaTest {
  id: string;
  student_id: string;
  test_date: string;
  status: 'pending' | 'in_progress' | 'completed';
  questions: ExamQuestion[];
  duration_minutes: number;
  created_at: string;
}

export interface University {
  id: string;
  name: string;
  name_vi: string;
  location: string;
  english_benchmark: number;
  admission_probability?: number;
  category: 'safe' | 'target' | 'reach';
}

export interface CounselingReport {
  student_id: string;
  predicted_score: number;
  target_score: number;
  gap: number;
  universities: University[];
  safe_schools: University[];
  target_schools: University[];
  reach_schools: University[];
  created_at: string;
}

export interface RecoveryPlan {
  student_id: string;
  weak_concepts: string[];
  weekly_schedule: {
    week: number;
    focus_areas: string[];
    daily_tasks: string[];
  }[];
  estimated_completion_date: string;
  created_at: string;
}

export interface ProgressResponse {
  student_id: string;
  total_tests_taken: number;
  total_questions_answered: number;
  overall_accuracy: number;
  current_streak: number;
  knowledge_graph: Record<string, number>;
  recent_accuracy_trend: number[];
  next_recommended_test_date: string;
}

export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
}

// API Request types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  target_score: number;
  exam_date: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  student: Student;
}

export interface FeedbackRequest {
  student_id: string;
  question_id: string;
  selected_answer: string;
  time_spent_seconds: number;
}

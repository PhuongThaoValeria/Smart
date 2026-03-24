/**
 * API Client for Smart English Test-Prep
 * Uses fetch with type-safe responses
 * NO AUTH REQUIRED - Direct access to AI functions
 */

import type {
  Student,
  DailyTest,
  FeedbackResponse,
  CompetencyMap,
  MegaTest,
  CounselingReport,
  RecoveryPlan,
  ProgressResponse,
} from '@/types';

// In production (Vercel), use relative path to hit serverless functions
// In development, use localhost backend
const API_URL = process.env.NEXT_PUBLIC_API_URL || (
  process.env.NODE_ENV === 'production'
    ? '/api'  // Relative path for Vercel serverless functions
    : 'http://localhost:8000'
);

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(
          response.status,
          error.detail || error.message || 'API request failed'
        );
      }

      return response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(0, 'Network error: Unable to reach the server');
    }
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/api/v1/health/ping');
  }

  // Guest Student Profile (No Auth)
  async getProfile(): Promise<Student> {
    return this.request('/api/v1/students/me');
  }

  async getProgress(): Promise<ProgressResponse> {
    return this.request('/api/v1/students/progress');
  }

  // Daily Tests
  async generateDailyTest(data: {
    student_id: string;
    test_date: string;
  }): Promise<DailyTest> {
    return this.request('/api/v1/daily-tests/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async startTest(testId: string) {
    return this.request(`/api/v1/daily-tests/${testId}/start`, {
      method: 'POST',
    });
  }

  async submitTest(data: {
    test_id: string;
    student_id: string;
    answers: Array<{ question_id: string; selected_answer: string; time_spent_seconds: number }>;
  }) {
    return this.request('/api/v1/daily-tests/submit', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getTestHistory(studentId: string) {
    return this.request(`/api/v1/daily-tests/history?student_id=${studentId}`);
  }

  // Feedback
  async generateFeedback(data: {
    student_id: string;
    question_id: string;
    selected_answer: string;
    time_spent_seconds: number;
  }): Promise<FeedbackResponse> {
    return this.request('/api/v1/feedback/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getWeakConcepts(studentId: string) {
    return this.request(`/api/v1/feedback/weak-concepts?student_id=${studentId}`);
  }

  // Assessment
  async getMegaTestStatus(studentId: string) {
    return this.request(`/api/v1/assessment/status?student_id=${studentId}`);
  }

  async generateMegaTest(data: { student_id: string; test_date: string }): Promise<MegaTest> {
    return this.request('/api/v1/assessment/mega-test/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getCompetencyMap(studentId: string): Promise<CompetencyMap> {
    return this.request(`/api/v1/assessment/competency-map/latest?student_id=${studentId}`);
  }

  // Counseling
  async getCounselingReport(studentId: string): Promise<CounselingReport> {
    return this.request(`/api/v1/counseling/report?student_id=${studentId}`);
  }

  async getRecoveryPlan(studentId: string): Promise<RecoveryPlan> {
    return this.request(`/api/v1/counseling/recovery-plan?student_id=${studentId}`);
  }

  async getExamCountdown(studentId: string) {
    return this.request(`/api/v1/counseling/exam-countdown?student_id=${studentId}`);
  }
}

export const api = new APIClient(API_URL);
export { ApiError };
export default api;

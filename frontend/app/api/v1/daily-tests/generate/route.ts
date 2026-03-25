import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const body = await request.json();

  // Mock daily test generation
  const mockTest = {
    test_id: `test_${Date.now()}`,
    student_id: body.student_id || 'guest_student',
    test_date: new Date().toISOString(),
    duration_minutes: 15,
    questions: Array.from({ length: 15 }, (_, i) => ({
      question_id: `q${i + 1}`,
      question_text: `Sample question ${i + 1} for daily practice`,
      options: ['Option A', 'Option B', 'Option C', 'Option D'],
      correct_answer: 'A',
      concept_id: `concept_${i + 1}`,
      difficulty_level: 'intermediate'
    })),
    status: 'ready',
    created_at: new Date().toISOString()
  };

  return NextResponse.json(mockTest);
}

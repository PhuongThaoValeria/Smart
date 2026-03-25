import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const body = await request.json();

  // Mock test submission result
  return NextResponse.json({
    test_id: body.test_id,
    student_id: body.student_id,
    score: Math.floor(Math.random() * 40) + 60, // Random score 60-100
    correct_answers: Math.floor(Math.random() * 5) + 10,
    total_questions: body.answers?.length || 15,
    time_spent_minutes: Math.floor(Math.random() * 10) + 10,
    feedback: {
      weak_concepts: ['Grammar', 'Vocabulary'],
      recommended_topics: ['Gerunds', 'Conditionals']
    },
    submitted_at: new Date().toISOString()
  });
}

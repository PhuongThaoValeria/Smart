import { NextResponse } from 'next/server';

export async function GET() {
  // Mock progress data
  return NextResponse.json({
    student_id: 'guest_student',
    tests_completed: 12,
    accuracy: 78,
    streak_days: 5,
    weak_concepts: [
      { concept: 'Gerunds and Infinitives', mastery: 45 },
      { concept: 'Conditional Sentences', mastery: 60 },
      { concept: 'Relative Clauses', mastery: 70 }
    ],
    strong_concepts: [
      { concept: 'Present Perfect', mastery: 90 },
      { concept: 'Passive Voice', mastery: 85 }
    ]
  });
}

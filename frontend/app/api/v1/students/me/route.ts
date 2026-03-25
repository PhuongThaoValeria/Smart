import { NextResponse } from 'next/server';

export async function GET() {
  // Mock student data for demo
  return NextResponse.json({
    student_id: 'guest_student',
    name: 'Guest Student',
    email: 'guest@example.com',
    target_score: 8.5,
    exam_date: new Date(Date.now() + 45 * 24 * 60 * 60 * 1000).toISOString(),
    created_at: new Date().toISOString(),
    level: 'intermediate'
  });
}

"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Clock, ChevronLeft, ChevronRight, CheckCircle, XCircle, ArrowRight } from "lucide-react";
import type { ExamQuestion, DailyTest } from "@/types";
import api from "@/lib/api";

interface TestRunnerProps {
  test: DailyTest;
  onComplete: (results: {
    correctCount: number;
    totalQuestions: number;
    accuracy: number;
    answers: Array<{
      question_id: string;
      selected_answer: string;
      time_spent_seconds: number;
    }>;
  }) => void;
  onCancel: () => void;
}

export function TestRunner({ test, onComplete, onCancel }: TestRunnerProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Array<{
    question_id: string;
    selected_answer: string;
    time_spent_seconds: number;
  }>>([]);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [timeRemaining, setTimeRemaining] = useState(test.duration_minutes * 60);
  const [showFeedback, setShowFeedback] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [feedback, setFeedback] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [fadeState, setFadeState] = useState<'in' | 'out'>('in');
  const [questionTransitioning, setQuestionTransitioning] = useState(false);

  const currentQuestion = test.questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / test.questions.length) * 100;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Wrap with useCallback to fix ESLint warning
  const handleAutoSubmit = useCallback(() => {
    // Submit with current answers
    const correctCount = answers.filter(a => {
      const question = test.questions.find(q => q.question_id === a.question_id);
      return question && a.selected_answer.toUpperCase() === question.correct_answer.toUpperCase();
    }).length;

    const totalQuestions = test.questions.length;

    onComplete({
      correctCount,
      totalQuestions,
      accuracy: (correctCount / totalQuestions) * 100,
      answers,
    });
  }, [answers, test.questions, onComplete]);

  // Wrap with useCallback to fix ESLint warning
  const handleSubmit = useCallback(async () => {
    // Calculate results
    const correctCount = answers.filter(a => {
      const question = test.questions.find(q => q.question_id === a.question_id);
      return question && a.selected_answer.toUpperCase() === question.correct_answer.toUpperCase();
    }).length;

    const totalQuestions = test.questions.length;

    const results = {
      correctCount,
      totalQuestions,
      accuracy: (correctCount / totalQuestions) * 100,
      answers,
    };

    // Submit test results to backend for adaptive learning
    try {
      await api.submitTest({
        test_id: test.test_id,
        student_id: "guest_student_001",
        answers: answers,
      });
      console.log("✅ Test results submitted to backend successfully");
    } catch (error) {
      console.warn("⚠️ Failed to submit test results to backend:", error);
      // Continue anyway - results are still displayed to the user
    }

    onComplete(results);
  }, [answers, test.questions, test.test_id, onComplete]);

  // Timer - now includes handleAutoSubmit in dependencies
  useEffect(() => {
    if (timeRemaining <= 0) {
      handleAutoSubmit();
      return;
    }

    const timer = setInterval(() => {
      setTimeRemaining((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining, handleAutoSubmit]);

  // Reset timer for each question
  useEffect(() => {
    setStartTime(Date.now());
  }, [currentQuestionIndex]);

  const handleAnswerSelect = async (answer: string) => {
    if (selectedAnswer || questionTransitioning) return;

    setSelectedAnswer(answer);

    const timeSpent = Math.round((Date.now() - startTime) / 1000);
    const answerData = {
      question_id: currentQuestion.question_id,
      selected_answer: answer,
      time_spent_seconds: timeSpent,
    };

    // Save answer locally
    const newAnswers = [...answers, answerData];
    setAnswers(newAnswers);

    // Submit feedback to backend for adaptive learning
    setLoading(true);
    try {
      const result = await api.generateFeedback({
        student_id: "guest_student_001",
        question_id: currentQuestion.question_id,
        selected_answer: answer,
        time_spent_seconds: timeSpent,
      });

      setIsCorrect(result.is_correct);
      setFeedback(result);
      setShowFeedback(true);
    } catch (error) {
      console.error("Failed to get feedback:", error);

      // Enhanced fallback: check correctness locally and create basic feedback
      const correct = answer.toUpperCase() === currentQuestion.correct_answer.toUpperCase();
      setIsCorrect(correct);

      // Create fallback feedback
      setFeedback({
        is_correct: correct,
        explanation_vn: correct
          ? "Chính xác! Bạn đã chọn đáp án đúng."
          : `Chưa chính xác. Đáp án đúng là ${currentQuestion.correct_answer}). ${currentQuestion.explanation || ''}`,
        explanation_en: correct
          ? "Correct! You selected the right answer."
          : `Not quite. The correct answer is ${currentQuestion.correct_answer}).`,
        grammar_rule: "",
      });
      setShowFeedback(true);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = useCallback(async () => {
    setQuestionTransitioning(true);
    setFadeState('out');

    // Wait for fade-out animation
    await new Promise(resolve => setTimeout(resolve, 200));

    setShowFeedback(false);
    setSelectedAnswer(null);
    setIsCorrect(false);
    setFeedback(null);

    if (currentQuestionIndex < test.questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);

      // Wait for fade-in animation
      await new Promise(resolve => setTimeout(resolve, 100));
      setFadeState('in');
      setQuestionTransitioning(false);
    } else {
      handleSubmit();
    }
  }, [currentQuestionIndex, test.questions.length, handleSubmit]);

  // Keyboard support for advancing
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (showFeedback && !questionTransitioning && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        handleNext();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [showFeedback, questionTransitioning, handleNext]);

  const getOptionLabel = (option: string) => {
    // Extract just the letter (A, B, C, D) from option string
    return option.charAt(0);
  };

  const getOptionClass = (option: string) => {
    if (!selectedAnswer) return "option-btn";

    const isSelected = option === selectedAnswer;
    const isCorrectOption = option.charAt(0) === currentQuestion.correct_answer;

    if (showFeedback) {
      if (isCorrectOption) return "option-btn correct";
      if (isSelected && !isCorrectOption) return "option-btn incorrect";
    }

    if (isSelected) return "option-btn selected";

    return "option-btn";
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-2xl">Question {currentQuestionIndex + 1} of {test.questions.length}</CardTitle>
            <CardDescription>
              {test.test_date} • {test.duration_minutes} minutes
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            <span className={`text-2xl font-bold ${timeRemaining < 60 ? 'text-red-600' : ''}`}>
              {formatTime(timeRemaining)}
            </span>
          </div>
        </div>
        <Progress value={progress} className="mt-4" />
      </CardHeader>

      <CardContent>
        {fadeState === 'in' && (
          <div className="space-y-6">
            {/* Question */}
            <div className="bg-gray-50 p-6 rounded-lg">
              <p className="text-lg leading-relaxed whitespace-pre-line">
                {currentQuestion.question_text}
              </p>
            </div>

            {/* Options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {currentQuestion.options.map((option, idx) => (
                <button
                  key={idx}
                  onClick={() => !selectedAnswer && handleAnswerSelect(option)}
                  className={getOptionClass(option)}
                  disabled={!!selectedAnswer || questionTransitioning}
                >
                  <span className="font-bold text-lg mr-3">
                    {getOptionLabel(option)})
                  </span>
                  <span>{option.slice(2).trim()}</span>
                </button>
              ))}
            </div>

            {/* Feedback */}
            {showFeedback && feedback && (
              <div className={`p-6 rounded-lg ${isCorrect ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                <div className="flex items-start gap-3">
                  {isCorrect ? (
                    <CheckCircle className="h-6 w-6 text-green-600 mt-1 flex-shrink-0" />
                  ) : (
                    <XCircle className="h-6 w-6 text-red-600 mt-1 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    <h3 className={`text-lg font-semibold mb-2 ${isCorrect ? 'text-green-800' : 'text-red-800'}`}>
                      {isCorrect ? 'Chính xác!' : 'Chưa chính xác'}
                    </h3>
                    <p className="text-gray-700 mb-2">
                      {feedback.explanation_vn || feedback.explanation_en}
                    </p>
                    {feedback.grammar_rule && (
                      <p className="text-sm text-gray-600 italic">
                        Grammar: {feedback.grammar_rule}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Navigation */}
            {showFeedback && (
              <div className="flex justify-between items-center pt-4">
                <Button
                  variant="outline"
                  onClick={onCancel}
                  className="text-gray-600"
                >
                  End Test
                </Button>

                {currentQuestionIndex < test.questions.length - 1 ? (
                  <Button
                    onClick={handleNext}
                    disabled={questionTransitioning}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    {questionTransitioning ? 'Loading...' : 'Next Question'}
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                ) : (
                  <Button
                    onClick={handleSubmit}
                    disabled={questionTransitioning}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    {loading ? 'Submitting...' : 'Submit Test'}
                    <CheckCircle className="ml-2 h-5 w-5" />
                  </Button>
                )}
              </div>
            )}
          </div>
        )}
      </CardContent>

      <style jsx>{`
        .option-btn {
          padding: 1rem;
          border: 2px solid #e5e7eb;
          border-radius: 0.5rem;
          text-align: left;
          transition: all 0.2s;
          background: white;
          cursor: pointer;
        }

        .option-btn:hover:not(:disabled) {
          border-color: #3b82f6;
          background: #eff6ff;
        }

        .option-btn.selected {
          border-color: #3b82f6;
          background: #dbeafe;
        }

        .option-btn.correct {
          border-color: #10b981;
          background: #d1fae5;
        }

        .option-btn.incorrect {
          border-color: #ef4444;
          background: #fee2e2;
        }

        .option-btn:disabled {
          cursor: not-allowed;
          opacity: 0.7;
        }
      `}</style>
    </Card>
  );
}

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

  const handleAutoSubmit = () => {
    // Submit with current answers
    const correctCount = answers.filter(a => {
      const question = test.questions.find(q => q.question_id === a.question_id);
      return question && a.selected_answer.toUpperCase() === question.correct_answer.toUpperCase();
    }).length;

    onComplete({
      correctCount,
      totalQuestions: test.questions.length,
      accuracy: (correctCount / test.questions.length) * 100,
      answers,
    });
  };

  const handleSubmit = async () => {
    // Calculate results
    const correctCount = answers.filter(a => {
      const question = test.questions.find(q => q.question_id === a.question_id);
      return question && a.selected_answer.toUpperCase() === question.correct_answer.toUpperCase();
    }).length;

    const results = {
      correctCount,
      totalQuestions: test.questions.length,
      accuracy: (correctCount / test.questions.length) * 100,
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
  };

  // Timer
  useEffect(() => {
    if (timeRemaining <= 0) {
      handleAutoSubmit();
      return;
    }

    const timer = setInterval(() => {
      setTimeRemaining((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [timeRemaining]);

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
  }, [currentQuestionIndex, test.questions.length]);

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

  const getOptionText = (option: string) => {
    // Extract the text after the letter and parenthesis
    const match = option.match(/^[A-D]\)\s*(.+)$/);
    return match ? match[1] : option;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Daily Test</h2>
          <p className="text-gray-600">
            Question {currentQuestionIndex + 1} of {test.questions.length}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-gray-600">
            <Clock className={`h-5 w-5 ${timeRemaining < 60 ? 'text-red-600 animate-pulse' : ''}`} />
            <span className={`font-mono text-lg ${timeRemaining < 60 ? 'text-red-600 font-bold' : ''}`}>
              {formatTime(timeRemaining)}
            </span>
          </div>
          {answers.length > 0 && (
            <Button variant="outline" onClick={onCancel} disabled={questionTransitioning}>
              End Test
            </Button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <Progress value={progress} className="h-2" />
        <div className="flex justify-between text-sm text-gray-600">
          <span>{Math.round(progress)}% complete</span>
          <span>{answers.length} answered</span>
        </div>
      </div>

      {/* Question Card with Fade Animation */}
      <div className={`transition-opacity duration-200 ${fadeState === 'out' ? 'opacity-0' : 'opacity-100'}`}>
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="text-xl leading-relaxed">
                  {currentQuestion.question_text}
                </CardTitle>
                <CardDescription className="mt-3">
                  <Badge variant="outline" className="mr-2">{currentQuestion.concept_name}</Badge>
                  <Badge variant="outline">{currentQuestion.difficulty}</Badge>
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {currentQuestion.options.map((option) => {
                const letter = getOptionLabel(option);
                const isSelected = selectedAnswer === letter;
                const isCorrectOption = letter === currentQuestion.correct_answer;

                return (
                  <button
                    key={option}
                    onClick={() => handleAnswerSelect(letter)}
                    disabled={!!selectedAnswer || loading || questionTransitioning}
                    className={`w-full text-left p-4 rounded-lg border-2 transition-all duration-200 ${
                      isSelected
                        ? isCorrectOption
                          ? "border-green-500 bg-green-50 hover:border-green-600"
                          : "border-red-500 bg-red-50 hover:border-red-600"
                        : "border-gray-200 hover:border-blue-300 hover:bg-blue-50/30"
                    } ${selectedAnswer && !isSelected ? "opacity-40 cursor-not-allowed" : ""} ${loading ? "opacity-60 cursor-wait" : ""}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all ${
                        isSelected
                          ? isCorrectOption
                            ? "border-green-600 bg-green-600 text-white"
                            : "border-red-600 bg-red-600 text-white"
                          : "border-gray-300 hover:border-blue-400"
                      }`}>
                        {letter}
                      </div>
                      <span className="flex-1 font-medium">{getOptionText(option)}</span>
                      {showFeedback && isSelected && (
                        <div className="ml-2 animate-fade-in">
                          {isCorrect ? (
                            <CheckCircle className="h-6 w-6 text-green-600" />
                          ) : (
                            <XCircle className="h-6 w-6 text-red-600" />
                          )}
                        </div>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Feedback Section - Always visible when answer is selected */}
            {showFeedback && feedback && !loading && (
              <div className={`mt-6 p-5 rounded-lg border-2 animate-slide-up ${
                isCorrect
                  ? "bg-green-50 border-green-200"
                  : "bg-orange-50 border-orange-200"
              }`}>
                <div className="flex items-start gap-3">
                  {isCorrect ? (
                    <CheckCircle className="h-6 w-6 text-green-600 mt-0.5 flex-shrink-0" />
                  ) : (
                    <XCircle className="h-6 w-6 text-orange-600 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1 space-y-3">
                    <h4 className={`font-bold text-lg ${
                      isCorrect ? "text-green-900" : "text-orange-900"
                    }`}>
                      {isCorrect ? "Chính xác! ✨" : "Chưa đúng 💪"}
                    </h4>

                    {/* Vietnamese Explanation */}
                    {feedback.explanation_vn && (
                      <div className="text-sm text-gray-800 leading-relaxed">
                        <span className="font-semibold">Giải thích:</span> {feedback.explanation_vn}
                      </div>
                    )}

                    {/* English Explanation (if different) */}
                    {feedback.explanation_en && feedback.explanation_en !== feedback.explanation_vn && (
                      <div className="text-sm text-gray-600 leading-relaxed border-t pt-2 mt-2">
                        <span className="font-semibold text-gray-500">Explanation:</span> {feedback.explanation_en}
                      </div>
                    )}

                    {/* Grammar Rule */}
                    {feedback.grammar_rule && (
                      <div className="mt-3 p-3 bg-white rounded-lg border">
                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                          📚 Grammar Rule
                        </p>
                        <p className="text-sm text-gray-800 leading-relaxed">
                          {feedback.grammar_rule}
                        </p>
                      </div>
                    )}

                    {/* Quick Recap for wrong answers */}
                    {!isCorrect && feedback.recap_rule && (
                      <div className="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <p className="text-sm text-blue-900">
                          <strong>🔄 Nhắc lại:</strong> {feedback.recap_rule}
                        </p>
                      </div>
                    )}

                    {/* Memory Hook (if available) */}
                    {feedback.memory_hook && (
                      <div className="mt-2 p-3 bg-purple-50 rounded-lg border border-purple-200">
                        <p className="text-sm text-purple-900">
                          <strong>💡 Mẹo nhớ:</strong> {feedback.memory_hook}
                        </p>
                      </div>
                    )}

                    {/* Prominent Next Question Button */}
                    <Button
                      onClick={handleNext}
                      disabled={questionTransitioning}
                      className="mt-4 w-full sm:w-auto min-w-[180px] font-semibold"
                      size="lg"
                    >
                      {currentQuestionIndex < test.questions.length - 1 ? (
                        <>
                          Next Question
                          <ArrowRight className="ml-2 h-5 w-5" />
                        </>
                      ) : (
                        "See Results 🎉"
                      )}
                    </Button>

                    {/* Keyboard hint */}
                    <p className="text-xs text-gray-500 text-center mt-2">
                      Press <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-gray-700 font-mono">Enter</kbd> or <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-gray-700 font-mono">Space</kbd> to continue
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="mt-6 flex flex-col items-center justify-center p-6 space-y-3">
                <div className="animate-spin rounded-full h-10 w-10 border-4 border-blue-600 border-t-transparent" />
                <div className="text-center space-y-1">
                  <p className="text-gray-800 font-medium">AI is analyzing your answer...</p>
                  <p className="text-sm text-gray-500">Preparing personalized feedback</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Navigation hint at bottom */}
      {!showFeedback && !selectedAnswer && (
        <div className="text-center text-sm text-gray-500">
          Select an answer to see AI-powered feedback
        </div>
      )}
    </div>
  );
}

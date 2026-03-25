"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";
import { BookOpen, Brain, TrendingUp, Clock, Loader2, Trophy, Target, CheckCircle } from "lucide-react";
import { TestRunner } from "@/components/features/test-runner";
import api from "@/lib/api";
import type { DailyTest } from "@/types";

const GUEST_STUDENT_ID = "guest_student_001";

type TestState = "idle" | "generating" | "ready" | "running" | "completed";

export default function DailyTestPage() {
  const [testState, setTestState] = useState<TestState>("idle");
  const [currentTest, setCurrentTest] = useState<DailyTest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);

  const handleGenerateTest = async () => {
    setTestState("generating");
    setError(null);
    try {
      const test = await api.generateDailyTest({
        student_id: GUEST_STUDENT_ID,
        test_date: new Date().toISOString().split('T')[0],
      });
      setCurrentTest(test);
      setTestState("ready");
    } catch (err: any) {
      console.error("Failed to generate test:", err);
      setError(err.message || "Failed to generate test. Please try again.");
      setTestState("idle");
    }
  };

  const handleStartTest = () => {
    setTestState("running");
  };

  const handleTestComplete = (testResults: any) => {
    setResults(testResults);
    setTestState("completed");
  };

  const handleRetakeTest = () => {
    setTestState("idle");
    setCurrentTest(null);
    setResults(null);
  };

  const getWeightBadgeColor = (weight: number) => {
    if (weight >= 1.3) return "bg-orange-100 text-orange-800 border-orange-300";
    if (weight >= 1.2) return "bg-yellow-100 text-yellow-800 border-yellow-300";
    if (weight >= 1.1) return "bg-blue-100 text-blue-800 border-blue-300";
    return "bg-gray-100 text-gray-800 border-gray-300";
  };

  const getWeightLabel = (weight: number) => {
    if (weight >= 1.3) return `High Priority (${Math.round(weight * 100)}%)`;
    if (weight >= 1.2) return `Priority (${Math.round(weight * 100)}%)`;
    if (weight >= 1.1) return `Standard (${Math.round(weight * 100)}%)`;
    return "Review";
  };

  // Test Runner View
  if (testState === "running" && currentTest) {
    return (
      <div className="max-w-4xl mx-auto">
        <TestRunner
          test={currentTest}
          onComplete={handleTestComplete}
          onCancel={() => setTestState("ready")}
        />
      </div>
    );
  }

  // Results View
  if (testState === "completed" && results) {
    const score = results.accuracy;
    const scoreColor = score >= 80 ? "text-green-600" : score >= 60 ? "text-yellow-600" : "text-red-600";
    const scoreMessage = score >= 80 ? "Excellent work!" : score >= 60 ? "Good effort!" : "Keep practicing!";

    return (
      <div className="space-y-6">
        <div className="text-center">
          <Trophy className="h-16 w-16 mx-auto text-yellow-500 mb-4" />
          <h2 className="text-3xl font-bold">Test Complete!</h2>
          <p className="text-gray-600 mt-2">{scoreMessage}</p>
        </div>

        <Card className="max-w-2xl mx-auto">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <div>
                <p className="text-sm text-gray-500 uppercase">Your Score</p>
                <p className={`text-6xl font-bold ${scoreColor}`}>
                  {Math.round(results.accuracy)}%
                </p>
              </div>
              <div className="flex justify-center gap-8">
                <div>
                  <p className="text-sm text-gray-500">Correct</p>
                  <p className="text-2xl font-semibold text-green-600">
                    {results.correctCount}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total</p>
                  <p className="text-2xl font-semibold">
                    {results.totalQuestions}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Streak</p>
                  <p className="text-2xl font-semibold text-blue-600">
                    🔥 {results.correctCount >= 10 ? results.correctCount : 1}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-center gap-4">
          <Button size="lg" onClick={handleRetakeTest}>
            Take Another Test
          </Button>
          <Button size="lg" variant="outline" onClick={() => setCurrentTest(null)}>
            Review Answers
          </Button>
        </div>
      </div>
    );
  }

  // Initial State - Ready to Generate
  if (testState === "idle" && !currentTest) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Daily Test</h1>
          <p className="mt-2 text-gray-600">
            15 questions • 15 minutes • Adaptive to your level
          </p>
        </div>

        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <p className="text-red-800">{error}</p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-blue-600" />
              Ready to Start?
            </CardTitle>
            <CardDescription>
              This test will adapt to your learning level based on 2019-2025 exam trends.
              Concepts you struggle with will get more focus in future tests.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="flex items-center gap-3 rounded-lg border border-gray-200 p-4">
                  <BookOpen className="h-8 w-8 text-blue-600" />
                  <div>
                    <p className="text-sm font-medium">Real Exam Questions</p>
                    <p className="text-xs text-gray-500">2019-2025 patterns</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 rounded-lg border border-gray-200 p-4">
                  <TrendingUp className="h-8 w-8 text-green-600" />
                  <div>
                    <p className="text-sm font-medium">15 Minutes</p>
                    <p className="text-xs text-gray-500">Quick daily practice</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 rounded-lg border border-gray-200 p-4">
                  <Target className="h-8 w-8 text-purple-600" />
                  <div>
                    <p className="text-sm font-medium">AI Feedback</p>
                    <p className="text-xs text-gray-500">Instant explanations</p>
                  </div>
                </div>
              </div>

              <Button
                className="w-full"
                size="lg"
                onClick={handleGenerateTest}
              >
                Generate Today&apos;s Test
              </Button>

              <p className="text-center text-xs text-gray-500">
                Guest Mode • No login required • Powered by Claude AI
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Generating State
  if (testState === "generating") {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
          <div className="mt-4 text-center">
            <h3 className="text-lg font-semibold text-gray-900">
              Analyzing exam patterns...
            </h3>
            <p className="mt-2 text-sm text-gray-600">
              Selecting questions based on your learning profile
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Test Ready - Show Overview
  if (testState === "ready" && currentTest) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Test Ready!</h1>
          <p className="mt-2 text-gray-600">
            {currentTest.total_questions} questions • {currentTest.duration_minutes} minutes
          </p>
        </div>

        {/* Reasoning Card */}
        {currentTest.reasoning && (
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-sm font-semibold text-blue-900">
                Why these questions?
              </CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="whitespace-pre-wrap text-sm text-blue-800 font-mono">
                {currentTest.reasoning}
              </pre>
            </CardContent>
          </Card>
        )}

        {/* Focus Areas */}
        {Object.keys(currentTest.adaptive_weights).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Today&apos;s Focus Areas</CardTitle>
              <CardDescription>
                Concepts prioritized based on exam frequency
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(currentTest.adaptive_weights)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 5)
                  .map(([concept, weight]) => (
                    <div
                      key={concept}
                      className="flex items-center justify-between rounded-lg border border-gray-200 p-4"
                    >
                      <div>
                        <h3 className="font-medium">{concept}</h3>
                      </div>
                      <Badge className={getWeightBadgeColor(weight)}>
                        {getWeightLabel(weight)}
                      </Badge>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Test Preview */}
        <Card>
          <CardHeader>
            <CardTitle>You&apos;re All Set!</CardTitle>
            <CardDescription>
              Click Start when you&apos;re ready to begin
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="rounded-lg border border-gray-200 p-4">
                <h4 className="font-medium">Concepts Covered</h4>
                <div className="mt-2 flex flex-wrap gap-2">
                  {currentTest.concepts_covered.map((concept) => (
                    <Badge key={concept} variant="outline">
                      {concept}
                    </Badge>
                  ))}
                </div>
              </div>

              <Button
                className="w-full"
                size="lg"
                onClick={handleStartTest}
              >
                <CheckCircle className="h-5 w-5 mr-2" />
                Start Test
              </Button>

              <Button
                variant="outline"
                className="w-full"
                onClick={handleRetakeTest}
              >
                Regenerate Test
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
}

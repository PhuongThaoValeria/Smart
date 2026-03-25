"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function CounselingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">University Counseling</h1>
        <p className="mt-2 text-gray-600">
          Admission predictions and personalized recovery plans
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Predicted Score</CardTitle>
          <CardDescription>Based on your current performance</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4">
            <div className="text-4xl font-bold text-blue-600">7.8</div>
            <div>
              <p className="text-sm text-gray-600">Target: 8.5</p>
              <p className="text-sm text-gray-600">Gap: -0.7</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>University Admission Probability</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-lg border border-gray-200 p-4">
              <div>
                <h3 className="font-medium">University of Languages</h3>
                <p className="text-sm text-gray-500">Benchmark: 8.0</p>
              </div>
              <Badge variant="success">98%</Badge>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-gray-200 p-4">
              <div>
                <h3 className="font-medium">Foreign Trade University</h3>
                <p className="text-sm text-gray-500">Benchmark: 8.5</p>
              </div>
              <Badge variant="warning">78%</Badge>
            </div>

            <div className="flex items-center justify-between rounded-lg border border-gray-200 p-4">
              <div>
                <h3 className="font-medium">National University</h3>
                <p className="text-sm text-gray-500">Benchmark: 9.0</p>
              </div>
              <Badge variant="error">45%</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recovery Plan</CardTitle>
          <CardDescription>Personalized study schedule</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">Week 1</h3>
                <Badge variant="default">Focus: Reported Speech</Badge>
              </div>
              <p className="mt-2 text-sm text-gray-600">
                Daily practice with transformation exercises and feedback review
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

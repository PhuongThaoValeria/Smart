"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="space-y-3">
        <h1 className="text-5xl font-display font-extrabold text-midnight-900 tracking-tight" style={{ letterSpacing: '-0.02em' }}>
          Welcome Back!
        </h1>
        <p className="text-lg font-sans text-midnight-500 font-medium">
          Your English Exam Prep Portal
        </p>
      </div>

      {/* Focus Zone - Hero Action */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Hero Action */}
        <Card className="glass-card glass-card-hover rounded-glass border-0">
          <CardContent className="p-8 space-y-6">
            <div>
              <h2 className="text-2xl font-display font-semibold text-midnight-900 mb-3 tracking-tight">
                Your Daily Practice Agent is Ready
              </h2>
              <p className="text-midnight-500 text-base leading-relaxed">
                15 minutes. Personalized to erase your weaknesses.
              </p>
            </div>
            <Link href="/dashboard/daily-test" className="block">
              <Button className="w-full bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white rounded-hero py-7 text-base font-semibold shadow-hero animate-pulse-glow transition-all duration-300">
                Start Today's Agent
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Right: Analytics Preview */}
        <Link href="/dashboard/analytics" className="group block">
          <Card className="glass-card glass-card-hover rounded-glass border-0 h-full cursor-pointer">
            <CardContent className="p-8 space-y-6">
              <div>
                <h2 className="text-2xl font-display font-semibold text-midnight-900 mb-3 tracking-tight">
                  Your Competency Map
                </h2>
                <p className="text-midnight-500 text-base leading-relaxed">
                  Unlock insights. Target errors.
                </p>
              </div>

              {/* Mini Chart Preview */}
              <div className="relative h-24 w-full">
                <svg viewBox="0 0 200 80" className="w-full h-full">
                  {/* Grid lines */}
                  <line x1="0" y1="20" x2="200" y2="20" stroke="#E2E8F0" strokeWidth="1" />
                  <line x1="0" y1="40" x2="200" y2="40" stroke="#E2E8F0" strokeWidth="1" />
                  <line x1="0" y1="60" x2="200" y2="60" stroke="#E2E8F0" strokeWidth="1" />

                  {/* Gradient line chart */}
                  <defs>
                    <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#6366F1" stopOpacity="0.3" />
                      <stop offset="50%" stopColor="#6366F1" stopOpacity="0.8" />
                      <stop offset="100%" stopColor="#8B5CF6" stopOpacity="1" />
                    </linearGradient>
                    <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor="#6366F1" stopOpacity="0.2" />
                      <stop offset="100%" stopColor="#6366F1" stopOpacity="0" />
                    </linearGradient>
                  </defs>

                  {/* Area fill */}
                  <path
                    d="M 0 60 L 0 50 L 33 45 L 66 35 L 100 40 L 133 30 L 166 25 L 200 20 L 200 80 L 0 80 Z"
                    fill="url(#areaGradient)"
                  />

                  {/* Line */}
                  <path
                    d="M 0 50 L 33 45 L 66 35 L 100 40 L 133 30 L 166 25 L 200 20"
                    fill="none"
                    stroke="url(#lineGradient)"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="transition-all duration-300 group-hover:stroke-opacity-100"
                  />

                  {/* Data points */}
                  <circle cx="0" cy="50" r="3" fill="#6366F1" className="opacity-60" />
                  <circle cx="33" cy="45" r="3" fill="#6366F1" className="opacity-70" />
                  <circle cx="66" cy="35" r="3" fill="#6366F1" className="opacity-80" />
                  <circle cx="100" cy="40" r="3" fill="#7C3AED" className="opacity-80" />
                  <circle cx="133" cy="30" r="3" fill="#8B5CF6" className="opacity-90" />
                  <circle cx="166" cy="25" r="3" fill="#8B5CF6" className="opacity-95" />
                  <circle cx="200" cy="20" r="4" fill="#A78BFA" className="group-hover:scale-125 transition-transform duration-300" />
                </svg>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Success Cards - Glassmorphism */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Tests Card */}
        <Card className="glass-card glass-card-hover rounded-glass border-0">
          <CardContent className="p-6 space-y-4">
            <div>
              <p className="text-sm font-semibold text-midnight-500 mb-2 uppercase tracking-wider">Tests</p>
              <p className="text-5xl font-display font-bold text-midnight-900">12</p>
            </div>
            <p className="text-xs font-medium text-accent-emerald/80">+2 this week</p>
          </CardContent>
        </Card>

        {/* Accuracy Card - Emerald Sea */}
        <Card className="glass-card glass-card-hover rounded-glass border-0">
          <CardContent className="p-6 space-y-4">
            <div>
              <p className="text-sm font-semibold text-midnight-500 mb-2 uppercase tracking-wider">Accuracy</p>
              <p className="text-5xl font-display font-bold text-accent-emerald">78%</p>
            </div>
            <p className="text-xs font-medium text-accent-emerald/80">+5% improvement</p>
          </CardContent>
        </Card>

        {/* Target Card - Amber Sunset */}
        <Card className="glass-card glass-card-hover rounded-glass border-0">
          <CardContent className="p-6 space-y-4">
            <div>
              <p className="text-sm font-semibold text-midnight-500 mb-2 uppercase tracking-wider">Target</p>
              <div className="flex items-baseline gap-3">
                <span className="text-4xl font-display font-bold text-accent-amber">8.5</span>
                <span className="text-sm font-medium text-midnight-400">7.8 pred</span>
              </div>
            </div>
            <p className="text-xs font-medium text-midnight-400">Band Score</p>
          </CardContent>
        </Card>

        {/* Days Card */}
        <Card className="glass-card glass-card-hover rounded-glass border-0">
          <CardContent className="p-6 space-y-4">
            <div>
              <p className="text-sm font-semibold text-midnight-500 mb-2 uppercase tracking-wider">Days</p>
              <p className="text-5xl font-display font-bold text-accent-amber">45</p>
            </div>
            <p className="text-xs font-medium text-midnight-400">Until exam</p>
          </CardContent>
        </Card>
      </div>

      {/* Counseling CTA */}
      <Link href="/dashboard/counseling" className="block group">
        <Card className="glass-card glass-card-hover rounded-glass border-0 cursor-pointer">
          <CardContent className="p-8">
            <div className="flex items-center justify-between">
              <div className="space-y-2">
                <h3 className="text-xl font-display font-semibold text-midnight-900 group-hover:text-primary-600 transition-colors tracking-tight">
                  University Counseling
                </h3>
                <p className="text-base text-midnight-500">
                  Admission predictions and recovery plans
                </p>
              </div>
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>
      </Link>
    </div>
  );
}

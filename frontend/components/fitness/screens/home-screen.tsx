"use client";

import { useApp } from "@/lib/app-context";
import { GlassCard } from "@/components/fitness/glass-card";
import { ThemeToggle } from "@/components/fitness/theme-toggle";
import { ProfileSelector } from "../profile-selector";
import { Play, Dumbbell, Route, Clock, Target, Flame } from "lucide-react";
import { cn } from "@/lib/utils";

export function HomeScreen() {
  const { setCurrentScreen, sessionHistory, calibrationData, userProfile } = useApp();

  const lastSession = sessionHistory[0];
  const totalRepsToday = sessionHistory
    .filter(
      (s: any) => new Date(s.date).toDateString() === new Date().toDateString()
    )
    .reduce((acc: number, s: any) => acc + s.totalReps, 0);

  return (
    <div className="min-h-screen pb-24 pt-16">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              {userProfile ? `Hello, ${userProfile.name}` : "Virtual Coach"}
            </h1>
            <p className="text-muted-foreground mt-1">
              {"Ready for your workout?"}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <ProfileSelector />
            <ThemeToggle />
          </div>
        </div>

        {/* Status Badge */}
        {calibrationData.isCalibrated && (
          <div className="mb-6">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              <span className="text-xs font-medium text-primary">
                Profile calibrated
              </span>
            </div>
          </div>
        )}

        {/* Main Action Cards */}
        <div className="grid gap-4 md:grid-cols-3 mb-8">
          {/* Quick Start */}
          <GlassCard
            hover
            onClick={() => setCurrentScreen("quick-start")}
            className="group"
          >
            <div className="flex flex-col h-full">
              <div
                className={cn(
                  "w-14 h-14 rounded-2xl flex items-center justify-center mb-4",
                  "bg-primary/10 group-hover:bg-primary/20 transition-colors"
                )}
              >
                <Play className="h-7 w-7 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Quick Start
              </h3>
              <p className="text-sm text-muted-foreground flex-1">
                {"Automatically start your next recommended workout"}
              </p>
              <div className="mt-4 pt-4 border-t border-border/50">
                <span className="text-xs text-primary font-medium">
                  {"Instant Start"}
                </span>
              </div>
            </div>
          </GlassCard>

          {/* Mode Manuel */}
          <GlassCard
            hover
            onClick={() => setCurrentScreen("manual-mode")}
            className="group"
          >
            <div className="flex flex-col h-full">
              <div
                className={cn(
                  "w-14 h-14 rounded-2xl flex items-center justify-center mb-4",
                  "bg-secondary/10 group-hover:bg-secondary/20 transition-colors"
                )}
              >
                <Dumbbell className="h-7 w-7 text-secondary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Manual Mode
              </h3>
              <p className="text-sm text-muted-foreground flex-1">
                Choose your muscle group and exercises
              </p>
              <div className="mt-4 pt-4 border-t border-border/50">
                <span className="text-xs text-secondary font-medium">
                  {"Customized"}
                </span>
              </div>
            </div>
          </GlassCard>

          {/* Custom Chain */}
          <GlassCard
            hover
            onClick={() => setCurrentScreen("custom-chain")}
            className="group"
          >
            <div className="flex flex-col h-full">
              <div
                className={cn(
                  "w-14 h-14 rounded-2xl flex items-center justify-center mb-4",
                  "bg-accent/10 group-hover:bg-accent/20 transition-colors"
                )}
              >
                <Route className="h-7 w-7 text-accent" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Workout Plan
              </h3>
              <p className="text-sm text-muted-foreground flex-1">
                {"Create your personalized training program"}
              </p>
              <div className="mt-4 pt-4 border-t border-border/50">
                <span className="text-xs text-accent font-medium">
                  {"Advanced Builder"}
                </span>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Today's Stats */}
        <div className="grid gap-4 md:grid-cols-3 mb-8">
          <GlassCard className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
              <Target className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">
                {totalRepsToday}
              </p>
              <p className="text-xs text-muted-foreground">{"Reps today"}</p>
            </div>
          </GlassCard>

          <GlassCard className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center">
              <Flame className="h-6 w-6 text-accent" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">
                {sessionHistory
                  .filter(
                    (s) =>
                      new Date(s.date).toDateString() ===
                      new Date().toDateString()
                  )
                  .reduce((acc: number, s: any) => acc + s.caloriesBurned, 0)
                  .toFixed(3)}
              </p>
              <p className="text-xs text-muted-foreground">Calories burned</p>
            </div>
          </GlassCard>

          <GlassCard className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center">
              <Clock className="h-6 w-6 text-secondary" />
            </div>
            <div>
              <p className="text-2xl font-bold text-foreground">
                {sessionHistory.length}
              </p>
              <p className="text-xs text-muted-foreground">Total sessions</p>
            </div>
          </GlassCard>
        </div>

        {/* Last Session */}
        {lastSession && (
          <GlassCard>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-foreground">
                {"Last Session"}
              </h3>
              <span className="text-xs text-muted-foreground">
                {new Date(lastSession.date).toLocaleDateString("en-US", {
                  weekday: "long",
                  day: "numeric",
                  month: "short",
                })}
              </span>
            </div>

            <div className="space-y-3 mb-4">
              {lastSession.exercises.map((ex, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between py-2 border-b border-border/30 last:border-0"
                >
                  <span className="text-sm text-foreground">{ex.name}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-muted-foreground">
                      {ex.reps} reps
                    </span>
                    <div className="flex items-center gap-1">
                      <div
                        className={cn(
                          "w-2 h-2 rounded-full",
                          ex.qualityScore >= 90
                            ? "bg-primary"
                            : ex.qualityScore >= 75
                              ? "bg-accent"
                              : "bg-destructive"
                        )}
                      />
                      <span className="text-xs text-muted-foreground">
                        {ex.qualityScore}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={() => setCurrentScreen("quick-start")}
              className={cn(
                "w-full py-3 rounded-xl font-medium transition-all",
                "bg-primary text-primary-foreground",
                "hover:opacity-90 active:scale-[0.98]"
              )}
            >
              Resume Session
            </button>
          </GlassCard>
        )}

        {/* Calibration CTA */}
        {!calibrationData.isCalibrated && (
          <GlassCard className="mt-6 border-dashed border-2 border-primary/30">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <Target className="h-6 w-6 text-primary" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-foreground">
                  Calibration Recommended
                </h4>
                <p className="text-sm text-muted-foreground">
                  Personalize thresholds based on your morphology
                </p>
              </div>
              <button
                onClick={() => setCurrentScreen("calibration")}
                className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity"
              >
                Calibrate
              </button>
            </div>
          </GlassCard>
        )}
      </div>
    </div>
  );
}

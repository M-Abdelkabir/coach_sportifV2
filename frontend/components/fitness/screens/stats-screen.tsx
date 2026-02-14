"use client";

import { useApp } from "@/lib/app-context";
import { GlassCard } from "@/components/fitness/glass-card";
import { ProgressRing } from "@/components/fitness/progress-ring";
import { ArrowLeft, Target, Flame, Activity, TrendingUp, User } from "lucide-react";
import { cn } from "@/lib/utils";

export function StatsScreen() {
  const { setCurrentScreen, sessionHistory, calibrationData } = useApp();

  const totalReps = sessionHistory.reduce((acc: number, s: any) => acc + s.totalReps, 0);
  const totalCalories = sessionHistory.reduce(
    (acc: number, s: any) => acc + s.caloriesBurned,
    0
  );
  const avgPostureAccuracy =
    sessionHistory.length > 0
      ? Math.round(
        sessionHistory.reduce((acc: number, s: any) => acc + s.postureAccuracy, 0) /
        sessionHistory.length
      )
      : 0;

  // Real Weekly Data Calculation
  const weekDays = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];
  const weeklyReps = new Array(7).fill(0);

  // Map JS getDay (0=Sun, 1=Mon...) to our array (0=Mon, 1=Tue... 6=Sun)
  const getDayIdx = (date: Date) => {
    const day = date.getDay();
    return day === 0 ? 6 : day - 1;
  };

  const now = new Date();
  const startOfWeek = new Date(now);
  startOfWeek.setDate(now.getDate() - getDayIdx(now));
  startOfWeek.setHours(0, 0, 0, 0);

  sessionHistory.forEach((s: any) => {
    const sDate = new Date(s.date);
    if (sDate >= startOfWeek) {
      const idx = getDayIdx(sDate);
      weeklyReps[idx] += s.totalReps;
    }
  });

  const maxReps = Math.max(...weeklyReps, 1); // Avoid division by zero

  const performanceScore = Math.min(
    100,
    Math.round((totalReps / 500) * 50 + avgPostureAccuracy * 0.5)
  );

  // Fatigue Estimation based on quality score and recent reps
  const latestSession = sessionHistory[0];
  const fatigueValue = latestSession
    ? Math.min(100, (latestSession.totalReps / 50) * 100)
    : 0;
  const fatigueLabel = fatigueValue > 70 ? "Elevé" : fatigueValue > 40 ? "Moyen" : "Faible";

  return (
    <div className="min-h-screen pb-24 pt-16">
      {/* Header */}
      <div className="fixed top-12 left-0 right-0 z-40 glass-panel px-4 py-3">
        <div className="flex items-center gap-4 max-w-4xl mx-auto">
          <button
            onClick={() => setCurrentScreen("home")}
            className="p-2 rounded-xl hover:bg-muted/50 transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-foreground" />
          </button>
          <div>
            <h1 className="text-lg font-semibold text-foreground">
              Statistiques
            </h1>
            <p className="text-xs text-muted-foreground">
              Suivi de vos performances
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 pt-20">
        {/* Profile & Performance */}
        <div className="grid gap-4 md:grid-cols-2 mb-6">
          <GlassCard>
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-secondary/10 flex items-center justify-center">
                <User className="h-8 w-8 text-secondary" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-foreground">
                  Athlète
                </h3>
                <p className="text-sm text-muted-foreground">
                  {calibrationData.isCalibrated ? "Profil calibré" : "Non calibré"}
                </p>
                {calibrationData.isCalibrated && (
                  <>
                    <div className="flex gap-2 mt-2">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                        Morphologie analysée
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      Body Type: {calibrationData.body_type || "Unknown"}
                    </p>
                  </>
                )}
              </div>
            </div>
          </GlassCard>

          <GlassCard>
            <div className="flex items-center gap-4">
              <ProgressRing progress={performanceScore} size={64} strokeWidth={5}>
                <span className="text-lg font-bold text-foreground">
                  {performanceScore}
                </span>
              </ProgressRing>
              <div>
                <h3 className="text-lg font-semibold text-foreground">
                  Score Performance
                </h3>
                <p className="text-sm text-muted-foreground">
                  {performanceScore >= 80
                    ? "Excellent"
                    : performanceScore >= 60
                      ? "Très bien"
                      : "En progression"}
                </p>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <GlassCard className="text-center">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-2">
              <Target className="h-5 w-5 text-primary" />
            </div>
            <p className="text-2xl font-bold text-foreground">{totalReps}</p>
            <p className="text-xs text-muted-foreground">Reps totales</p>
          </GlassCard>

          <GlassCard className="text-center">
            <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center mx-auto mb-2">
              <Flame className="h-5 w-5 text-accent" />
            </div>
            <p className="text-2xl font-bold text-foreground">{totalCalories.toFixed(3)}</p>
            <p className="text-xs text-muted-foreground">Calories</p>
          </GlassCard>

          <GlassCard className="text-center">
            <div className="w-10 h-10 rounded-xl bg-secondary/10 flex items-center justify-center mx-auto mb-2">
              <Activity className="h-5 w-5 text-secondary" />
            </div>
            <p className="text-2xl font-bold text-foreground">
              {avgPostureAccuracy}%
            </p>
            <p className="text-xs text-muted-foreground">Posture</p>
          </GlassCard>
        </div>

        {/* Weekly Chart */}
        <GlassCard className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">
              Cette semaine
            </h3>
            <div className="flex items-center gap-1 text-primary">
              <TrendingUp className="h-4 w-4" />
              <span className="text-sm font-medium">Réel</span>
            </div>
          </div>

          <div className="flex items-end justify-between gap-2 h-32">
            {weekDays.map((day, i) => (
              <div key={day} className="flex-1 flex flex-col items-center gap-2">
                <div className="w-full flex flex-col items-center justify-end h-24">
                  <div
                    className={cn(
                      "w-full rounded-t-lg transition-all duration-500",
                      weeklyReps[i] > 0 ? "bg-primary" : "bg-muted",
                      i === getDayIdx(new Date()) && "glow-energy"
                    )}
                    style={{
                      height: `${(weeklyReps[i] / maxReps) * 100}%`,
                      minHeight: weeklyReps[i] > 0 ? "8px" : "4px",
                    }}
                  />
                </div>
                <span className="text-xs text-muted-foreground">{day}</span>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Fatigue & Progress Indicators */}
        <div className="grid gap-4 md:grid-cols-2 mb-6">
          <GlassCard>
            <h3 className="text-sm font-semibold text-foreground mb-3">
              Niveau de fatigue
            </h3>
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <div className="h-3 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary via-accent to-destructive rounded-full transition-all duration-500"
                    style={{ width: `${fatigueValue}%` }}
                  />
                </div>
              </div>
              <span className="text-sm font-medium text-primary">{fatigueLabel}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {fatigueValue > 70
                ? "Fatigue importante, repos conseillé"
                : "Bonne récupération, prêt pour l'entraînement"}
            </p>
          </GlassCard>

          <GlassCard>
            <h3 className="text-sm font-semibold text-foreground mb-3">
              Tendance de progression
            </h3>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-primary">+23%</span>
              <span className="text-sm text-muted-foreground">ce mois</span>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Progression régulière sur les squats
            </p>
          </GlassCard>
        </div>

        {/* Session History */}
        <GlassCard>
          <h3 className="text-lg font-semibold text-foreground mb-4">
            Historique
          </h3>
          <div className="space-y-3">
            {sessionHistory.map((session, i) => (
              <div
                key={i}
                className="flex items-center gap-4 py-3 border-b border-border/30 last:border-0"
              >
                <div className="w-12 text-center">
                  <p className="text-lg font-bold text-foreground">
                    {new Date(session.date).getDate()}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(session.date).toLocaleDateString("fr-FR", {
                      month: "short",
                    })}
                  </p>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-foreground">
                    {session.exercises.map((e) => e.name).join(", ")}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {session.totalReps} reps • {session.caloriesBurned} cal
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <div
                    className={cn(
                      "w-2 h-2 rounded-full",
                      session.postureAccuracy >= 90
                        ? "bg-primary"
                        : session.postureAccuracy >= 75
                          ? "bg-accent"
                          : "bg-destructive"
                    )}
                  />
                  <span className="text-sm font-medium text-foreground">
                    {session.postureAccuracy}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}

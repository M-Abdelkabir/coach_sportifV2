"use client";

import { useApp, MuscleGroup, Exercise, defaultExercises } from "@/lib/app-context";
import { GlassCard } from "@/components/fitness/glass-card";
import { CameraFeed } from "@/components/fitness/camera-feed";
import { useState } from "react";
import { ArrowLeft, Check, Minus, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

type Step = "muscle-group" | "exercises" | "configure";

const muscleGroups: { id: MuscleGroup; name: string; icon: string }[] = [
  { id: "legs", name: "Legs", icon: "legs" },
  { id: "arms", name: "Arms", icon: "arms" },
  { id: "chest", name: "Chest", icon: "chest" },
  { id: "back", name: "Back", icon: "back" },
  { id: "core", name: "Core", icon: "core" },
];

const difficultyColors = {
  easy: "bg-primary/20 text-primary",
  medium: "bg-accent/20 text-accent",
  hard: "bg-destructive/20 text-destructive",
};

const difficultyLabels = {
  easy: "Easy",
  medium: "Medium",
  hard: "Hard",
};

export function ManualModeScreen() {
  const {
    setCurrentScreen,
    selectedMuscleGroup,
    setSelectedMuscleGroup,
    setSelectedExercises: setGlobalSelectedExercises
  } = useApp();
  const [step, setStep] = useState<Step>("muscle-group");
  const [selectedExercises, setSelectedExercises] = useState<Exercise[]>([]);
  const [config, setConfig] = useState({
    reps: 12,
    sets: 3,
    restTime: 60,
  });

  const filteredExercises = selectedMuscleGroup
    ? defaultExercises.filter((ex) =>
      ex.targetMuscles.includes(selectedMuscleGroup)
    )
    : defaultExercises;

  const handleMuscleGroupSelect = (group: MuscleGroup) => {
    setSelectedMuscleGroup(group);
    setStep("exercises");
  };

  const handleExerciseToggle = (exercise: Exercise) => {
    setSelectedExercises((prev) => {
      const exists = prev.find((e) => e.id === exercise.id);
      if (exists) {
        return prev.filter((e) => e.id !== exercise.id);
      }
      return [...prev, exercise];
    });
  };

  const handleStartSession = () => {
    // Apply config to selected exercises and set them globally
    const configuredExercises = selectedExercises.map(ex => ({
      ...ex,
      reps: config.reps,
      sets: config.sets,
      restTime: config.restTime,
    }));
    setGlobalSelectedExercises(configuredExercises);
    setCurrentScreen("quick-start");
  };

  const getMuscleGroupIcon = (id: string) => {
    switch (id) {
      case "legs":
        return (
          <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M8 3v6m0 0l-2 12m2-12h2m-2 0L6 9m8-6v6m0 0l2 12m-2-12h-2m2 0l2-3" />
          </svg>
        );
      case "arms":
        return (
          <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M4 12h4l2-4 4 8 2-4h4" />
          </svg>
        );
      case "chest":
        return (
          <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="4" y="6" width="16" height="12" rx="2" />
            <line x1="12" y1="6" x2="12" y2="18" />
          </svg>
        );
      case "back":
        return (
          <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M12 3v18M8 7l4-4 4 4M8 17l4 4 4-4" />
          </svg>
        );
      case "core":
        return (
          <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="6" y="4" width="12" height="16" rx="2" />
            <line x1="6" y1="8" x2="18" y2="8" />
            <line x1="6" y1="12" x2="18" y2="12" />
            <line x1="6" y1="16" x2="18" y2="16" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen pb-24 pt-16">
      {/* Header */}
      <div className="fixed top-12 left-0 right-0 z-40 glass-panel px-4 py-3">
        <div className="flex items-center gap-4 max-w-4xl mx-auto">
          <button
            onClick={() => {
              if (step === "muscle-group") {
                setCurrentScreen("home");
              } else if (step === "exercises") {
                setStep("muscle-group");
              } else {
                setStep("exercises");
              }
            }}
            className="p-2 rounded-xl hover:bg-muted/50 transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-foreground" />
          </button>
          <div>
            <h1 className="text-lg font-semibold text-foreground">
              Manual Mode
            </h1>
            <p className="text-xs text-muted-foreground">
              {step === "muscle-group" && "Choose your target"}
              {step === "exercises" && "Select your exercises"}
              {step === "configure" && "Configure your session"}
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 pt-20">
        {/* Step 1: Muscle Group Selection */}
        {step === "muscle-group" && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {muscleGroups.map((group) => (
              <GlassCard
                key={group.id}
                hover
                onClick={() => handleMuscleGroupSelect(group.id)}
                className="group"
              >
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-2xl bg-primary/10 group-hover:bg-primary/20 flex items-center justify-center transition-colors text-primary">
                    {getMuscleGroupIcon(group.id)}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-foreground">
                      {group.name}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {
                        defaultExercises.filter((e) =>
                          e.targetMuscles.includes(group.id)
                        ).length
                      }{" "}
                      exercises
                    </p>
                  </div>
                </div>
              </GlassCard>
            ))}
          </div>
        )}

        {/* Step 2: Exercise Selection */}
        {step === "exercises" && (
          <>
            <div className="grid gap-3 mb-6">
              {filteredExercises.map((exercise) => {
                const isSelected = selectedExercises.some(
                  (e) => e.id === exercise.id
                );
                return (
                  <GlassCard
                    key={exercise.id}
                    hover
                    onClick={() => handleExerciseToggle(exercise)}
                    className={cn(
                      "transition-all",
                      isSelected && "ring-2 ring-primary"
                    )}
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={cn(
                          "w-10 h-10 rounded-xl flex items-center justify-center transition-colors",
                          isSelected
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted"
                        )}
                      >
                        {isSelected ? (
                          <Check className="w-5 h-5" />
                        ) : (
                          <span className="text-lg font-bold text-muted-foreground">
                            {exercise.name[0]}
                          </span>
                        )}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-foreground">
                          {exercise.name}
                        </h4>
                        <div className="flex items-center gap-2 mt-1">
                          <span
                            className={cn(
                              "text-xs px-2 py-0.5 rounded-full",
                              difficultyColors[exercise.difficulty]
                            )}
                          >
                            {difficultyLabels[exercise.difficulty]}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {exercise.targetMuscles.join(", ")}
                          </span>
                        </div>
                      </div>
                    </div>
                  </GlassCard>
                );
              })}
            </div>

            {selectedExercises.length > 0 && (
              <div className="fixed bottom-24 left-4 right-4 md:left-auto md:right-4 md:w-80">
                <GlassCard>
                  <p className="text-sm text-muted-foreground mb-3">
                    {selectedExercises.length} exercise
                    {selectedExercises.length > 1 ? "s" : ""} selected
                  </p>
                  <button
                    onClick={() => setStep("configure")}
                    className={cn(
                      "w-full py-3 rounded-xl font-medium transition-all",
                      "bg-primary text-primary-foreground",
                      "hover:opacity-90 active:scale-[0.98]"
                    )}
                  >
                    Continue
                  </button>
                </GlassCard>
              </div>
            )}
          </>
        )}

        {/* Step 3: Configuration */}
        {step === "configure" && (
          <>
            <GlassCard className="mb-4">
              <h3 className="text-lg font-semibold text-foreground mb-4">
                Configuration
              </h3>

              <div className="mb-6 h-64 rounded-2xl overflow-hidden relative">
                <CameraFeed
                  className="w-full h-full"
                  mirror={true}
                />
              </div>

              <div className="space-y-6">
                {/* Reps */}
                <div>
                  <label className="text-sm text-muted-foreground mb-2 block">
                    Reps per set
                  </label>
                  <div className="flex items-center gap-4">
                    <button
                      onClick={() =>
                        setConfig((c) => ({
                          ...c,
                          reps: Math.max(1, c.reps - 1),
                        }))
                      }
                      className="p-3 rounded-xl bg-muted hover:bg-muted/80 transition-colors"
                    >
                      <Minus className="h-5 w-5" />
                    </button>
                    <span className="text-3xl font-bold text-foreground w-16 text-center">
                      {config.reps}
                    </span>
                    <button
                      onClick={() =>
                        setConfig((c) => ({ ...c, reps: c.reps + 1 }))
                      }
                      className="p-3 rounded-xl bg-muted hover:bg-muted/80 transition-colors"
                    >
                      <Plus className="h-5 w-5" />
                    </button>
                  </div>
                </div>

                {/* Sets */}
                <div>
                  <label className="text-sm text-muted-foreground mb-2 block">
                    Number of sets
                  </label>
                  <div className="flex items-center gap-4">
                    <button
                      onClick={() =>
                        setConfig((c) => ({
                          ...c,
                          sets: Math.max(1, c.sets - 1),
                        }))
                      }
                      className="p-3 rounded-xl bg-muted hover:bg-muted/80 transition-colors"
                    >
                      <Minus className="h-5 w-5" />
                    </button>
                    <span className="text-3xl font-bold text-foreground w-16 text-center">
                      {config.sets}
                    </span>
                    <button
                      onClick={() =>
                        setConfig((c) => ({ ...c, sets: c.sets + 1 }))
                      }
                      className="p-3 rounded-xl bg-muted hover:bg-muted/80 transition-colors"
                    >
                      <Plus className="h-5 w-5" />
                    </button>
                  </div>
                </div>

                {/* Rest Time */}
                <div>
                  <label className="text-sm text-muted-foreground mb-2 block">
                    Rest time (seconds)
                  </label>
                  <div className="flex items-center gap-4">
                    <button
                      onClick={() =>
                        setConfig((c) => ({
                          ...c,
                          restTime: Math.max(15, c.restTime - 15),
                        }))
                      }
                      className="p-3 rounded-xl bg-muted hover:bg-muted/80 transition-colors"
                    >
                      <Minus className="h-5 w-5" />
                    </button>
                    <span className="text-3xl font-bold text-foreground w-16 text-center">
                      {config.restTime}
                    </span>
                    <button
                      onClick={() =>
                        setConfig((c) => ({ ...c, restTime: c.restTime + 15 }))
                      }
                      className="p-3 rounded-xl bg-muted hover:bg-muted/80 transition-colors"
                    >
                      <Plus className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            </GlassCard>

            {/* Selected exercises summary */}
            <GlassCard className="mb-4">
              <h3 className="text-sm font-semibold text-foreground mb-3">
                Selected exercises
              </h3>
              <div className="space-y-2">
                {selectedExercises.map((ex, i) => (
                  <div
                    key={ex.id}
                    className="flex items-center gap-3 py-2 border-b border-border/30 last:border-0"
                  >
                    <span className="w-6 h-6 rounded-full bg-primary/20 text-primary text-xs flex items-center justify-center font-medium">
                      {i + 1}
                    </span>
                    <span className="text-sm text-foreground">{ex.name}</span>
                  </div>
                ))}
              </div>
            </GlassCard>

            <button
              onClick={handleStartSession}
              className={cn(
                "w-full py-4 rounded-xl font-medium transition-all",
                "bg-primary text-primary-foreground",
                "hover:opacity-90 active:scale-[0.98]"
              )}
            >
              Start Session
            </button>
          </>
        )}
      </div>
    </div>
  );
}

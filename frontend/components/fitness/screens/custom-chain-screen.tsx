"use client";

import React from "react"

import { useApp, Exercise, defaultExercises } from "@/lib/app-context";
import { GlassCard } from "@/components/fitness/glass-card";
import { useState } from "react";
import {
  ArrowLeft,
  Plus,
  GripVertical,
  Trash2,
  Play,
  Clock,
  RotateCcw,
  Target,
} from "lucide-react";
import { cn } from "@/lib/utils";

export function CustomChainScreen() {
  const { setCurrentScreen, customChain, setCustomChain } = useApp();
  const [showExerciseList, setShowExerciseList] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  const handleAddExercise = (exercise: Exercise) => {
    setCustomChain((prev) => [
      ...prev,
      { ...exercise, id: `${exercise.id}-${Date.now()}` },
    ]);
    setShowExerciseList(false);
  };

  const handleRemoveExercise = (index: number) => {
    setCustomChain((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === index) return;

    setCustomChain((prev) => {
      const newChain = [...prev];
      const [removed] = newChain.splice(draggedIndex, 1);
      newChain.splice(index, 0, removed);
      return newChain;
    });
    setDraggedIndex(index);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  const totalDuration = customChain.reduce((acc, ex) => {
    const exerciseTime = ex.sets * ex.reps * 3; // ~3 seconds per rep
    const restTime = (ex.sets - 1) * ex.restTime;
    return acc + exerciseTime + restTime;
  }, 0);

  const totalReps = customChain.reduce((acc, ex) => acc + ex.sets * ex.reps, 0);

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
          <div className="flex-1">
            <h1 className="text-lg font-semibold text-foreground">
              Programme personnalisé
            </h1>
            <p className="text-xs text-muted-foreground">
              Glissez pour réorganiser
            </p>
          </div>
          {customChain.length > 0 && (
            <button
              onClick={() => setCustomChain([])}
              className="p-2 rounded-xl hover:bg-destructive/20 text-destructive transition-colors"
            >
              <RotateCcw className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 pt-20">
        {/* Stats summary */}
        {customChain.length > 0 && (
          <div className="grid grid-cols-2 gap-3 mb-6">
            <GlassCard className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-secondary/10 flex items-center justify-center">
                <Clock className="h-5 w-5 text-secondary" />
              </div>
              <div>
                <p className="text-lg font-bold text-foreground">
                  {Math.ceil(totalDuration / 60)} min
                </p>
                <p className="text-xs text-muted-foreground">Durée estimée</p>
              </div>
            </GlassCard>
            <GlassCard className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                <Target className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-lg font-bold text-foreground">{totalReps}</p>
                <p className="text-xs text-muted-foreground">Reps totales</p>
              </div>
            </GlassCard>
          </div>
        )}

        {/* Exercise chain */}
        <div className="space-y-3 mb-6">
          {customChain.map((exercise, index) => (
            <div
              key={exercise.id}
              draggable
              onDragStart={() => handleDragStart(index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragEnd={handleDragEnd}
              className={cn(
                "relative",
                draggedIndex === index && "opacity-50"
              )}
            >
              {/* Timeline connector */}
              {index < customChain.length - 1 && (
                <div className="absolute left-7 top-full w-0.5 h-3 bg-border z-0" />
              )}

              <GlassCard className="relative z-10">
                <div className="flex items-center gap-3">
                  {/* Drag handle */}
                  <div className="cursor-grab active:cursor-grabbing p-1 text-muted-foreground hover:text-foreground transition-colors">
                    <GripVertical className="h-5 w-5" />
                  </div>

                  {/* Exercise number */}
                  <div className="w-8 h-8 rounded-full bg-primary/20 text-primary text-sm flex items-center justify-center font-bold">
                    {index + 1}
                  </div>

                  {/* Exercise info */}
                  <div className="flex-1">
                    <h4 className="font-medium text-foreground">
                      {exercise.name}
                    </h4>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
                      <span>{exercise.reps} reps</span>
                      <span>{exercise.sets} séries</span>
                      <span>{exercise.restTime}s repos</span>
                    </div>
                  </div>

                  {/* Delete button */}
                  <button
                    onClick={() => handleRemoveExercise(index)}
                    className="p-2 rounded-xl hover:bg-destructive/20 text-muted-foreground hover:text-destructive transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </GlassCard>
            </div>
          ))}

          {/* Add exercise button */}
          <button
            onClick={() => setShowExerciseList(true)}
            className={cn(
              "w-full py-4 rounded-2xl border-2 border-dashed border-primary/30 transition-all",
              "flex items-center justify-center gap-2",
              "text-primary hover:bg-primary/5 hover:border-primary/50"
            )}
          >
            <Plus className="h-5 w-5" />
            <span className="font-medium">Ajouter un exercice</span>
          </button>
        </div>

        {/* Empty state */}
        {customChain.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mx-auto mb-4">
              <Plus className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">
              Commencez votre programme
            </h3>
            <p className="text-sm text-muted-foreground max-w-xs mx-auto">
              {
                "Ajoutez des exercices et organisez-les dans l'ordre souhaité"
              }
            </p>
          </div>
        )}

        {/* Start button */}
        {customChain.length > 0 && (
          <button
            onClick={() => setCurrentScreen("quick-start")}
            className={cn(
              "w-full py-4 rounded-xl font-medium transition-all",
              "bg-primary text-primary-foreground",
              "hover:opacity-90 active:scale-[0.98]",
              "flex items-center justify-center gap-2"
            )}
          >
            <Play className="h-5 w-5" />
            Lancer le programme
          </button>
        )}
      </div>

      {/* Exercise list modal */}
      {showExerciseList && (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
          <div className="absolute bottom-0 left-0 right-0 max-h-[70vh] overflow-y-auto rounded-t-3xl bg-card border-t border-border">
            <div className="sticky top-0 bg-card px-4 py-4 border-b border-border">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-foreground">
                  Ajouter un exercice
                </h3>
                <button
                  onClick={() => setShowExerciseList(false)}
                  className="p-2 rounded-xl hover:bg-muted transition-colors text-muted-foreground"
                >
                  <ArrowLeft className="h-5 w-5" />
                </button>
              </div>
            </div>
            <div className="p-4 space-y-2">
              {defaultExercises.map((exercise) => (
                <button
                  key={exercise.id}
                  onClick={() => handleAddExercise(exercise)}
                  className="w-full p-4 rounded-xl bg-muted/50 hover:bg-muted transition-colors text-left"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                      <span className="text-lg font-bold text-primary">
                        {exercise.name[0]}
                      </span>
                    </div>
                    <div>
                      <h4 className="font-medium text-foreground">
                        {exercise.name}
                      </h4>
                      <p className="text-xs text-muted-foreground">
                        {exercise.targetMuscles.join(", ")}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

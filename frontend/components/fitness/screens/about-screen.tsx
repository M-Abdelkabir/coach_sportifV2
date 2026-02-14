"use client";

import { useApp } from "@/lib/app-context";
import { GlassCard } from "@/components/fitness/glass-card";
import { SkeletonOverlay } from "@/components/fitness/skeleton-overlay";
import { ArrowLeft, Laptop, Tablet, Cpu, Eye, Zap, Target } from "lucide-react";
import { cn } from "@/lib/utils";

export function AboutScreen() {
  const { setCurrentScreen } = useApp();

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
              Technology & Vision
            </h1>
            <p className="text-xs text-muted-foreground">
              How the AI works
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 pt-20">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-4 text-balance">
            A smart coach, powered by computer vision
          </h2>
          <p className="text-muted-foreground max-w-xl mx-auto">
            {
              "Our technology analyzes every movement in real-time to offer you personalized and precise coaching."
            }
          </p>
        </div>

        {/* Feature 1: Real-time Analysis */}
        <GlassCard className="mb-6">
          <div className="grid md:grid-cols-2 gap-6 items-center">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
                <Eye className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                Real-time Analysis
              </h3>
              <p className="text-muted-foreground">
                {
                  "Our AI detects every movement, angle, and posture. The skeleton is reconstructed in real-time for maximum precision."
                }
              </p>
            </div>
            <div className="relative h-48 flex items-center justify-center bg-muted/30 rounded-2xl overflow-hidden">
              <div className="w-32 h-44">
                <SkeletonOverlay
                  animate
                  joints={{
                    head: "perfect",
                    leftShoulder: "perfect",
                    rightShoulder: "perfect",
                    leftElbow: "warning",
                    rightElbow: "perfect",
                    leftWrist: "perfect",
                    rightWrist: "perfect",
                    leftHip: "perfect",
                    rightHip: "perfect",
                    leftKnee: "perfect",
                    rightKnee: "perfect",
                    leftAnkle: "perfect",
                    rightAnkle: "perfect",
                  }}
                />
              </div>
              {/* Scanning effect */}
              <div className="absolute inset-0 bg-gradient-to-b from-primary/10 via-transparent to-primary/10 animate-pulse" />
            </div>
          </div>
        </GlassCard>

        {/* Feature 2: Personalized Calibration */}
        <GlassCard className="mb-6">
          <div className="grid md:grid-cols-2 gap-6 items-center">
            <div className="order-2 md:order-1 relative h-48 flex items-center justify-center bg-muted/30 rounded-2xl overflow-hidden">
              {/* Body mapping visualization */}
              <div className="relative">
                <div className="w-24 h-32 border-2 border-dashed border-primary/50 rounded-full flex items-center justify-center">
                  <div className="space-y-2">
                    <div className="h-1 w-12 bg-primary/60 rounded" />
                    <div className="h-1 w-16 bg-secondary/60 rounded" />
                    <div className="h-1 w-20 bg-accent/60 rounded" />
                  </div>
                </div>
                {/* Measurement lines */}
                <div className="absolute -left-8 top-1/2 w-6 h-0.5 bg-primary/40" />
                <div className="absolute -right-8 top-1/2 w-6 h-0.5 bg-primary/40" />
                <div className="absolute left-1/2 -top-6 h-4 w-0.5 bg-secondary/40" />
                <div className="absolute left-1/2 -bottom-6 h-4 w-0.5 bg-accent/40" />
              </div>
            </div>
            <div className="order-1 md:order-2">
              <div className="w-12 h-12 rounded-2xl bg-secondary/10 flex items-center justify-center mb-4">
                <Target className="h-6 w-6 text-secondary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                Personalized Calibration
              </h3>
              <p className="text-muted-foreground">
                {
                  "Every morphology is unique. Our thresholds automatically adapt to your body for precise measurements and relevant feedback."
                }
              </p>
            </div>
          </div>
        </GlassCard>

        {/* Feature 3: Instant Feedback */}
        <GlassCard className="mb-6">
          <div className="grid md:grid-cols-2 gap-6 items-center">
            <div>
              <div className="w-12 h-12 rounded-2xl bg-accent/10 flex items-center justify-center mb-4">
                <Zap className="h-6 w-6 text-accent" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                Instant Feedback
              </h3>
              <p className="text-muted-foreground">
                {
                  "Immediate corrections to progress faster and avoid injuries. Every repetition is analyzed and scored."
                }
              </p>
            </div>
            <div className="relative h-48 flex flex-col items-center justify-center gap-3 bg-muted/30 rounded-2xl p-4">
              {/* Feedback simulation */}
              <div
                className={cn(
                  "w-full p-3 rounded-xl text-center text-sm font-medium",
                  "bg-primary/20 text-primary"
                )}
              >
                Perfect posture
              </div>
              <div
                className={cn(
                  "w-full p-3 rounded-xl text-center text-sm font-medium",
                  "bg-accent/20 text-accent"
                )}
              >
                Go down slower
              </div>
              <div
                className={cn(
                  "w-full p-3 rounded-xl text-center text-sm font-medium",
                  "bg-destructive/20 text-destructive"
                )}
              >
                Watch your back
              </div>
            </div>
          </div>
        </GlassCard>

        {/* Platforms */}
        <GlassCard>
          <h3 className="text-xl font-semibold text-foreground mb-6 text-center">
            Compatible Platforms
          </h3>
          <p className="text-muted-foreground text-center mb-8">
            {
              "Optimized for all your screens, from desktop to embedded lab."
            }
          </p>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-3">
                <Laptop className="h-8 w-8 text-primary" />
              </div>
              <h4 className="font-medium text-foreground">Laptop</h4>
              <p className="text-xs text-muted-foreground mt-1">
                Full experience
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-secondary/10 flex items-center justify-center mx-auto mb-3">
                <Tablet className="h-8 w-8 text-secondary" />
              </div>
              <h4 className="font-medium text-foreground">Tablet</h4>
              <p className="text-xs text-muted-foreground mt-1">
                Optimal mobility
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center mx-auto mb-3">
                <Cpu className="h-8 w-8 text-accent" />
              </div>
              <h4 className="font-medium text-foreground">Raspberry Pi</h4>
              <p className="text-xs text-muted-foreground mt-1">
                Embedded system
              </p>
            </div>
          </div>
        </GlassCard>

        {/* Tech specs */}
        <div className="mt-8 text-center text-sm text-muted-foreground">
          <p>Computer Vision • Pose Detection • Biomechanical Analysis</p>
          <p className="mt-1">Optimized for 30+ FPS on all devices</p>
        </div>
      </div>
    </div>
  );
}

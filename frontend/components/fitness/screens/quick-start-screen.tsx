"use client";

import { useApp, defaultExercises } from "@/lib/app-context";
import { useWebSocket, useExercise, useFeedback, useKeypoints, useVoice, useHardware } from "@/lib/use-backend";
import { GlassCard } from "@/components/fitness/glass-card";
import { SkeletonOverlay } from "@/components/fitness/skeleton-overlay";
import { ProgressRing } from "@/components/fitness/progress-ring";
import { CameraFeed } from "@/components/fitness/camera-feed";
import { PositionFeedbackPanel, QuickPositionStatus } from "@/components/fitness/position-feedback-panel";
import { useState, useEffect, useCallback } from "react";
import {
  Pause,
  Play,
  SkipForward,
  Dumbbell,
  Zap,
  Info,
  X,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

type JointStatus = "perfect" | "warning" | "error";

export function QuickStartScreen() {
  const {
    setCurrentScreen,
    setIsSessionActive,
    setCameraConnected,
    setFps,
    postureStatus,
    setPostureStatus,
    postureFeedback,
    setPostureFeedback,
    customChain,
    selectedExercises,
    userProfile,
    cameraStream,
    isDebugMode,
    useBackendPose,
  } = useApp();

  // Backend Integration
  const { isConnected, startSession, stopSession, pause, resume, selectExercise } = useWebSocket();
  const { keypoints } = useKeypoints();
  const exerciseState = useExercise();
  const feedbackState = useFeedback();
  const hardware = useHardware();
  const { speak } = useVoice(); // Activates voice feedback

  // ML Classification from backend (available from exerciseState)
  const mlClass = exerciseState?.mlClass;
  const mlConf = exerciseState?.mlConfidence;

  const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
  const [currentReps, setCurrentReps] = useState(0);
  const [currentSet, setCurrentSet] = useState(1);
  const [isPaused, setIsPaused] = useState(false);
  const [isResting, setIsResting] = useState(false);
  const [restTime, setRestTime] = useState(0);
  const [sessionComplete, setSessionComplete] = useState(false);
  const [sessionResults, setSessionResults] = useState<{ reps: number; sets: number; calories: number } | null>(null);
  const [joints, setJoints] = useState<Record<string, JointStatus>>({
    head: "perfect",
    leftShoulder: "perfect",
    rightShoulder: "perfect",
    leftElbow: "perfect",
    rightElbow: "perfect",
    leftWrist: "perfect",
    rightWrist: "perfect",
    leftHip: "perfect",
    rightHip: "perfect",
    leftKnee: "perfect",
    rightKnee: "perfect",
    leftAnkle: "perfect",
    rightAnkle: "perfect",
  });

  // Exercises list
  const exercises = customChain.length > 0
    ? customChain
    : selectedExercises.length > 0
      ? selectedExercises
      : defaultExercises.slice(0, 4);
  const currentExercise = exercises[currentExerciseIndex];
  const totalSets = currentExercise?.sets || 3;
  const targetReps = currentExercise?.reps || 15;
  const totalExercises = exercises.length;

  useEffect(() => {
    setIsSessionActive(true);
    return () => setIsSessionActive(false);
  }, [setIsSessionActive]);

  // Sync state with backend exercise state
  useEffect(() => {
    if (exerciseState) {
      setCurrentReps(exerciseState.repCount);
      setCurrentSet(exerciseState.setCount);
    }
  }, [exerciseState]);

  useEffect(() => {
    // Update posture status from feedback
    if (feedbackState) {
      setPostureStatus(feedbackState.status as "perfect" | "warning" | "error");
      setPostureFeedback(feedbackState.message);

      // Update joints based on issues
      setJoints(prev => {
        const newJoints = { ...prev };
        Object.keys(newJoints).forEach(k => newJoints[k] = "perfect");

        if (feedbackState.issues) {
          feedbackState.issues.forEach(issue => {
            if (issue.includes('knee')) {
              newJoints.leftKnee = "warning";
              newJoints.rightKnee = "warning";
            }
            if (issue.includes('back') || issue.includes('hip')) {
              newJoints.leftHip = "warning";
              newJoints.rightHip = "warning";
            }
            if (issue.includes('elbow')) {
              newJoints.leftElbow = "warning";
              newJoints.rightElbow = "warning";
            }
          });
        }
        return newJoints;
      });
    } else {
      // Clear UI when feedback is null
      setPostureFeedback("");
      setPostureStatus("perfect");
      setJoints(prev => {
        const newJoints = { ...prev };
        Object.keys(newJoints).forEach(k => newJoints[k] = "perfect");
        return newJoints;
      });
    }
  }, [feedbackState, setPostureStatus, setPostureFeedback]);

  // Handle session start and events
  useEffect(() => {
    if (!isConnected) return;

    const exerciseIds = exercises.map(e => e.id);
    startSession(userProfile?.id || "demo_user", exerciseIds);

    const { wsManager } = require("@/lib/api-client");

    const unsubSet = wsManager.on("set_complete", (msg: any) => {
      setIsResting(true);
      setRestTime(60);
    });

    const unsubExChange = wsManager.on("exercise_change", (msg: any) => {
      const isImmediate = msg.data?.immediate === true;

      if (isImmediate) {
        setIsResting(false);
        setRestTime(0);
      } else {
        setIsResting(true);
        setRestTime(60);
      }

      if (msg.data && typeof msg.data.index === 'number') {
        setCurrentExerciseIndex(msg.data.index);
        // No need to call selectExercise here as it's coming from backend
      }
    });

    const unsubSessionStop = wsManager.on("session_stopped", (msg: any) => {
      console.log("[WS] Session stopped message received:", msg);
      if (msg.data) {
        setSessionResults({
          reps: msg.data.total_reps || 0,
          sets: msg.data.total_sets || 1,
          calories: msg.data.calories || 0
        });
      }
      setSessionComplete(true);
    });

    return () => {
      unsubSet();
      unsubExChange();
      unsubSessionStop();
    };
  }, [isConnected, startSession, userProfile, exercises]);

  // Rest timer
  useEffect(() => {
    if (!isResting || restTime <= 0) return;

    const timer = setInterval(() => {
      setRestTime((prev) => {
        if (prev <= 1) {
          setIsResting(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isResting, restTime]);

  const handleStop = useCallback(() => {
    stopSession();
    setIsSessionActive(false);
    setCurrentScreen("home");
  }, [stopSession, setIsSessionActive, setCurrentScreen]);

  const handleSkip = useCallback(() => {
    if (isResting) {
      setIsResting(false);
      setRestTime(0);
    } else if (currentExerciseIndex < totalExercises - 1) {
      // Go to next exercise
      const nextIdx = currentExerciseIndex + 1;
      setCurrentExerciseIndex(nextIdx);
      setCurrentReps(0);
      setCurrentSet(1);

      // Notify backend about exercise switch
      selectExercise(nextIdx);
    } else {
      // Last exercise, end session
      stopSession();
      setSessionComplete(true);
    }
  }, [isResting, currentExerciseIndex, totalExercises, selectExercise]);

  // Progress calculations
  const progress = exerciseState.repCount && exerciseState.targetReps
    ? (exerciseState.repCount / exerciseState.targetReps) * 100
    : 0;

  const setProgress = exerciseState.setCount && exerciseState.targetSets
    ? ((exerciseState.setCount - 1) / exerciseState.targetSets) * 100 + (progress / exerciseState.targetSets)
    : 0;

  // Get feedback style
  const getFeedbackConfig = () => {
    switch (postureStatus) {
      case "perfect":
        return { icon: Zap, color: "text-primary", bg: "bg-primary/20", border: "border-primary" };
      case "warning":
        return { icon: Info, color: "text-amber-500", bg: "bg-amber-500/20", border: "border-amber-500" };
      case "error":
        return { icon: Info, color: "text-destructive", bg: "bg-destructive/20", border: "border-destructive" };
      default:
        return { icon: Zap, color: "text-primary", bg: "bg-primary/20", border: "border-primary" };
    }
  };

  const feedbackConfig = getFeedbackConfig();
  const FeedbackIcon = feedbackConfig.icon;

  return (
    <div className="relative h-screen w-screen bg-black overflow-hidden">
      {/* Fullscreen Camera Background */}
      {/* Fullscreen Camera Background with Aspect Ratio Constraint */}
      <div className="absolute inset-0 z-0 flex items-center justify-center bg-zinc-900">
        {/* Dataset is 800x600 (4:3), so we constrain the view to matches detection coordinates */}
        <div className="relative aspect-[4/3] h-full max-w-full w-auto">
          <CameraFeed
            mirror={true}
            onCameraStatus={setCameraConnected}
            onFpsUpdate={setFps}
            className="w-full h-full"
          />

          {/* Skeleton overlay - matching the camera perfectly */}
          <SkeletonOverlay
            joints={joints}
            backendJoints={keypoints?.keypoints}
            animate={!isPaused && !isResting}
            mirror={true}
            debug={isDebugMode}
            className="absolute inset-0 pointer-events-none drop-shadow-[0_0_20px_rgba(0,0,0,0.5)]"
          />
        </div>
      </div>

      {/* Overlay UI */}
      <div className="absolute inset-0 z-10 p-4 md:p-6 flex flex-col justify-between pointer-events-none">

        {/* Top Bar - Exercise Progress */}
        <div className="flex justify-between items-start pointer-events-none">
          {/* Exercise Info */}
          <div className="flex flex-col gap-2 backdrop-blur-md bg-black/40 rounded-2xl p-4 pointer-events-auto">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-full ${feedbackConfig.bg} ${feedbackConfig.color}`}>
                <Dumbbell size={20} />
              </div>
              <div>
                <div className="text-xs text-gray-300">Exercise {currentExerciseIndex + 1}/{totalExercises}</div>
                <div className="font-bold text-xl leading-none text-white">
                  {currentExercise?.name || "No Exercise"}
                </div>
              </div>
            </div>

            {/* Set Counter */}
            <div className="flex items-center gap-4 mt-2">
              <div className="text-sm text-gray-300">
                Set <span className="font-bold text-white text-lg">{currentSet}</span>
                <span className="text-gray-400">/{totalSets}</span>
              </div>

              {/* Next Exercise Preview */}
              {currentExerciseIndex < totalExercises - 1 && (
                <div className="flex items-center gap-2 text-sm text-gray-300">
                  <span>Next:</span>
                  <span className="text-white font-medium">
                    {exercises[currentExerciseIndex + 1]?.name}
                  </span>
                  <ChevronRight size={16} />
                </div>
              )}
            </div>

            {/* Position Status Badge */}
            {mlClass && (
              <div className="mt-2">
                <QuickPositionStatus
                  status={postureStatus as any}
                  mlClass={mlClass}
                  mlConfidence={mlConf}
                />
              </div>
            )}
          </div>

          {/* Stop Button */}
          <button
            onClick={handleStop}
            className="bg-destructive/80 hover:bg-destructive text-white p-3 rounded-xl backdrop-blur-md transition-colors pointer-events-auto"
          >
            <X size={24} />
          </button>
        </div>

        {/* Center Rest Timer (Only during rest) */}
        {isResting && (
          <div className="self-center pointer-events-auto">
            <div className="flex flex-col items-center gap-6">
              <div className="glass-panel p-8 rounded-full aspect-square flex flex-col items-center justify-center animate-pulse border-2 border-primary">
                <span className="text-sm text-primary uppercase font-bold tracking-widest">REST</span>
                <span className="text-7xl font-bold font-mono text-white mt-2">{restTime}s</span>
              </div>

              {/* Next Exercise Info */}
              <div className="text-center">
                <div className="text-gray-300 text-sm mb-1">Up Next</div>
                <div className="text-white text-xl font-bold">
                  {exercises[currentExerciseIndex + 1]?.name || "End of Session"}
                </div>
                <button
                  onClick={() => {
                    setIsResting(false);
                    setRestTime(0);
                    resume(); // Call backend resume which now resets session_resting
                  }}
                  className="mt-4 px-6 py-2 bg-primary/20 text-primary rounded-lg hover:bg-primary/30 transition-colors text-sm"
                >
                  Skip Rest
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Bottom Panel - Stats & Controls */}
        <div className="flex items-end justify-between pointer-events-none">
          {/* Enhanced Feedback Panel with Speech Corrections */}
          <div className="max-w-lg pointer-events-auto">
            <PositionFeedbackPanel
              status={postureStatus as "perfect" | "warning" | "error"}
              message={postureFeedback || "Perfect Posture"}
              mlClass={mlClass}
              mlConfidence={mlConf}
              formIssues={feedbackState?.issues}
              onSpeak={speak}
              animated={!isPaused && !isResting}
              className="w-full"
            />
          </div>

          {/* Rep Counter & Skip Button */}
          <div className="flex flex-col items-end gap-4 pointer-events-auto">
            {/* Rep Counter */}
            <div className="relative">
              <ProgressRing progress={progress} size={140} strokeWidth={10} className="drop-shadow-lg">
                <div className="flex flex-col items-center justify-center">
                  <span className="text-5xl font-bold text-white">{currentReps}</span>
                  <span className="text-sm text-gray-300">REPS</span>
                  <div className="text-xs text-gray-400 mt-1">
                    Target: {targetReps}
                  </div>
                </div>
              </ProgressRing>
            </div>

            {/* Skip Button */}
            <button
              onClick={handleSkip}
              className="flex items-center gap-2 px-4 py-3 rounded-xl bg-white/10 text-white hover:bg-white/20 transition-colors backdrop-blur-md"
            >
              <SkipForward size={18} />
              <span>{isResting ? "Skip Rest" : "Skip Exercise"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Safety Overlay */}
      {hardware && (hardware.heart_rate_warning || hardware.imu_tremor_detected) && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-destructive/60 backdrop-blur-md animate-in fade-in duration-300 pointer-events-auto">
          <div className="text-center p-8 glass-panel border-4 border-white">
            <div className="w-24 h-24 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-6">
              <Zap className="w-12 h-12 text-white fill-white" />
            </div>
            <h2 className="text-4xl font-extrabold text-white mb-2 uppercase tracking-tighter">
              Safety Warning
            </h2>
            <p className="text-xl text-white font-medium mb-6">
              {hardware.heart_rate_warning
                ? "HEART RATE TOO HIGH"
                : "UNUSUAL TREMORS DETECTED"}
            </p>
            <div className="bg-white text-destructive font-bold py-4 px-8 rounded-2xl text-2xl shadow-xl">
              STOP EXERCISING IMMEDIATELY
            </div>
          </div>
        </div>
      )}

      {/* Session Complete Overlay */}
      {sessionComplete && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/95 backdrop-blur-md z-20 pointer-events-auto">
          <div className="text-center p-8 max-w-md">
            <div className="w-24 h-24 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-6">
              <svg className="w-12 h-12 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold text-white mb-2">Session Complete!</h2>
            <p className="text-gray-300 mb-2">
              You completed {totalExercises} exercises
            </p>
            <p className="text-gray-400 mb-6 font-medium">
              Total sets: {sessionResults?.sets || currentSet} | Total reps: {sessionResults?.reps || currentReps}
              {sessionResults?.calories ? ` | Calories: ${sessionResults.calories.toFixed(3)} kcal` : ""}
            </p>
            <button
              onClick={handleStop}
              className="px-8 py-4 rounded-xl bg-primary text-white font-medium hover:bg-primary/90 transition-colors text-lg w-full"
            >
              Back to Home
            </button>
          </div>
        </div>
      )}

      {/* Connection Status */}
      {!isConnected && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 px-4 py-2 bg-destructive/80 text-white rounded-full text-sm backdrop-blur-md">
          Backend Disconnected
        </div>
      )}
    </div>
  );
}
"use client";

import { useApp } from "@/lib/app-context";
import { useWebSocket, useCalibration } from "@/lib/use-backend"; // Added backend hooks
import { GlassCard } from "@/components/fitness/glass-card";
import { SkeletonOverlay } from "@/components/fitness/skeleton-overlay";
import { CameraFeed } from "@/components/fitness/camera-feed";
import { useState, useEffect } from "react";
import { ArrowLeft, Check, AlertCircle, User } from "lucide-react"; // Added User icon
import { cn } from "@/lib/utils";

type CalibrationStep = "waiting" | "countdown" | "analyzing" | "complete";

type CheckStatus = "pending" | "checking" | "success" | "error";

export function CalibrationScreen() {
  const { setCurrentScreen, setCalibrationData, setCameraConnected, setFps, userProfile, setUserProfile,  cameraStream, cameraError } = useApp();
  const { isConnected, connect, startCalibration } = useWebSocket();
  const calibrationState = useCalibration();

  const [step, setStep] = useState<CalibrationStep>("waiting");
  const [countdown, setCountdown] = useState(5);
  const [checks, setChecks] = useState<Record<string, CheckStatus>>({
    shoulders: "pending",
    legs: "pending",
    stability: "pending",
  });

  // Ensure WebSocket connection
  useEffect(() => {
    if (!isConnected) {
      connect();
    }
  }, [isConnected, connect]);

  // Sync component state with backend calibration state
  useEffect(() => {
    if (calibrationState.status === "collecting") {
      setStep("analyzing");
      setChecks(prev => ({ ...prev, stability: "checking" }));
    } else if (calibrationState.status === "complete" && calibrationState.result) {
      setStep("complete");
      setChecks(prev => ({
        shoulders: "success",
        legs: "success",
        stability: "success"
      }));

      // Update global calibration data with body_type
      if (calibrationState.result.ratios) {
        setCalibrationData({
          isCalibrated: true,
          shoulderWidth: calibrationState.result.ratios.shoulder_width || 0,
          armLength: calibrationState.result.ratios.arm_length || 0,
          legLength: calibrationState.result.ratios.leg_length || 0,
          torsoHeight: calibrationState.result.ratios.torso_height || 0,
          body_type: calibrationState.result.body_type || 'unknown', // Add body_type
        });
      }
    }
  }, [calibrationState.status, calibrationState.result, setCalibrationData]);

  // Countdown logic
  useEffect(() => {
    if (step === "countdown" && countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
    if (step === "countdown" && countdown === 0) {
      // Start actual calibration on backend
      const userId = userProfile?.id || "demo_user";
      startCalibration(userId, 5); // 5 seconds calibration
      setStep("analyzing");
    }
  }, [step, countdown, startCalibration, userProfile]);

  const handleStartCalibration = () => {
    setStep("countdown");
    setCountdown(5);
  };

  const handleComplete = () => {
    if (calibrationState.result) {
      setCalibrationData({
        isCalibrated: true,
        shoulderWidth: calibrationState.result.ratios?.shoulder_width || 0,
        armLength: calibrationState.result.ratios?.arm_length || 0,
        legLength: calibrationState.result.ratios?.leg_length || 0,
        torsoHeight: calibrationState.result.ratios?.torso_height || 0,
        body_type: calibrationState.result.body_type || 'unknown', // Add body_type
      });
    }
    setCurrentScreen("home");
  };

  const checkStatusIcon = (status: CheckStatus) => {
    switch (status) {
      case "pending":
        return <div className="w-4 h-4 rounded-full border-2 border-muted-foreground/30" />;
      case "checking":
        return (
          <div className="w-4 h-4 rounded-full border-2 border-primary border-t-transparent animate-spin" />
        );
      case "success":
        return (
          <div className="w-4 h-4 rounded-full bg-primary flex items-center justify-center">
            <Check className="w-3 h-3 text-primary-foreground" />
          </div>
        );
      case "error":
        return (
          <div className="w-4 h-4 rounded-full bg-destructive flex items-center justify-center">
            <AlertCircle className="w-3 h-3 text-destructive-foreground" />
          </div>
        );
    }
  };

  // Get ratios for display
  const displayRatios = calibrationState.result?.ratios || {
    shoulder_width: 0,
    arm_length: 0,
    leg_length: 0,
    torso_height: 0
  };

  return (
    <div className="min-h-screen pb-24 pt-16">
      {/* Back button */}
      <button
        onClick={() => setCurrentScreen("home")}
        className="fixed top-16 left-4 z-40 p-2 rounded-xl glass-card hover:bg-muted/50 transition-colors"
      >
        <ArrowLeft className="h-5 w-5 text-foreground" />
      </button>

      <div className="relative h-[calc(100vh-10rem)]">
        {/* Live camera feed in mirror mode with BACKEND STREAM */}
        <div className="absolute inset-0 overflow-hidden">
          <CameraFeed
            mirror={true}
            onCameraStatus={setCameraConnected}
            onFpsUpdate={setFps}
            className="absolute inset-0"
            useBackendStream={true}
            externalStream={cameraStream}
          />

          {/* Gradient overlays for UI readability */}
          <div className="absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-background/70 to-transparent pointer-events-none" />
          <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-background/80 to-transparent pointer-events-none" />

          {/* T-Pose guide overlay */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="relative w-72 h-96">
              {/* T-Pose silhouette guide */}
              <div className={cn(
                "absolute inset-0 border-2 border-dashed rounded-3xl transition-all duration-500",
                step === "analyzing" ? "border-primary/60" : "border-primary/30"
              )} />

              {/* Skeleton overlay for pose detection visualization */}
              {/* We hide the local skeleton overlay because backend stream already has it */}
              {/* <SkeletonOverlay showTPose animate={step === "analyzing"} className="absolute inset-0 drop-shadow-lg" /> */}

              {/* Target markers for body alignment */}
              {step === "waiting" && (
                <>
                  <div className="absolute top-4 left-1/2 -translate-x-1/2 w-12 h-12 rounded-full border-2 border-dashed border-primary/50 flex items-center justify-center">
                    <div className="w-2 h-2 rounded-full bg-primary/50" />
                  </div>
                  <div className="absolute top-1/3 left-0 w-8 h-8 rounded-full border-2 border-dashed border-primary/50" />
                  <div className="absolute top-1/3 right-0 w-8 h-8 rounded-full border-2 border-dashed border-primary/50" />
                  <div className="absolute bottom-4 left-1/4 w-8 h-8 rounded-full border-2 border-dashed border-primary/50" />
                  <div className="absolute bottom-4 right-1/4 w-8 h-8 rounded-full border-2 border-dashed border-primary/50" />
                </>
              )}
            </div>
          </div>
        </div>

        {/* Countdown overlay */}
        {step === "countdown" && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/60 backdrop-blur-sm">
            <div className="text-center">
              <div className="text-8xl font-bold text-primary glow-energy">
                {countdown}
              </div>
              <p className="text-lg text-foreground mt-4">
                Get into T-Pose position
              </p>
            </div>
          </div>
        )}

        {/* Status Panel */}
        <div className="absolute bottom-8 left-4 right-4 md:left-auto md:right-8 md:w-80">
          <GlassCard>
            {step === "waiting" && (
              <>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  T-Pose Calibration
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {
                    "Stand facing the camera with your arms extended horizontally. Make sure you are clearly visible."
                  }
                </p>
                <div className="flex items-center gap-2 mb-4 text-xs text-amber-500 bg-amber-500/10 p-2 rounded">
                  <AlertCircle className="w-4 h-4" />
                  <span>Backend connected: {isConnected ? "Yes" : "No"}</span>
                </div>
                <button
                  onClick={handleStartCalibration}
                  disabled={!isConnected}
                  className={cn(
                    "w-full py-3 rounded-xl font-medium transition-all",
                    "bg-primary text-primary-foreground",
                    "hover:opacity-90 active:scale-[0.98]",
                    !isConnected && "opacity-50 cursor-not-allowed"
                  )}
                >
                  {"Start Calibration"}
                </button>
              </>
            )}

            {(step === "countdown" || step === "analyzing") && (
              <>
                <h3 className="text-lg font-semibold text-foreground mb-4">
                  {step === "countdown" ? "Get ready..." : "Analysis in progress"}
                </h3>

                {step === "analyzing" && (
                  <div className="w-full bg-muted h-2 rounded-full mb-4 overflow-hidden">
                    <div
                      className="bg-primary h-full transition-all duration-300"
                      style={{ width: `${calibrationState.progress * 100}%` }}
                    />
                  </div>
                )}

                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    {checkStatusIcon(calibrationState.progress > 0.2 ? "success" : "checking")}
                    <span className="text-sm text-foreground">
                      T-Pose Acquisition
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    {checkStatusIcon(calibrationState.progress > 0.5 ? "success" : "pending")}
                    <span className="text-sm text-foreground">
                      Ratio Calculation
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    {checkStatusIcon(calibrationState.progress > 0.8 ? "success" : "pending")}
                    <span className="text-sm text-foreground">
                      Stability Check
                    </span>
                  </div>
                </div>
              </>
            )}

            {step === "complete" && (
              <>
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                    <Check className="w-5 h-5 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold text-primary">
                    Calibration Successful
                  </h3>
                </div>

                <p className="text-sm text-muted-foreground mb-4">
                  Personalized thresholds applied
                </p>

                {/* Body type display - NEW */}
                {calibrationState.result?.body_type && (
                  <div className="mb-4">
                    <h4 className="text-xs font-medium text-muted-foreground mb-2">Detected Body Type</h4>
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-muted/50">
                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <User className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground capitalize">
                          {calibrationState.result.body_type}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Based on your T-pose analysis
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Body ratios */}
                <div className="space-y-3 mb-4">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-muted-foreground">
                        Shoulder Width
                      </span>
                      <span className="text-foreground">
                        {(displayRatios.shoulder_width * 100).toFixed(1)} %
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all duration-500"
                        style={{ width: `${displayRatios.shoulder_width * 100}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-muted-foreground">
                        Arm Length
                      </span>
                      <span className="text-foreground">
                        {(displayRatios.arm_length * 100).toFixed(1)} %
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-secondary rounded-full transition-all duration-500"
                        style={{ width: `${displayRatios.arm_length * 100}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-muted-foreground">
                        Leg/Torso Ratio
                      </span>
                      <span className="text-foreground">
                        {displayRatios.leg_torso_ratio?.toFixed(2) || "N/A"}
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-accent rounded-full transition-all duration-500"
                        style={{ width: `${Math.min((displayRatios.leg_torso_ratio || 0) * 50, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleComplete}
                  className={cn(
                    "w-full py-3 rounded-xl font-medium transition-all",
                    "bg-primary text-primary-foreground",
                    "hover:opacity-90 active:scale-[0.98]"
                  )}
                >
                  Continue
                </button>
              </>
            )}
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, AlertCircle, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { useFeedback, useExercise } from "@/lib/use-backend";

interface PositionValidatorProps {
  className?: string;
}

interface PositionStatus {
  status: "good" | "bad" | "warning" | "neutral";
  message: string;
  mlClass?: string | null;
  mlConfidence?: number | null;
  timestamp: number;
}

export function PositionValidator({ className }: PositionValidatorProps) {
  const feedback = useFeedback();
  const exercise = useExercise();
  const [positionStatus, setPositionStatus] = useState<PositionStatus>({
    status: "neutral",
    message: "Position en attente",
    timestamp: Date.now(),
  });
  const [isVisible, setIsVisible] = useState(true);
  const [lastSpokenMessage, setLastSpokenMessage] = useState<string>("");

  // Handle feedback and ML classification updates
  useEffect(() => {
    if (!feedback) return;

    const mlClass = feedback.mlClass;
    const status = feedback.status;
    let newStatus: PositionStatus["status"] = "neutral";
    let message = feedback.message;

    // Determine position status based on ML classification
    if (mlClass) {
      if (mlClass.includes("Correct")) {
        newStatus = "good";
        message = `✓ ${mlClass}`;
      } else {
        newStatus = "bad";
        message = `✗ ${mlClass}`;
      }
    } else if (status === "warning") {
      newStatus = "warning";
    } else if (status === "perfect") {
      newStatus = "good";
    }

    // Only update if message is different (to avoid spam)
    const timestamp = Date.now();
    if (message !== positionStatus.message) {
      setPositionStatus({
        status: newStatus,
        message,
        mlClass: feedback.mlClass,
        mlConfidence: feedback.mlConfidence,
        timestamp,
      });

      // Speak the message if it's a correction (bad position)
      if ((newStatus === "bad" || newStatus === "warning") && message !== lastSpokenMessage) {
        speakMessage(message);
        setLastSpokenMessage(message);
      }

      setIsVisible(true);

      // Auto-hide good feedback after 3 seconds
      if (newStatus === "good") {
        const timeout = setTimeout(() => {
          setIsVisible(false);
        }, 3000);
        return () => clearTimeout(timeout);
      }
    }
  }, [feedback, lastSpokenMessage, positionStatus.message]);

  const speakMessage = (text: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;

    // Cancel previous speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "fr-FR";
    utterance.rate = 0.9;
    utterance.pitch = 1.0;

    try {
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.error("Speech synthesis error:", e);
    }
  };

  if (!isVisible) return null;

  const statusConfig = {
    good: {
      bgColor: "bg-emerald-500/20",
      borderColor: "border-emerald-500/50",
      textColor: "text-emerald-500",
      icon: CheckCircle2,
      label: "Bonne Position",
    },
    bad: {
      bgColor: "bg-destructive/20",
      borderColor: "border-destructive/50",
      textColor: "text-destructive",
      icon: AlertCircle,
      label: "Mauvaise Position",
    },
    warning: {
      bgColor: "bg-amber-500/20",
      borderColor: "border-amber-500/50",
      textColor: "text-amber-500",
      icon: AlertCircle,
      label: "Attention",
    },
    neutral: {
      bgColor: "bg-muted/20",
      borderColor: "border-muted/50",
      textColor: "text-muted-foreground",
      icon: AlertCircle,
      label: "Neutre",
    },
  };

  const config = statusConfig[positionStatus.status];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "rounded-2xl border backdrop-blur-sm transition-all duration-300 animate-in fade-in",
        config.bgColor,
        config.borderColor,
        className
      )}
    >
      <div className="p-4 space-y-3">
        {/* Header */}
        <div className="flex items-start gap-3">
          <Icon className={cn("h-5 w-5 mt-0.5 flex-shrink-0", config.textColor)} />
          <div className="flex-1 min-w-0">
            <h3 className={cn("font-semibold text-sm", config.textColor)}>
              {config.label}
            </h3>
            <p className="text-sm text-foreground/80 mt-1 line-clamp-2">
              {positionStatus.message}
            </p>
          </div>
        </div>

        {/* ML Classification Details */}
        {positionStatus.mlClass && positionStatus.mlConfidence !== null && (
          <div className="bg-black/20 rounded-lg p-2.5 space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs text-foreground/70">Analyse IA</span>
              <span className={cn("text-xs font-semibold px-2 py-1 rounded", config.textColor)}>
                {Math.round((positionStatus.mlConfidence ?? 0) * 100)}%
              </span>
            </div>
            <div className="w-full bg-black/30 rounded-full h-1.5 overflow-hidden">
              <div
                className={cn(
                  "h-full transition-all duration-300",
                  positionStatus.status === "good" ? "bg-emerald-500" : "bg-destructive"
                )}
                style={{
                  width: `${((positionStatus.mlConfidence ?? 0) * 100)}%`,
                }}
              />
            </div>
          </div>
        )}

        {/* Exercise Info */}
        {exercise && exercise.exercise !== "unknown" && (
          <div className="text-xs text-foreground/60 space-y-0.5">
            <p>
              <span className="font-medium text-foreground/80">{exercise.exercise.toUpperCase()}</span>
              {" "}
              <span className="text-foreground/60">Rep {exercise.repCount} / {exercise.targetReps}</span>
            </p>
          </div>
        )}

        {/* Action Button for Bad Position */}
        {positionStatus.status === "bad" && (
          <button
            onClick={() => speakMessage(positionStatus.message)}
            className="w-full mt-3 px-3 py-2 bg-destructive/20 hover:bg-destructive/30 rounded-lg text-sm font-medium text-destructive transition-colors flex items-center justify-center gap-2"
          >
            <Zap className="h-4 w-4" />
            Répéter le conseil
          </button>
        )}
      </div>
    </div>
  );
}

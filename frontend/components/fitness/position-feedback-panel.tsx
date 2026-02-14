"use client";

import { useEffect, useState, useCallback } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Zap,
  Volume2,
  BarChart3,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface PositionFeedbackPanelProps {
  status: "perfect" | "warning" | "error";
  message: string;
  mlClass?: string | null;
  mlConfidence?: number | null;
  formIssues?: string[];
  onSpeak?: (text: string) => void;
  animated?: boolean;
  className?: string;
}

/**
 * Enhanced Position Feedback Panel
 * Displays real-time ML classification with visual and speech corrections
 */
export function PositionFeedbackPanel({
  status,
  message,
  mlClass,
  mlConfidence,
  formIssues,
  onSpeak,
  animated = true,
  className,
}: PositionFeedbackPanelProps) {
  const [isSpoken, setIsSpoken] = useState(false);
  const [correctionMessage, setCorrectionMessage] = useState("");

  // Generate correction message from ML classification
  useEffect(() => {
    if (!mlClass) return;

    let correction = "";
    if (mlClass.includes("Correct")) {
      correction = "Excellente position! Continuez comme ça.";
    } else if (mlClass.includes("Knee")) {
      correction = "Vérifiez vos genoux. Gardez-les alignés avec vos pieds.";
    } else if (mlClass.includes("Back")) {
      correction = "Colonne vertébrale droite. Rentrez légèrement le bassin.";
    } else if (mlClass.includes("Hip")) {
      correction = "Vérifiez la position de vos hanches. Gardez-les stables.";
    } else if (mlClass.includes("Arm") || mlClass.includes("Elbow")) {
      correction = "Positionnez correctement vos bras. Ils doivent être alignés.";
    } else {
      correction = mlClass.replace(/_/g, " ");
    }

    setCorrectionMessage(correction);
  }, [mlClass]);

  // Trigger speech when status or message changes
  useEffect(() => {
    if (!onSpeak || !animated) return;

    // Only speak warnings and corrections
    if (status === "warning" && !isSpoken) {
      const textToSpeak = correctionMessage || message;
      onSpeak(textToSpeak);
      setIsSpoken(true);

      // Reset after 3 seconds to allow re-speaking if issue persists
      const timeout = setTimeout(() => setIsSpoken(false), 3000);
      return () => clearTimeout(timeout);
    }

    if (status === "perfect") {
      setIsSpoken(false);
    }
  }, [status, message, correctionMessage, onSpeak, animated, isSpoken]);

  // Get styling based on status
  const getStyles = () => {
    switch (status) {
      case "perfect":
        return {
          bg: "bg-emerald-500/10",
          border: "border-emerald-500/50",
          icon: CheckCircle2,
          iconColor: "text-emerald-400",
          textColor: "text-emerald-100",
          accentBg: "bg-emerald-500/20",
          glow: "shadow-emerald-500/20",
        };
      case "warning":
        return {
          bg: "bg-amber-500/10",
          border: "border-amber-500/50",
          icon: AlertTriangle,
          iconColor: "text-amber-400",
          textColor: "text-amber-100",
          accentBg: "bg-amber-500/20",
          glow: "shadow-amber-500/20",
        };
      case "error":
        return {
          bg: "bg-red-500/10",
          border: "border-red-500/50",
          icon: Zap,
          iconColor: "text-red-400",
          textColor: "text-red-100",
          accentBg: "bg-red-500/20",
          glow: "shadow-red-500/20",
        };
      default:
        return {
          bg: "bg-blue-500/10",
          border: "border-blue-500/50",
          icon: Sparkles,
          iconColor: "text-blue-400",
          textColor: "text-blue-100",
          accentBg: "bg-blue-500/20",
          glow: "shadow-blue-500/20",
        };
    }
  };

  const styles = getStyles();
  const Icon = styles.icon;

  return (
    <div
      className={cn(
        "glass-panel rounded-2xl border backdrop-blur-md overflow-hidden transition-all duration-300",
        "p-4 flex items-center gap-4",
        styles.bg,
        styles.border,
        animated && status === "warning" && "animate-pulse",
        animated && status === "perfect" && "animate-in fade-in",
        className
      )}
    >
      {/* Icon */}
      <div className={cn("flex-shrink-0", styles.accentBg, "p-3 rounded-full")}>
        <Icon className={cn("w-6 h-6", styles.iconColor)} />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* ML Classification Badge */}
        {mlClass && (
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/30 backdrop-blur-sm border border-white/10">
              <BarChart3 className="w-3.5 h-3.5 text-primary" />
              <span className="text-xs font-medium text-white">{mlClass}</span>
              {mlConfidence && (
                <span className="text-xs text-gray-300">
                  {Math.round(mlConfidence * 100)}%
                </span>
              )}
            </span>
          </div>
        )}

        {/* Main Message */}
        <p className={cn("text-sm font-medium leading-snug", styles.textColor)}>
          {message}
        </p>

        {/* Correction Message (for warnings) */}
        {status === "warning" && correctionMessage && (
          <p className="text-xs text-gray-300 mt-1.5 leading-relaxed italic opacity-90">
            💡 {correctionMessage}
          </p>
        )}

        {/* Form Issues List */}
        {formIssues && formIssues.length > 0 && (
          <div className="mt-2 text-xs space-y-1">
            {formIssues.map((issue, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2 text-gray-300 opacity-80"
              >
                <span className="w-1 h-1 rounded-full bg-current" />
                <span>{issue.replace(/_/g, " ")}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Speaking Indicator */}
      {isSpoken && (
        <div className="flex-shrink-0 flex items-center gap-1.5">
          <Volume2 className={cn("w-4 h-4 animate-bounce", styles.iconColor)} />
          <span className="text-xs font-medium text-gray-300">Correction</span>
        </div>
      )}
    </div>
  );
}

/**
 * Quick Position Status Bar
 * Compact version for display in margins
 */
interface QuickPositionStatusProps {
  status: "perfect" | "warning" | "error";
  mlClass?: string | null;
  mlConfidence?: number | null;
}

export function QuickPositionStatus({
  status,
  mlClass,
  mlConfidence,
}: QuickPositionStatusProps) {
  const statusColors = {
    perfect: "bg-emerald-500/20 border-emerald-500/50 text-emerald-300",
    warning: "bg-amber-500/20 border-amber-500/50 text-amber-300",
    error: "bg-red-500/20 border-red-500/50 text-red-300",
  };

  const statusIcons = {
    perfect: CheckCircle2,
    warning: AlertTriangle,
    error: Zap,
  };

  const StatusIcon = statusIcons[status];

  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border",
        "text-xs font-medium backdrop-blur-sm",
        statusColors[status]
      )}
    >
      <StatusIcon className="w-3.5 h-3.5" />
      {mlClass ? (
        <>
          <span>{mlClass}</span>
          {mlConfidence && <span className="opacity-70">{Math.round(mlConfidence * 100)}%</span>}
        </>
      ) : (
        <span className="capitalize">{status}</span>
      )}
    </div>
  );
}

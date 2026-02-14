"use client";

import { cn } from "@/lib/utils";

type JointStatus = "perfect" | "warning" | "error";

type SkeletonOverlayProps = {
  joints?: Record<string, JointStatus>;
  showTPose?: boolean;
  animate?: boolean;
  className?: string;
  backendJoints?: Record<string, any>;
  mirror?: boolean;
  debug?: boolean;
};

const defaultJoints: Record<string, JointStatus> = {
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
};

const jointColors = {
  perfect: "fill-primary",
  warning: "fill-accent",
  error: "fill-destructive",
};

const jointGlows = {
  perfect: "drop-shadow-[0_0_8px_var(--primary)]",
  warning: "drop-shadow-[0_0_8px_var(--accent)]",
  error: "drop-shadow-[0_0_8px_var(--destructive)]",
};

export function SkeletonOverlay({
  joints = defaultJoints,
  showTPose = false,
  animate = true,
  className,
  backendJoints,
  mirror = false,
  debug = false,
}: SkeletonOverlayProps) {
  // Map backend joints to overlay coordinates if available
  const getPos = (name: string, defaultX: number, defaultY: number) => {
    if (backendJoints && backendJoints[name]) {
      // Backend provides normalized coordinates (0-1), map to 100x100 (percentage)
      let x = backendJoints[name].x * 100;
      let y = backendJoints[name].y * 100;

      return {
        x: x,
        y: y,
        visibility: backendJoints[name].visibility,
        visible: backendJoints[name].visibility > 0.4,
        detected: true,
        name: name
      };
    }
    // If not detected, we return hidden instead of fixed default position
    return { x: defaultX, y: defaultY, visibility: 0, visible: false, detected: false, name: name };
  };

  const jointsList = [
    { pos: getPos("nose", 50, 10), status: joints.head },
    { pos: getPos("left_shoulder", 30, 25), status: joints.leftShoulder },
    { pos: getPos("right_shoulder", 70, 25), status: joints.rightShoulder },
    { pos: getPos("left_elbow", 20, 45), status: joints.leftElbow },
    { pos: getPos("right_elbow", 80, 45), status: joints.rightElbow },
    { pos: getPos("left_wrist", 15, 60), status: joints.leftWrist },
    { pos: getPos("right_wrist", 85, 60), status: joints.rightWrist },
    { pos: getPos("left_hip", 35, 45), status: joints.leftHip },
    { pos: getPos("right_hip", 65, 45), status: joints.rightHip },
    { pos: getPos("left_knee", 30, 70), status: joints.leftKnee },
    { pos: getPos("right_knee", 70, 70), status: joints.rightKnee },
    { pos: getPos("left_ankle", 30, 90), status: joints.leftAnkle },
    { pos: getPos("right_ankle", 70, 90), status: joints.rightAnkle },
  ];

  const head = jointsList[0].pos;
  const lShoulder = jointsList[1].pos;
  const rShoulder = jointsList[2].pos;
  const lElbow = jointsList[3].pos;
  const rElbow = jointsList[4].pos;
  const lWrist = jointsList[5].pos;
  const rWrist = jointsList[6].pos;
  const lHip = jointsList[7].pos;
  const rHip = jointsList[8].pos;
  const lKnee = jointsList[9].pos;
  const rKnee = jointsList[10].pos;
  const lAnkle = jointsList[11].pos;
  const rAnkle = jointsList[12].pos;

  // If no person detected at all, show nothing to avoid 'fixed' skeleton
  const hasDetection = Object.values(backendJoints || {}).length > 0;
  if (!hasDetection && !showTPose) return null;

  return (
    <svg
      viewBox="0 0 100 100"
      className={cn(
        "w-full h-full transition-opacity duration-300",
        animate && "skeleton-pulse",
        mirror && "scale-x-[-1]",
        className
      )}
    >
      {/* Connection lines */}
      <g stroke="currentColor" strokeWidth="0.8" strokeOpacity="0.6" fill="none">
        {/* Spine */}
        {lShoulder.detected && rShoulder.detected && lHip.detected && rHip.detected && (
          <line x1={(lShoulder.x + rShoulder.x) / 2} y1={(lShoulder.y + rShoulder.y) / 2} x2={(lHip.x + rHip.x) / 2} y2={(lHip.y + rHip.y) / 2} />
        )}
        {/* Shoulders */}
        {lShoulder.detected && rShoulder.detected && <line x1={lShoulder.x} y1={lShoulder.y} x2={rShoulder.x} y2={rShoulder.y} />}
        {/* Left arm */}
        {lShoulder.detected && lElbow.detected && <line x1={lShoulder.x} y1={lShoulder.y} x2={lElbow.x} y2={lElbow.y} />}
        {lElbow.detected && lWrist.detected && <line x1={lElbow.x} y1={lElbow.y} x2={lWrist.x} y2={lWrist.y} />}
        {/* Right arm */}
        {rShoulder.detected && rElbow.detected && <line x1={rShoulder.x} y1={rShoulder.y} x2={rElbow.x} y2={rElbow.y} />}
        {rElbow.detected && rWrist.detected && <line x1={rElbow.x} y1={rElbow.y} x2={rWrist.x} y2={rWrist.y} />}
        {/* Hips */}
        {lHip.detected && rHip.detected && <line x1={lHip.x} y1={lHip.y} x2={rHip.x} y2={rHip.y} />}
        {/* Left leg */}
        {lHip.detected && lKnee.detected && <line x1={lHip.x} y1={lHip.y} x2={lKnee.x} y2={lKnee.y} />}
        {lKnee.detected && lAnkle.detected && <line x1={lKnee.x} y1={lKnee.y} x2={lAnkle.x} y2={lAnkle.y} />}
        {/* Right leg */}
        {rHip.detected && rKnee.detected && <line x1={rHip.x} y1={rHip.y} x2={rKnee.x} y2={rKnee.y} />}
        {rKnee.detected && rAnkle.detected && <line x1={rKnee.x} y1={rKnee.y} x2={rAnkle.x} y2={rAnkle.y} />}
      </g>

      {/* Joint circles - only render if visible */}
      {head.visible && (
        <circle
          cx={head.x}
          cy={head.y}
          r="12"
          className={cn(jointColors[joints.head], jointGlows[joints.head])}
          fillOpacity="0.8"
        />
      )}
      {/* Shoulders */}
      {lShoulder.visible && (
        <circle
          cx={lShoulder.x}
          cy={lShoulder.y}
          r="8"
          className={cn(
            jointColors[joints.leftShoulder],
            jointGlows[joints.leftShoulder]
          )}
        />
      )}
      {rShoulder.visible && (
        <circle
          cx={rShoulder.x}
          cy={rShoulder.y}
          r="8"
          className={cn(
            jointColors[joints.rightShoulder],
            jointGlows[joints.rightShoulder]
          )}
        />
      )}

      {/* Elbows */}
      {lElbow.visible && (
        <circle
          cx={lElbow.x}
          cy={lElbow.y}
          r="5"
          className={cn(
            jointColors[joints.leftElbow],
            jointGlows[joints.leftElbow]
          )}
        />
      )}
      {rElbow.visible && (
        <circle
          cx={rElbow.x}
          cy={rElbow.y}
          r="5"
          className={cn(
            jointColors[joints.rightElbow],
            jointGlows[joints.rightElbow]
          )}
        />
      )}

      {/* Wrists */}
      {lWrist.visible && (
        <circle
          cx={lWrist.x}
          cy={lWrist.y}
          r="4"
          className={cn(
            jointColors[joints.leftWrist],
            jointGlows[joints.leftWrist]
          )}
        />
      )}
      {rWrist.visible && (
        <circle
          cx={rWrist.x}
          cy={rWrist.y}
          r="4"
          className={cn(
            jointColors[joints.rightWrist],
            jointGlows[joints.rightWrist]
          )}
        />
      )}

      {/* Hips */}
      {lHip.visible && (
        <circle
          cx={lHip.x}
          cy={lHip.y}
          r="5"
          className={cn(jointColors[joints.leftHip], jointGlows[joints.leftHip])}
        />
      )}
      {rHip.visible && (
        <circle
          cx={rHip.x}
          cy={rHip.y}
          r="5"
          className={cn(
            jointColors[joints.rightHip],
            jointGlows[joints.rightHip]
          )}
        />
      )}

      {/* Knees */}
      {lKnee.visible && (
        <circle
          cx={lKnee.x}
          cy={lKnee.y}
          r="5"
          className={cn(
            jointColors[joints.leftKnee],
            jointGlows[joints.leftKnee]
          )}
        />
      )}
      {rKnee.visible && (
        <circle
          cx={rKnee.x}
          cy={rKnee.y}
          r="5"
          className={cn(
            jointColors[joints.rightKnee],
            jointGlows[joints.rightKnee]
          )}
        />
      )}

      {/* Ankles */}
      {lAnkle.visible && (
        <circle
          cx={lAnkle.x}
          cy={lAnkle.y}
          r="4"
          className={cn(
            jointColors[joints.leftAnkle],
            jointGlows[joints.leftAnkle]
          )}
        />
      )}
      {rAnkle.visible && (
        <circle
          cx={rAnkle.x}
          cy={rAnkle.y}
          r="4"
          className={cn(
            jointColors[joints.rightAnkle],
            jointGlows[joints.rightAnkle]
          )}
        />
      )}
      {/* Debug Labels */}
      {debug && jointsList.map(({ pos }, idx) => (
        <g key={idx}>
          <rect
            x={pos.x + 5}
            y={pos.y - 12}
            width="40"
            height="10"
            rx="2"
            className="fill-black/60"
          />
          <text
            x={pos.x + 7}
            y={pos.y - 4}
            className="text-[6px] fill-white font-mono"
          >
            {Math.round(pos.visibility * 100)}%
          </text>
        </g>
      ))}
    </svg>
  );
}

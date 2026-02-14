"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { useSessionHistory } from "@/lib/use-backend";

export type Screen =
  | "home"
  | "calibration"
  | "quick-start"
  | "manual-mode"
  | "custom-chain"
  | "stats"
  | "about";

export type MuscleGroup = "legs" | "arms" | "chest" | "back" | "core";

export type Exercise = {
  id: string;
  name: string;
  icon: string;
  difficulty: "easy" | "medium" | "hard";
  targetMuscles: MuscleGroup[];
  reps: number;
  sets: number;
  restTime: number;
};

export type SessionData = {
  date: Date;
  exercises: {
    name: string;
    reps: number;
    sets: number;
    qualityScore: number;
  }[];
  totalReps: number;
  caloriesBurned: number;
  postureAccuracy: number;
};

export type CalibrationData = {
  isCalibrated: boolean;
  shoulderWidth: number;
  armLength: number;
  legLength: number;
  torsoHeight: number;
  body_type?: string;
};

// User profile from backend
export type UserProfile = {
  id: string;
  name: string;
  ratios?: Record<string, number>;
  thresholds?: Record<string, number>;
  bodyType?: string;
  createdAt?: string;
};

type AppContextType = {
  currentScreen: Screen;
  setCurrentScreen: (screen: Screen) => void;
  isSessionActive: boolean;
  setIsSessionActive: (active: boolean) => void;
  currentExercise: Exercise | null;
  setCurrentExercise: (exercise: Exercise | null) => void;
  currentReps: number;
  setCurrentReps: (reps: number) => void;
  currentSet: number;
  setCurrentSet: (set: number) => void;
  calibrationData: CalibrationData;
  setCalibrationData: (data: CalibrationData) => void;
  selectedMuscleGroup: MuscleGroup | null;
  setSelectedMuscleGroup: (group: MuscleGroup | null) => void;
  selectedExercises: Exercise[];
  setSelectedExercises: React.Dispatch<React.SetStateAction<Exercise[]>>;
  customChain: Exercise[];
  setCustomChain: React.Dispatch<React.SetStateAction<Exercise[]>>;
  sessionHistory: SessionData[];
  addSessionToHistory: (session: SessionData) => void;
  cameraConnected: boolean;
  setCameraConnected: (connected: boolean) => void;
  fps: number;
  setFps: (fps: number) => void;
  postureStatus: "perfect" | "warning" | "error";
  setPostureStatus: (status: "perfect" | "warning" | "error") => void;
  postureFeedback: string;
  setPostureFeedback: (feedback: string) => void;
  cameraStream: MediaStream | null;
  setCameraStream: (stream: MediaStream | null) => void;
  cameraError: string | null;
  setCameraError: (error: string | null) => void;
  // Backend integration
  userProfile: UserProfile | null;
  setUserProfile: (profile: UserProfile | null) => void;
  availableProfiles: UserProfile[];
  setAvailableProfiles: (profiles: UserProfile[]) => void;
  switchToProfile: (profileId: string) => Promise<void>;
  createProfile: (name: string) => Promise<void>;
  backendConnected: boolean;
  setBackendConnected: (connected: boolean) => void;
  useBackendPose: boolean;
  setUseBackendPose: (use: boolean) => void;
  isDebugMode: boolean;
  setIsDebugMode: (debug: boolean) => void;
};

const AppContext = createContext<AppContextType | undefined>(undefined);

const defaultExercises: Exercise[] = [
  {
    id: "squat",
    name: "Squat",
    icon: "squat",
    difficulty: "medium",
    targetMuscles: ["legs"],
    reps: 15,
    sets: 3,
    restTime: 60,
  },
  {
    id: "lunge",
    name: "Fentes",
    icon: "lunges",
    difficulty: "medium",
    targetMuscles: ["legs"],
    reps: 12,
    sets: 3,
    restTime: 45,
  },
  {
    id: "bicep_curl",
    name: "Curl Biceps",
    icon: "bicep",
    difficulty: "easy",
    targetMuscles: ["arms"],
    reps: 12,
    sets: 3,
    restTime: 45,
  },
  {
    id: "pushup",
    name: "Pompes",
    icon: "pushup",
    difficulty: "medium",
    targetMuscles: ["chest", "arms"],
    reps: 10,
    sets: 3,
    restTime: 60,
  },
  {
    id: "plank",
    name: "Planche",
    icon: "plank",
    difficulty: "hard",
    targetMuscles: ["core"],
    reps: 1,
    sets: 3,
    restTime: 30,
  },
  {
    id: "tricep-dips",
    name: "Dips Triceps",
    icon: "dips",
    difficulty: "medium",
    targetMuscles: ["arms"],
    reps: 10,
    sets: 3,
    restTime: 45,
  },
  {
    id: "shoulder-press",
    name: "Press Epaules",
    icon: "shoulder",
    difficulty: "medium",
    targetMuscles: ["arms", "chest"],
    reps: 12,
    sets: 3,
    restTime: 60,
  },
  {
    id: "rows",
    name: "Rowing",
    icon: "rows",
    difficulty: "medium",
    targetMuscles: ["back"],
    reps: 12,
    sets: 3,
    restTime: 60,
  },
  {
    id: "crunches",
    name: "Crunchs",
    icon: "crunch",
    difficulty: "easy",
    targetMuscles: ["core"],
    reps: 20,
    sets: 3,
    restTime: 30,
  },
  {
    id: "deadlift",
    name: "Soulevé de terre",
    icon: "deadlift",
    difficulty: "hard",
    targetMuscles: ["legs", "back"],
    reps: 8,
    sets: 3,
    restTime: 90,
  },
];

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [currentScreen, setCurrentScreen] = useState<Screen>("home");
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [currentExercise, setCurrentExercise] = useState<Exercise | null>(null);
  const [currentReps, setCurrentReps] = useState(0);
  const [currentSet, setCurrentSet] = useState(1);
  const [calibrationData, setCalibrationData] = useState<CalibrationData>({
    isCalibrated: false,
    shoulderWidth: 0,
    armLength: 0,
    legLength: 0,
    torsoHeight: 0,
    body_type: "unknown",
  });
  const [selectedMuscleGroup, setSelectedMuscleGroup] =
    useState<MuscleGroup | null>(null);
  const [selectedExercises, setSelectedExercises] =
    useState<Exercise[]>(defaultExercises);
  const [customChain, setCustomChain] = useState<Exercise[]>([]);
  const [sessionHistory, setSessionHistory] = useState<SessionData[]>([]);
  const [cameraConnected, setCameraConnected] = useState(true);
  const [fps, setFps] = useState(30);
  const [postureStatus, setPostureStatus] = useState<
    "perfect" | "warning" | "error"
  >("perfect");
  const [postureFeedback, setPostureFeedback] = useState("Posture parfaite");

  // Backend integration state
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [availableProfiles, setAvailableProfiles] = useState<UserProfile[]>([]);
  const [backendConnected, setBackendConnected] = useState(false);
  const [useBackendPose, setUseBackendPose] = useState(false);
  const [isDebugMode, setIsDebugMode] = useState(false);

  // Fetch profiles on mount
  useEffect(() => {
    async function loadProfiles() {
      try {
        const { api } = require("@/lib/api-client");
        const users = await api.listProfiles();
        if (Array.isArray(users) && users.length > 0) {
          setAvailableProfiles(users);
          // Set first profile as default if none selected
          if (!userProfile) {
            setUserProfile(users[0]);
          }
        }
      } catch (err) {
        console.error("Failed to load profiles:", err);
        setAvailableProfiles([]);
      }
    }
    loadProfiles();
  }, []);

  // Fetch session history from backend
  const { sessions: backendSessions, refresh: refreshHistory } = useSessionHistory(userProfile?.id || "demo_user");

  // Refresh history when session ends
  useEffect(() => {
    if (!isSessionActive && userProfile?.id) {
      refreshHistory();
    }
  }, [isSessionActive, userProfile?.id, refreshHistory]);

  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);

  useEffect(() => {
    if (backendSessions && backendSessions.length > 0) {
      const mappedSessions: SessionData[] = backendSessions.map(s => ({
        date: new Date(s.date),
        exercises: [{
          name: s.exercise,
          reps: s.reps,
          sets: s.sets,
          qualityScore: Math.max(0, 100 - (s.fatigue_score || 0))
        }],
        totalReps: s.reps,
        caloriesBurned: s.calories_est,
        postureAccuracy: 90
      }));
      setSessionHistory(mappedSessions);
    } else {
      setSessionHistory([]);
    }
  }, [backendSessions]);

  const addSessionToHistory = useCallback((session: SessionData) => {
    setSessionHistory((prev) => [session, ...prev]);
  }, []);

  return (
    <AppContext.Provider
      value={{
        currentScreen,
        setCurrentScreen,
        isSessionActive,
        setIsSessionActive,
        currentExercise,
        setCurrentExercise,
        currentReps,
        setCurrentReps,
        currentSet,
        setCurrentSet,
        calibrationData,
        setCalibrationData,
        selectedMuscleGroup,
        setSelectedMuscleGroup,
        selectedExercises,
        setSelectedExercises,
        customChain,
        setCustomChain,
        sessionHistory,
        addSessionToHistory,
        cameraConnected,
        setCameraConnected,
        fps,
        setFps,
        postureStatus,
        setPostureStatus,
        postureFeedback,
        setPostureFeedback,
        cameraStream,
        setCameraStream,
        cameraError,
        setCameraError,
        // Backend integration
        userProfile,
        setUserProfile,
        availableProfiles,
        setAvailableProfiles,
        switchToProfile: async (profileId: string) => {
          try {
            const { api } = require("@/lib/api-client");
            const profile = await api.getProfile(profileId);
            setUserProfile(profile);
            // Optionally reset screen to home
            setCurrentScreen("home");
          } catch (err) {
            console.error("Failed to switch profile:", err);
          }
        },
        createProfile: async (name: string) => {
          try {
            const { api } = require("@/lib/api-client");
            const newProfile = await api.createProfile(name);
            if (newProfile && newProfile.id) {
              setAvailableProfiles(prev => [...prev, newProfile]);
              setUserProfile(newProfile);
              setCurrentScreen("home");
            }
          } catch (err) {
            console.error("Failed to create profile:", err);
          }
        },
        backendConnected,
        setBackendConnected,
        useBackendPose,
        setUseBackendPose,
        isDebugMode,
        setIsDebugMode,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
}

export { defaultExercises };

"use client";

/**
 * React hooks for WebSocket connection and real-time data
 */
import { useState, useEffect, useCallback, useRef } from "react";
import {
    wsManager,
    api,
    type WSMessage,
    type KeypointsData,
    type ExerciseUpdate,
    type HardwareStatus,
    type UserProfile,
} from "./api-client";

// ==================== useWebSocket Hook ====================

interface UseWebSocketOptions {
    autoConnect?: boolean;
    onConnect?: () => void;
    onDisconnect?: () => void;
    onError?: (error: Event) => void;
}

interface UseWebSocketReturn {
    isConnected: boolean;
    connect: () => Promise<void>;
    disconnect: () => void;
    send: (type: string, data?: Record<string, unknown>) => boolean;
    // Session controls
    startSession: (userId: string, exercises: string[], targetReps?: number, targetSets?: number, exerciseConfigs?: any[]) => boolean;
    stopSession: () => boolean;
    pause: () => boolean;
    resume: () => boolean;
    selectExercise: (index: number) => boolean;
    startCalibration: (userId: string, duration?: number) => boolean;
    sendFrame: (base64Image: string) => boolean;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
    const [isConnected, setIsConnected] = useState(wsManager.isConnected);
    const { autoConnect = true, onConnect, onDisconnect } = options;

    useEffect(() => {
        if (autoConnect && !wsManager.isConnected) {
            wsManager.connect().catch(console.error);
        }

        // Check connection status periodically
        const interval = setInterval(() => {
            setIsConnected(wsManager.isConnected);
        }, 1000);

        return () => {
            clearInterval(interval);
        };
    }, [autoConnect]);

    const connect = useCallback(async () => {
        await wsManager.connect();
        setIsConnected(true);
        onConnect?.();
    }, [onConnect]);

    const disconnect = useCallback(() => {
        wsManager.disconnect();
        setIsConnected(false);
        onDisconnect?.();
    }, [onDisconnect]);

    const send = useCallback((type: string, data: Record<string, unknown> = {}) => {
        return wsManager.send(type, data);
    }, []);

    const startSession = useCallback((userId: string, exercises: string[], targetReps?: number, targetSets?: number, exerciseConfigs?: any[]) => {
        if (wsManager.isConnected) return wsManager.startSession(userId, exercises, targetReps, targetSets, exerciseConfigs);
        return false;
    }, []);

    const stopSession = useCallback(() => {
        if (wsManager.isConnected) return wsManager.stopSession();
        return false;
    }, []);

    const pause = useCallback(() => {
        if (wsManager.isConnected) return wsManager.pause();
        return false;
    }, []);

    const resume = useCallback(() => {
        if (wsManager.isConnected) return wsManager.resume();
        return false;
    }, []);

    const startCalibration = useCallback((userId: string, duration = 5) => {
        if (wsManager.isConnected) return wsManager.startCalibration(userId, duration);
        return false;
    }, []);

    const sendFrame = useCallback((base64Image: string) => {
        if (wsManager.isConnected) return wsManager.sendFrame(base64Image);
        return false;
    }, []);

    const selectExercise = useCallback((index: number) => {
        if (wsManager.isConnected) return wsManager.selectExercise(index);
        return false;
    }, []);

    return {
        isConnected,
        connect,
        disconnect,
        send,
        startSession,
        stopSession,
        pause,
        resume,
        selectExercise,
        startCalibration,
        sendFrame,
    };
}

// ==================== useKeypoints Hook ====================

interface UseKeypointsReturn {
    keypoints: KeypointsData | null;
    fps: number;
    isReceiving: boolean;
}

export function useKeypoints(): UseKeypointsReturn {
    const [keypoints, setKeypoints] = useState<KeypointsData | null>(null);
    const [fps, setFps] = useState(0);
    const [isReceiving, setIsReceiving] = useState(false);
    const lastUpdateRef = useRef<number>(0);

    useEffect(() => {
        const unsubscribe = wsManager.on("keypoints", (message: WSMessage) => {
            const data = message.data as unknown as KeypointsData;
            if (!data) return;
            setKeypoints(data);
            setFps(data.fps);
            lastUpdateRef.current = Date.now();
            setIsReceiving(true);
        });

        const unsubNoDetection = wsManager.on("no_detection", () => {
            setIsReceiving(false);
            // We still want to clear keypoints if no one is there
            setKeypoints(null);
        });

        // Check if we're still receiving data
        const interval = setInterval(() => {
            if (Date.now() - lastUpdateRef.current > 2000) {
                setIsReceiving(false);
            }
        }, 1000);

        return () => {
            unsubscribe();
            unsubNoDetection();
            clearInterval(interval);
        };
    }, []);

    return { keypoints, fps, isReceiving };
}

// ==================== useExercise Hook ====================

interface UseExerciseReturn {
    exercise: string;
    phase: string;
    repCount: number;
    setCount: number;
    targetReps: number;
    targetSets: number;
    confidence: number;
    formQuality: number;
    formIssues: string[];
    fatigueWarning: boolean;
    fatiguePercent: number;
    // ML Classification fields
    mlClass: string | null;
    mlConfidence: number | null;
}

export function useExercise(): UseExerciseReturn {
    const [state, setState] = useState({
        exercise: "unknown",
        phase: "idle",
        repCount: 0,
        setCount: 1,
        targetReps: 15,
        targetSets: 3,
        confidence: 0,
        formQuality: 1,
        formIssues: [] as string[],
        fatigueWarning: false,
        fatiguePercent: 0,
        // ML fields
        mlClass: null as string | null,
        mlConfidence: null as number | null,
    });

    useEffect(() => {
        const unsubExercise = wsManager.on("exercise_update", (message: WSMessage) => {
            const data = message.data as unknown as ExerciseUpdate;
            if (!data) return;
            setState((prev) => ({
                ...prev,
                exercise: data.exercise,
                phase: data.phase,
                repCount: data.rep_count,
                confidence: data.confidence,
                formQuality: data.form_quality,
                // ML classification from backend
                mlClass: data.ml_class || prev.mlClass,
                mlConfidence: data.ml_confidence || prev.mlConfidence,
                formIssues: data.feedback_codes || prev.formIssues,
            }));
        });

        const unsubRep = wsManager.on("rep_count", (message: WSMessage) => {
            const data = message.data as { count: number; target: number; set: number };
            if (!data) return;
            setState((prev) => ({
                ...prev,
                repCount: data.count,
                targetReps: data.target,
                setCount: data.set,
            }));
        });

        const unsubFatigue = wsManager.on("fatigue_warning", (message: WSMessage) => {
            const data = message.data as { slowdown_percent: number };
            if (!data) return;
            setState((prev) => ({
                ...prev,
                fatigueWarning: true,
                fatiguePercent: data.slowdown_percent,
            }));

            // Clear fatigue warning after 5 seconds
            setTimeout(() => {
                setState((prev) => ({ ...prev, fatigueWarning: false }));
            }, 5000);
        });

        const unsubFeedback = wsManager.on("feedback", (message: WSMessage) => {
            const data = message.data as { issues?: string[] };
            if (data.issues) {
                setState((prev) => ({
                    ...prev,
                    formIssues: data.issues || [],
                }));
            }
        });

        return () => {
            unsubExercise();
            unsubRep();
            unsubFatigue();
            unsubFeedback();
        };
    }, []);

    return state;
}

// ==================== useHardware Hook ====================

export function useHardware(): HardwareStatus | null {
    const [status, setStatus] = useState<HardwareStatus | null>(null);

    useEffect(() => {
        const unsubscribe = wsManager.on("hardware_status", (message: WSMessage) => {
            const data = message.data as unknown as HardwareStatus;
            if (data) setStatus(data);
        });

        return unsubscribe;
    }, []);

    return status;
}

// ==================== useFeedback Hook ====================

interface FeedbackMessage {
    status: "perfect" | "warning" | "error";
    message: string;
    issues?: string[];
    timestamp: number;
    mlClass?: string | null;  // Add ML class to feedback
    mlConfidence?: number | null;
}

export function useFeedback(): FeedbackMessage | null {
    const [feedback, setFeedback] = useState<FeedbackMessage | null>(null);

    useEffect(() => {
        const unsubscribe = wsManager.on("feedback", (message: WSMessage) => {
            const data = message.data as {
                status: string;
                message: string;
                issues?: string[];
                ml_class?: string;
                ml_confidence?: number;
            };
            if (!data) return;
            setFeedback({
                status: data.status as "perfect" | "warning" | "error",
                message: data.message,
                issues: data.issues,
                mlClass: data.ml_class,
                mlConfidence: data.ml_confidence,
                timestamp: Date.now(),
            });
        });

        // Listen for exercise updates which may contain ML classification
        const unsubExercise = wsManager.on("exercise_update", (message: WSMessage) => {
            const data = message.data as unknown as ExerciseUpdate;
            if (!data || !data.ml_class) return;

            // Create feedback from ML classification
            setFeedback({
                status: data.ml_class.includes("Correct") ? "perfect" : "warning",
                message: data.ml_class,
                mlClass: data.ml_class,
                mlConfidence: data.ml_confidence,
                timestamp: Date.now(),
            });
        });

        // Listen for rejected reps too as they are a type of feedback
        const unsubRejected = wsManager.on("rep_rejected", (message: WSMessage) => {
            const data = message.data as { reason: string; message: string };
            if (!data) return;
            setFeedback({
                status: "error",
                message: data.message,
                timestamp: Date.now(),
            });
        });

        // Listen for pauses (safety warnings or manual)
        const unsubPaused = wsManager.on("paused", (message: WSMessage) => {
            const data = (message.data || {}) as { reason?: string };
            if (data.reason) {
                setFeedback({
                    status: "warning",
                    message: data.reason,
                    timestamp: Date.now(),
                });
            }
        });

        const unsubResumed = wsManager.on("resumed", () => {
            setFeedback(null);
        });

        // Listen for fatigue warnings
        const unsubFatigue = wsManager.on("fatigue_warning", (message: WSMessage) => {
            const data = (message.data || {}) as { message?: string; slowdown_percent?: number };
            // If the message is not explicitly in the data, use a default fallback
            const msg = data.message || (data.slowdown_percent && data.slowdown_percent > 30
                ? "Fatigue importante détectée. Ralentissez."
                : "Ralentissez un peu, respirez.");

            setFeedback({
                status: "warning",
                message: msg,
                timestamp: Date.now(),
            });
        });

        // Reset feedback state on transitions to avoid "stuck" UI messages
        const unsubTransition = wsManager.on("exercise_change", () => {
            setFeedback(null);
        });

        const unsubSetComplete = wsManager.on("set_complete", () => {
            setFeedback(null);
        });

        return () => {
            unsubscribe();
            unsubExercise();
            unsubRejected();
            unsubPaused();
            unsubResumed();
            unsubTransition();
            unsubSetComplete();
            unsubFatigue();
        };
    }, []);

    return feedback;
}

// ==================== useVoice Hook ====================

export function useVoice() {
    const speak = useCallback((text: string) => {
        if (typeof window === "undefined" || !window.speechSynthesis) return;

        // Cancel previous speech to avoid queue buildup
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = "fr-FR"; // Use French as per backend translation
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        window.speechSynthesis.speak(utterance);
    }, []);

    useEffect(() => {
        const unsubscribe = wsManager.on("voice", (message: WSMessage) => {
            const data = (message.data || {}) as { text: string };
            if (data.text) {
                speak(data.text);
            }
        });

        return unsubscribe;
    }, [speak]);

    return { speak };
}

// ==================== useCalibration Hook ====================

interface CalibrationState {
    isCalibrating: boolean;
    progress: number;
    status: string;
    result: {
        success: boolean;
        ratios?: Record<string, number>;
        thresholds?: Record<string, number>;
        body_type?: string;  // Add body type from ONNX
        message: string;
    } | null;
}

export function useCalibration(): CalibrationState {
    const [state, setState] = useState<CalibrationState>({
        isCalibrating: false,
        progress: 0,
        status: "idle",
        result: null,
    });

    useEffect(() => {
        const unsubProgress = wsManager.on("calibration_progress", (message: WSMessage) => {
            const data = message.data as { progress: number; status: string };
            if (!data) return;
            setState((prev) => ({
                ...prev,
                isCalibrating: true,
                progress: data.progress,
                status: data.status,
            }));
        });

        const unsubComplete = wsManager.on("calibration_complete", (message: WSMessage) => {
            const data = message.data as CalibrationState["result"];
            if (!data) return;

            // Add body_type with fallback
            const enhancedData = {
                ...data,
                body_type: data.body_type || 'unknown'
            };

            setState({
                isCalibrating: false,
                progress: 1,
                status: "complete",
                result: enhancedData,
            });
        });

        return () => {
            unsubProgress();
            unsubComplete();
        };
    }, []);

    return state;
}

// ==================== useProfile Hook ====================

interface UseProfileReturn {
    profile: UserProfile | null;
    isLoading: boolean;
    error: string | null;
    createProfile: (name: string) => Promise<UserProfile | null>;
    loadProfile: (userId: string) => Promise<void>;
    updateProfile: (updates: Partial<UserProfile>) => Promise<boolean>;
}

export function useProfile(initialUserId?: string): UseProfileReturn {
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadProfile = useCallback(async (userId: string) => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await api.getProfile(userId);
            setProfile(data);
        } catch (e: unknown) {
            setError((e as Error).message);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const createProfile = useCallback(async (name: string): Promise<UserProfile | null> => {
        setIsLoading(true);
        setError(null);
        try {
            const result = await api.createProfile(name);
            if (result) {
                setProfile(result);
                return result;
            }
            return null;
        } catch (e: unknown) {
            setError((e as Error).message);
            return null;
        } finally {
            setIsLoading(false);
        }
    }, []);

    const updateProfile = useCallback(
        async (updates: Partial<UserProfile>): Promise<boolean> => {
            if (!profile) return false;
            setIsLoading(true);
            try {
                await api.updateProfile(profile.id, updates);
                setProfile((prev) => (prev ? { ...prev, ...updates } : null));
                return true;
            } catch (e: unknown) {
                setError((e as Error).message);
                return false;
            } finally {
                setIsLoading(false);
            }
        },
        [profile]
    );

    useEffect(() => {
        if (initialUserId) {
            loadProfile(initialUserId);
        }
    }, [initialUserId, loadProfile]);

    return {
        profile,
        isLoading,
        error,
        createProfile,
        loadProfile,
        updateProfile,
    };
}

// ==================== useSessionHistory Hook ====================

interface UseSessionHistoryReturn {
    sessions: import("./api-client").SessionData[];
    stats: {
        totalSessions: number;
        totalReps: number;
        totalCalories: number;
        avgFatigue: number;
    } | null;
    isLoading: boolean;
    error: string | null;
    refresh: () => Promise<void>;
}

export function useSessionHistory(userId?: string): UseSessionHistoryReturn {
    const [sessions, setSessions] = useState<import("./api-client").SessionData[]>([]);
    const [stats, setStats] = useState<UseSessionHistoryReturn["stats"]>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const refresh = useCallback(async () => {
        if (!userId) return;
        setIsLoading(true);
        setError(null);
        try {
            const data = await api.getHistory(userId);
            setSessions(data.sessions);
            setStats({
                totalSessions: data.total_sessions,
                totalReps: data.total_reps,
                totalCalories: data.total_calories,
                avgFatigue: data.avg_fatigue,
            });
        } catch (e: unknown) {
            setError((e as Error).message);
        } finally {
            setIsLoading(false);
        }
    }, [userId]);

    useEffect(() => {
        if (userId) {
            refresh();
        }
    }, [userId, refresh]);

    return { sessions, stats, isLoading, error, refresh };
}
/**
 * API Client for Virtual Sports Coach Backend
 * Handles REST endpoints and WebSocket connection
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

// ==================== Types ====================

export interface UserProfile {
  id: string;
  name: string;
  ratios?: BodyRatios;
  thresholds?: ExerciseThresholds;
  body_type?: 'fat' | 'weak' | 'normal' | 'athletic' | 'slim' | 'muscular';  // Added slim/muscular for ONNX
  created_at: string;
}

export interface BodyRatios {
  shoulder_width: number;
  arm_length: number;
  leg_length: number;
  torso_height: number;
  leg_torso_ratio: number;
}

export interface ExerciseThresholds {
  squat_knee_angle: number;
  squat_tolerance: number;
  pushup_elbow_angle: number;
  plank_hip_angle: number;
  bicep_curl_angle: number;
}

export interface CalibrationResult {
  success: boolean;
  user_id: string;
  ratios?: BodyRatios;
  thresholds?: ExerciseThresholds;
  body_type?: string;  // Will contain 'fat', 'slim', or 'muscular' from ONNX
  message: string;
}

export interface SessionData {
  id: number;
  user_id: string;
  date: string;
  exercise: string;
  reps: number;
  sets: number;
  calories_est: number;
  fatigue_score: number;
  duration: number;
}

export interface SessionSummary {
  user_id: string;
  total_sessions: number;
  total_reps: number;
  total_calories: number;
  avg_fatigue: number;
  sessions: SessionData[];
}

export interface Keypoint {
  x: number;
  y: number;
  visibility: number;
}

export interface KeypointsData {
  keypoints: Record<string, Keypoint>;
  angles: Record<string, number>;
  fps: number;
}

export interface ExerciseUpdate {
  exercise: string;
  phase: string;
  rep_count: number;
  confidence: number;
  form_quality: number;
  avg_rep_time: number;
  events: Array<{ type: string;[key: string]: unknown }>;
  // ML Classification fields (for squat/pushup)
  ml_class?: string;      // e.g., "Squat Correct", "Pushup Incorrect", "Squat Shallow"
  ml_confidence?: number; // 0.0 to 1.0
  feedback_codes?: string[];
}

export interface HardwareStatus {
  heart_rate: number;
  heart_rate_warning: boolean;
  imu_tremor_detected: boolean;
  battery_level: number;
  eco_mode: boolean;
  calories_burned: number;
  water_glasses_saved: number;
}

export interface WSMessage {
  type: string;
  data: Record<string, unknown>;
  timestamp?: number;
}

// ==================== API Client ====================

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error ${response.status}: ${errorText}`);
      }
      return response.json() as Promise<T>;
    } catch (err) {
      console.error(`Request failed for ${endpoint}:`, err);
      throw err;
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string; camera_available: boolean }> {
    return this.request('/health');
  }

  // ==================== Profile Endpoints ====================

  async createProfile(name: string): Promise<UserProfile> {
    return this.request('/users', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  async getProfile(userId: string): Promise<UserProfile> {
    return this.request(`/users/${userId}`);
  }

  async updateProfile(
    userId: string,
    updates: Partial<UserProfile>
  ): Promise<{ success: boolean }> {
    return this.request(`/profile/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteProfile(userId: string): Promise<{ status: string; message: string }> {
    return this.request(`/users/${userId}`, {
      method: 'DELETE',
    });
  }

  async listProfiles(): Promise<UserProfile[]> {
    return this.request('/users');
  }

  // ==================== Calibration ====================

  async calibrate(userId: string, durationSeconds: number = 5): Promise<CalibrationResult> {
    return this.request('/calibrate', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        duration: durationSeconds,
      }),
    });
  }

  // ==================== History ====================

  async getHistory(userId: string, limit: number = 50): Promise<SessionSummary> {
    return this.request(`/sessions/${userId}?limit=${limit}`);
  }

  async saveSession(
    userId: string,
    exercise: string,
    reps: number,
    sets: number = 1,
    calories: number = 0,
    fatigue: number = 0,
    duration: number = 0
  ): Promise<{ success: boolean; session_id: number }> {
    return this.request('/sessions', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        exercise,
        reps,
        sets,
        calories_est: calories,
        fatigue_score: fatigue,
        duration,
      }),
    });
  }
}

// ==================== WebSocket Manager ====================

export type WSMessageHandler = (message: WSMessage) => void;

class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private handlers: Map<string, Set<WSMessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;

  constructor(url: string = WS_URL) {
    this.url = url;
  }

  private connectionPromise: Promise<void> | null = null;

  connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    // If socket exists but is closed or closing, null it out
    if (this.ws && (this.ws.readyState === WebSocket.CLOSED || this.ws.readyState === WebSocket.CLOSING)) {
      this.ws = null;
    }

    this.isConnecting = true;
    this.connectionPromise = new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[WS] Connected to backend');
          this.reconnectAttempts = 0;
          this.isConnecting = false;
          this.connectionPromise = null;
          resolve();
        };

        this.ws.onclose = (event) => {
          console.log('[WS] Disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.connectionPromise = null;
          // Only attempt reconnect if we didn't intentionally close?
          // For now, keep current behavior but ensure promise is cleared.
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          // ReadyState 3 means CLOSED. If it's already closed, we just log it.
          if (this.ws?.readyState === WebSocket.CLOSED) {
            console.warn('[WS] Socket closed during or after error.');
          } else {
            console.error('[WS] Connection error. Current state:', this.ws?.readyState);
          }
          this.isConnecting = false;
          this.connectionPromise = null;
          reject(error);
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (e) {
            console.error('[WS] Failed to parse message:', e);
          }
        };
      } catch (error) {
        this.isConnecting = false;
        this.connectionPromise = null;
        reject(error);
      }
    });

    return this.connectionPromise;
  }

  private handleMessage(message: WSMessage) {
    // Call type-specific handlers
    const typeHandlers = this.handlers.get(message.type);
    if (typeHandlers) {
      typeHandlers.forEach((handler) => handler(message));
    }

    // Call wildcard handlers
    const allHandlers = this.handlers.get('*');
    if (allHandlers) {
      allHandlers.forEach((handler) => handler(message));
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WS] Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch((e) => {
        console.error('[WS] Reconnect failed:', e);
      });
    }, delay);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(type: string, data: Record<string, unknown> = {}) {
    if (!this.isConnected || !this.ws) {
      // Don't log error for common scenarios, just return false
      return false;
    }

    const message: WSMessage = {
      type,
      data,
      timestamp: Date.now(),
    };

    this.ws.send(JSON.stringify(message));
    return true;
  }

  // Subscribe to message types
  on(type: string, handler: WSMessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.handlers.get(type)?.delete(handler);
    };
  }

  // Convenience methods for common operations
  startSession(userId: string, exercises: string[], targetReps = 15, targetSets = 3, exerciseConfigs?: any[]) {
    return this.send('start_session', {
      user_id: userId,
      exercises,
      target_reps: targetReps,
      target_sets: targetSets,
      exercise_configs: exerciseConfigs
    });
  }

  selectExercise(index: number) {
    return this.send('select_exercise', { index });
  }

  stopSession() {
    return this.send('stop_session');
  }

  pause() {
    return this.send('pause');
  }

  resume() {
    return this.send('resume');
  }

  startCalibration(userId: string, duration = 5) {
    return this.send('start_calibration', {
      user_id: userId,
      duration,
    });
  }

  sendFrame(base64Image: string) {
    // Throttled frame sending to not saturate connection
    return this.send('process_frame', {
      image: base64Image
    });
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// ==================== Exports ====================

export const api = new APIClient();
export const wsManager = new WebSocketManager();

// Default export
export default {
  api,
  wsManager,
  API_BASE_URL,
  WS_URL,
};
"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { CameraOff, Smartphone, UserCheck, UserX, Bug, Power, PowerOff } from "lucide-react";
import { useWebSocket, useKeypoints } from "@/lib/use-backend";
import { useApp } from "@/lib/app-context";

interface CameraFeedProps {
  className?: string;
  onCameraStatus?: (connected: boolean) => void;
  onFpsUpdate?: (fps: number) => void;
  mirror?: boolean;
}

export function CameraFeed({
  className,
  onCameraStatus,
  onFpsUpdate,
  mirror = true,
}: CameraFeedProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const frameCountRef = useRef(0);
  const lastTimeRef = useRef(performance.now());

  const { isReceiving: isPersonDetected } = useKeypoints();
  const { send, isConnected: isWSConnected } = useWebSocket();
  const { isDebugMode, setIsDebugMode } = useApp();

  let API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  if (API_URL.endsWith('/')) API_URL = API_URL.slice(0, -1);

  // Handle backend connectivity check
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const res = await fetch(`${API_URL}/`, {
          headers: {
            'ngrok-skip-browser-warning': 'true',
          },
        });
        if (res.ok) {
          const data = await res.json();

          const running = data.camera_available || data.is_running;
          setIsCameraActive(running);

          if (!running) {
            setError(null); // Not an error if just not started
            setIsConnected(false);
            onCameraStatus?.(false);
          } else {
            setIsConnected(true);
            setError(null);
            onCameraStatus?.(true);
          }
        } else {
          throw new Error();
        }
      } catch (err) {
        setError("Liaison backend perdue");
        setIsConnected(false);
        onCameraStatus?.(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 5000); // Reduce frequency to 5s to avoid hardware race conditions
    return () => clearInterval(interval);
  }, [API_URL, onCameraStatus]);

  // FPS calculation
  useEffect(() => {
    if (!isConnected || !onFpsUpdate) return;
    const calculateFps = () => {
      const currentTime = performance.now();
      const elapsed = currentTime - lastTimeRef.current;
      if (elapsed >= 1000) {
        const fps = Math.round((frameCountRef.current * 1000) / elapsed);
        onFpsUpdate(fps);
        frameCountRef.current = 0;
        lastTimeRef.current = currentTime;
      }
      frameCountRef.current++; // In backend mode, we just assume frames are flowing
      requestAnimationFrame(calculateFps);
    };
    const animationId = requestAnimationFrame(calculateFps);
    return () => cancelAnimationFrame(animationId);
  }, [isConnected, onFpsUpdate]);

  // Automatic camera cleanup on unmount
  useEffect(() => {
    return () => {
      // Use send function to notify backend to stop camera
      if (isWSConnected) {
        send("stop_camera");
      }
    };
  }, [send, isWSConnected]);

  return (
    <div className={cn("relative w-full h-full overflow-hidden bg-black rounded-3xl border border-white/10 shadow-2xl flex items-center justify-center", className)}>
      {/* Backend Stream Image */}
      {isConnected && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={`${API_URL}/video_feed`}
          alt="Live Feed"
          onError={(e) => {
            console.error("Video feed error:", e);
            setError("Erreur chargement vidéo backend");
            setIsConnected(false);
          }}
          className={cn(
            "absolute inset-0 w-full h-full object-contain",
            mirror && "scale-x-[-1]"
          )}
        />
      )}

      {/* Mode Status Badge */}
      <div className="absolute top-4 left-4 flex items-center gap-2 z-10">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full glass-panel border border-white/20">
          <Smartphone className="h-3.5 w-3.5 text-primary" />
          <span className="text-[10px] font-bold tracking-wider uppercase text-white">
            Mode Embarqué
          </span>
        </div>

        {/* AI Detection Status Badge */}
        {isConnected && (
          <div className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-full glass-panel border animate-in fade-in slide-in-from-top-2 duration-500",
            isPersonDetected ? "border-emerald-500/50 bg-emerald-500/10" : "border-rose-500/50 bg-rose-500/10"
          )}>
            {isPersonDetected ? (
              <UserCheck className="h-3.5 w-3.5 text-emerald-500" />
            ) : (
              <UserX className="h-3.5 w-3.5 text-rose-500" />
            )}
            <span className={cn(
              "text-[10px] font-bold tracking-wider uppercase",
              isPersonDetected ? "text-emerald-500" : "text-rose-500"
            )}>
              {isPersonDetected ? "Personne Détectée" : "Aucun Corps Détecté"}
            </span>
          </div>
        )}
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80 backdrop-blur-md z-20">
          <div className="text-center">
            <div className="w-12 h-12 rounded-full border-2 border-primary border-t-transparent animate-spin mx-auto mb-4" />
            <p className="text-sm font-medium text-white">
              Connexion au Raspberry...
            </p>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/90 backdrop-blur-md z-30">
          <div className="text-center p-8 max-w-md">
            <div className="w-20 h-20 rounded-3xl bg-destructive/20 flex items-center justify-center mx-auto mb-6 border border-destructive/30">
              <CameraOff className="h-10 w-10 text-destructive" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Erreur Caméra</h3>
            <p className="text-sm text-white/60 mb-8">{error}</p>

            <div className="flex flex-col gap-3">
              {!isCameraActive && (
                <button
                  onClick={() => {
                    send("start_camera", { camera_id: 0 });
                    setIsLoading(true);
                  }}
                  className="w-full px-6 py-3 rounded-2xl bg-emerald-500 text-white text-sm font-semibold hover:bg-emerald-600 transition-all flex items-center justify-center gap-2"
                >
                  <Power className="h-4 w-4" />
                  Démarrer la Caméra
                </button>
              )}
              <button
                onClick={() => window.location.reload()}
                className="w-full px-6 py-3 rounded-2xl bg-white/10 text-white text-sm font-semibold hover:bg-white/20 transition-all border border-white/10"
              >
                Actualiser la page
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Camera Off Placeholder */}
      {!isCameraActive && !isLoading && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-zinc-900/50 backdrop-blur-sm z-10">
          <div className="text-center">
            <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4 border border-white/10">
              <CameraOff className="h-10 w-10 text-white/20" />
            </div>
            <p className="text-white/40 font-medium mb-6 text-sm">Caméra inactive</p>
            <button
              onClick={() => {
                send("start_camera", { camera_id: 0 });
                setIsLoading(true);
              }}
              className="px-6 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 transition-all flex items-center gap-2 mx-auto"
            >
              <Power className="h-3.5 w-3.5" />
              Allumer
            </button>
          </div>
        </div>
      )}

      {/* Debug Toggle - Discretely placed */}
      <div className="absolute bottom-6 right-6 z-50">
        <button
          onClick={() => setIsDebugMode(!isDebugMode)}
          className={cn(
            "p-3 rounded-2xl transition-all glass-panel border border-white/10 shadow-xl",
            isDebugMode ? "bg-amber-500/20 text-amber-500 border-amber-500/50" : "text-white/40 hover:text-white"
          )}
          title="Toggle Debug Mode"
        >
          <Bug className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}

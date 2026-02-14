"use client";

import { useApp } from "@/lib/app-context";
import { useHardware } from "@/lib/use-backend";
import { Camera, Wifi, Battery, Gauge, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

export function StatusBar() {
  const { cameraConnected, fps, cameraError } = useApp();
  const hardware = useHardware();

  return (
    <div className="fixed top-0 left-0 right-0 z-50 glass-panel">
      <div className="flex items-center justify-between px-4 py-2 max-w-7xl mx-auto">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Gauge className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs font-medium text-muted-foreground">
              {fps} FPS
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Camera
              className={cn(
                "h-4 w-4",
                cameraConnected ? "text-primary" : "text-destructive"
              )}
            />
            <span
              className={cn(
                "text-xs font-medium",
                cameraConnected ? "text-primary" : "text-destructive"
              )}
            >
              {/* SHOW ERROR IF EXISTS, OTHERWISE STATUS: */}
              {cameraError || (cameraConnected ? "Camera Active" : "Camera Off")}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Wifi className={cn("h-4 w-4", hardware ? "text-primary" : "text-muted-foreground")} />
          </div>
          {hardware?.eco_mode && (
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-primary/10 border border-primary/20">
              <Zap className="h-3 w-3 text-primary animate-pulse" />
              <span className="text-[10px] font-bold text-primary uppercase">Eco</span>
            </div>
          )}
          <div className="flex items-center gap-1.5">
            <Battery className={cn(
              "h-4 w-4",
              (hardware?.battery_level || 0) < 20 ? "text-destructive" : "text-primary"
            )} />
            <span className="text-xs font-medium text-muted-foreground">
              {hardware ? `${Math.round(hardware.battery_level)}%` : "--%"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import React from "react"

import { useApp, Screen } from "@/lib/app-context";
import { cn } from "@/lib/utils";
import {
  Home,
  Zap,
  Dumbbell,
  Link2,
  BarChart3,
  Info,
  Crosshair,
} from "lucide-react";

const navItems: { id: Screen; label: string; icon: React.ElementType }[] = [
  { id: "home", label: "Home", icon: Home },
  { id: "calibration", label: "Calibration", icon: Crosshair },
  { id: "quick-start", label: "Quick Start", icon: Zap },
  { id: "manual-mode", label: "Manual", icon: Dumbbell },
  { id: "custom-chain", label: "Plan", icon: Link2 },
  { id: "stats", label: "Stats", icon: BarChart3 },
  { id: "about", label: "Tech", icon: Info },
];

export function Navigation() {
  const { currentScreen, setCurrentScreen, isSessionActive } = useApp();

  if (isSessionActive) return null;

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 glass-panel safe-area-inset-bottom">
      <div className="flex items-center justify-around px-2 py-2 max-w-2xl mx-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentScreen === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setCurrentScreen(item.id)}
              className={cn(
                "flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-all touch-target",
                isActive
                  ? "text-primary bg-primary/10"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              )}
            >
              <Icon className={cn("h-5 w-5", isActive && "glow-energy")} />
              <span className="text-[10px] font-medium">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

"use client";

import { useApp } from "@/lib/app-context";
import { StatusBar } from "./status-bar";
import { Navigation } from "./navigation";
import { HomeScreen } from "./screens/home-screen";
import { CalibrationScreen } from "./screens/calibration-screen";
import { QuickStartScreen } from "./screens/quick-start-screen";
import { ManualModeScreen } from "./screens/manual-mode-screen";
import { CustomChainScreen } from "./screens/custom-chain-screen";
import { StatsScreen } from "./screens/stats-screen";
import { AboutScreen } from "./screens/about-screen";

export function FitnessApp() {
  const { currentScreen } = useApp();

  const renderScreen = () => {
    switch (currentScreen) {
      case "home":
        return <HomeScreen />;
      case "calibration":
        return <CalibrationScreen />;
      case "quick-start":
        return <QuickStartScreen />;
      case "manual-mode":
        return <ManualModeScreen />;
      case "custom-chain":
        return <CustomChainScreen />;
      case "stats":
        return <StatsScreen />;
      case "about":
        return <AboutScreen />;
      default:
        return <HomeScreen />;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <StatusBar />
      {renderScreen()}
      <Navigation />
    </div>
  );
}

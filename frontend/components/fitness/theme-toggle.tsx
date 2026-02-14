"use client";

import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="w-14 h-8 rounded-full bg-muted border border-border" />
    );
  }

  const isDark = resolvedTheme === "dark";

  const handleToggle = () => {
    const newTheme = isDark ? "light" : "dark";
    console.log("[v0] Theme toggle clicked. Current:", resolvedTheme, "Setting to:", newTheme);
    setTheme(newTheme);
  };

  return (
    <button
      type="button"
      onClick={handleToggle}
      className={cn(
        "relative flex items-center justify-center w-14 h-8 rounded-full",
        "bg-muted border border-border transition-all duration-300",
        "hover:border-primary/50 cursor-pointer"
      )}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
    >
      <div
        className={cn(
          "absolute w-6 h-6 rounded-full bg-primary transition-transform duration-300 ease-out",
          isDark ? "translate-x-3" : "-translate-x-3"
        )}
      />
      <Sun
        className={cn(
          "absolute left-1.5 h-4 w-4 transition-opacity duration-300",
          isDark
            ? "opacity-50 text-muted-foreground"
            : "opacity-100 text-primary-foreground"
        )}
      />
      <Moon
        className={cn(
          "absolute right-1.5 h-4 w-4 transition-opacity duration-300",
          isDark
            ? "opacity-100 text-primary-foreground"
            : "opacity-50 text-muted-foreground"
        )}
      />
    </button>
  );
}

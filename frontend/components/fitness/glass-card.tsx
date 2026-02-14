"use client";

import React from "react"

import { cn } from "@/lib/utils";

type GlassCardProps = {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
};

export function GlassCard({
  children,
  className,
  hover = false,
  onClick,
}: GlassCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "glass-card rounded-2xl p-6 transition-all duration-300",
        hover && "card-glow cursor-pointer",
        onClick && "cursor-pointer",
        className
      )}
    >
      {children}
    </div>
  );
}

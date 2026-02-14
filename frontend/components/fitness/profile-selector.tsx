"use client";

import { useState } from "react";
import { useApp } from "@/lib/app-context";
import { GlassCard } from "./glass-card";
import { User, Plus, Check, UserPlus, X } from "lucide-react";
import { cn } from "@/lib/utils";

export function ProfileSelector() {
    const {
        userProfile,
        availableProfiles,
        switchToProfile,
        createProfile
    } = useApp();

    const [isAdding, setIsAdding] = useState(false);
    const [newName, setNewName] = useState("");
    const [isExpanded, setIsExpanded] = useState(false);

    const handleCreate = async () => {
        if (newName.trim()) {
            await createProfile(newName.trim());
            setNewName("");
            setIsAdding(false);
            setIsExpanded(false);
        }
    };

    return (
        <div className="relative">
            {/* Active Profile Trigger */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-3 px-4 py-2 rounded-2xl bg-secondary/10 hover:bg-secondary/20 transition-all border border-secondary/20"
            >
                <div className="w-8 h-8 rounded-full bg-secondary/20 flex items-center justify-center text-secondary">
                    <User className="h-4 w-4" />
                </div>
                <div className="text-left">
                    <p className="text-xs text-muted-foreground leading-none mb-1">User Profile</p>
                    <p className="text-sm font-semibold text-foreground leading-none">
                        {userProfile?.name || "Select Profile"}
                    </p>
                    {/* Add body type display here */}
                    {userProfile && (
                        <p className="text-xs text-muted-foreground mt-0.5 leading-none">
                            Body Type: {userProfile.body_type || "Not set"}
                        </p>
                    )}
                </div>
            </button>

            {/* Dropdown / Modal */}
            {isExpanded && (
                <>
                    <div
                        className="fixed inset-0 z-40 bg-black/20 backdrop-blur-[2px]"
                        onClick={() => setIsExpanded(false)}
                    />
                    <div className="absolute top-full left-0 mt-2 w-64 z-50 animate-in fade-in zoom-in-95 duration-200">
                        <GlassCard className="p-2 shadow-2xl border-secondary/20">
                            <div className="max-h-64 overflow-y-auto custom-scrollbar p-1">
                                {availableProfiles.map((profile) => (
                                    <button
                                        key={profile.id}
                                        onClick={() => {
                                            switchToProfile(profile.id);
                                            setIsExpanded(false);
                                        }}
                                        className={cn(
                                            "w-full flex items-center justify-between p-3 rounded-xl transition-all mb-1",
                                            userProfile?.id === profile.id
                                                ? "bg-secondary/20 text-secondary"
                                                : "hover:bg-muted/50 text-foreground"
                                        )}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center">
                                                <User className="h-4 w-4" />
                                            </div>
                                            <span className="text-sm font-medium">{profile.name}</span>
                                        </div>
                                        {userProfile?.id === profile.id && <Check className="h-4 w-4" />}
                                    </button>
                                ))}
                            </div>

                            <div className="mt-2 border-t border-border/50 pt-2">
                                {!isAdding ? (
                                    <button
                                        onClick={() => setIsAdding(true)}
                                        className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-primary/10 text-primary transition-all font-medium"
                                    >
                                        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                                            <UserPlus className="h-4 w-4" />
                                        </div>
                                        <span className="text-sm">New Profile</span>
                                    </button>
                                ) : (
                                    <div className="p-2 space-y-2">
                                        <div className="relative">
                                            <input
                                                autoFocus
                                                type="text"
                                                placeholder="Name..."
                                                value={newName}
                                                onChange={(e) => setNewName(e.target.value)}
                                                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                                                className="w-full bg-muted/50 border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                                            />
                                            <button
                                                onClick={() => setIsAdding(false)}
                                                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                            >
                                                <X className="h-3 w-3" />
                                            </button>
                                        </div>
                                        <button
                                            onClick={handleCreate}
                                            disabled={!newName.trim()}
                                            className="w-full bg-primary text-primary-foreground py-2 rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-all"
                                        >
                                            Create
                                        </button>
                                    </div>
                                )}
                            </div>
                        </GlassCard>
                    </div>
                </>
            )}
        </div>
    );
}

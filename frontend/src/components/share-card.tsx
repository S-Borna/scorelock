"use client";

import { useRef, useState } from "react";

interface ShareCardProps {
    /** "Du slog AI:n 7 av 10!" or similar */
    headline: string;
    /** E.g. "42p totalt · 85% träffsäkerhet" */
    subline?: string;
    /** Username */
    userName?: string;
    /** Variant: "ai-win" | "leaderboard" | "streak" */
    variant?: "ai-win" | "leaderboard" | "streak";
}

export function ShareCard({ headline, subline, userName, variant = "ai-win" }: ShareCardProps) {
    const cardRef = useRef<HTMLDivElement>(null);
    const [copied, setCopied] = useState(false);

    const gradients: Record<string, string> = {
        "ai-win": "from-scorelock-950/50 to-surface-950",
        leaderboard: "from-amber-950/30 to-surface-950",
        streak: "from-accent-purple/10 to-surface-950",
    };

    const icons: Record<string, string> = {
        "ai-win": "🤖",
        leaderboard: "🏆",
        streak: "🔥",
    };

    async function handleShare() {
        const text = `${headline}${subline ? ` — ${subline}` : ""} | ScoreLock`;

        if (navigator.share) {
            try {
                await navigator.share({
                    title: "ScoreLock",
                    text,
                    url: typeof window !== "undefined" ? window.location.href : "",
                });
                return;
            } catch {
                // User cancelled or not supported — fall through to clipboard
            }
        }

        // Fallback: copy to clipboard
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch {
            // Silent fail
        }
    }

    return (
        <div className="space-y-3">
            {/* Visual card */}
            <div
                ref={cardRef}
                className={`bg-gradient-to-br ${gradients[variant]} rounded-2xl p-6 border border-white/[0.06] shadow-card`}
            >
                <div className="flex items-start gap-3">
                    <span className="text-4xl">{icons[variant]}</span>
                    <div className="flex-1 min-w-0">
                        <p className="text-xl font-bold leading-tight">{headline}</p>
                        {subline && (
                            <p className="text-gray-400 text-sm mt-1">{subline}</p>
                        )}
                        {userName && (
                            <p className="text-gray-500 text-xs mt-2">— {userName}</p>
                        )}
                    </div>
                </div>
                <div className="flex items-center justify-between mt-4 pt-3 border-t border-white/[0.06]">
                    <span className="text-scorelock-400 font-semibold text-sm tracking-wide">
                        SCORELOCK
                    </span>
                    <span className="text-gray-600 text-xs">scorelock.se</span>
                </div>
            </div>

            {/* Share button */}
            <button
                onClick={handleShare}
                className="w-full btn-primary py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2"
            >
                {copied ? (
                    <>✓ Kopierat!</>
                ) : (
                    <>
                        <svg
                            className="w-4 h-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                            />
                        </svg>
                        Dela resultat
                    </>
                )}
            </button>
        </div>
    );
}

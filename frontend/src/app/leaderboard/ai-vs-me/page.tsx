"use client";

import { ShareCard } from "@/components/share-card";
import { fetchApiAuth } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-token";
import type { AIvsUserStats } from "@/lib/types";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function AIvsMePage() {
    const [stats, setStats] = useState<AIvsUserStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const token = getAccessToken();
        if (!token) {
            setError("login");
            setLoading(false);
            return;
        }

        fetchApiAuth<AIvsUserStats>("/api/v1/tips/ai-vs-me", token)
            .then(setStats)
            .catch(() => setError("fetch"))
            .finally(() => setLoading(false));
    }, []);

    if (loading) {
        return (
            <div className="max-w-3xl mx-auto px-4 py-8 space-y-4">
                <div className="h-8 w-48 bg-gray-800 rounded animate-pulse" />
                <div className="h-64 bg-gray-800 rounded animate-pulse" />
            </div>
        );
    }

    if (error === "login") {
        return (
            <div className="max-w-3xl mx-auto px-4 py-8 text-center">
                <p className="text-4xl mb-4">🔒</p>
                <h1 className="text-2xl font-bold mb-2">Logga in först</h1>
                <p className="text-gray-400 mb-6">
                    Du måste vara inloggad för att se din statistik mot AI:n.
                </p>
                <Link
                    href="/login"
                    className="btn-primary inline-block px-6 py-2 rounded"
                >
                    Logga in
                </Link>
            </div>
        );
    }

    if (!stats || error) {
        return (
            <div className="max-w-3xl mx-auto px-4 py-8 text-center">
                <p className="text-4xl mb-4">⚠️</p>
                <p className="text-gray-400">Kunde inte ladda din statistik. Försök igen senare.</p>
            </div>
        );
    }

    const totalMatches = stats.user_wins + stats.ai_wins + stats.ties;
    const userWinRate = totalMatches > 0 ? Math.round((stats.user_wins / totalMatches) * 100) : 0;
    const aiWinRate = totalMatches > 0 ? Math.round((stats.ai_wins / totalMatches) * 100) : 0;
    const userLeading = stats.user_wins > stats.ai_wins;
    const tied = stats.user_wins === stats.ai_wins;

    return (
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Link
                href="/leaderboard"
                className="text-sm text-gray-500 hover:text-gray-300 mb-4 inline-block"
            >
                ← Tillbaka till topplistan
            </Link>

            <h1 className="text-3xl font-bold mb-2">🤖 AI vs Du</h1>
            <p className="text-gray-400 mb-8">
                Se hur dina tips står sig mot ScoreLocks AI-modell, match för match.
            </p>

            {totalMatches === 0 ? (
                <div className="card text-center py-12">
                    <p className="text-4xl mb-4">🏟️</p>
                    <p className="text-gray-400 text-lg mb-2">Inga avgjorda matcher ännu</p>
                    <p className="text-gray-600 text-sm">
                        Tippa på kommande matcher så jämför vi dina resultat mot AI:n efter avspark.
                    </p>
                    <Link
                        href="/matches"
                        className="inline-block mt-4 text-scorelock-400 hover:underline text-sm"
                    >
                        Se matcher →
                    </Link>
                </div>
            ) : (
                <>
                    {/* Score banner */}
                    <div className="card border-scorelock-900/50 bg-scorelock-950/10 mb-8">
                        <div className="text-center">
                            <p className="text-sm text-gray-500 mb-2">Ställningen</p>
                            <div className="flex items-center justify-center gap-6 text-3xl font-bold">
                                <div className="text-center">
                                    <p className={userLeading ? "text-green-400" : "text-white"}>
                                        {stats.user_wins}
                                    </p>
                                    <p className="text-xs text-gray-500 font-normal mt-1">Du</p>
                                </div>
                                <span className="text-gray-600">–</span>
                                <div className="text-center">
                                    <p className="text-gray-500">{stats.ties}</p>
                                    <p className="text-xs text-gray-500 font-normal mt-1">Lika</p>
                                </div>
                                <span className="text-gray-600">–</span>
                                <div className="text-center">
                                    <p className={!userLeading && !tied ? "text-red-400" : "text-white"}>
                                        {stats.ai_wins}
                                    </p>
                                    <p className="text-xs text-gray-500 font-normal mt-1">AI</p>
                                </div>
                            </div>
                            <p className="text-sm text-gray-500 mt-3">
                                {tied
                                    ? "Helt jämnt! Kan du ta ledningen?"
                                    : userLeading
                                        ? "Du leder — fortsätt så! 🔥"
                                        : "AI:n leder — dags att slå tillbaka!"}
                            </p>
                        </div>
                    </div>

                    {/* Detailed stats */}
                    <div className="grid sm:grid-cols-2 gap-4 mb-8">
                        {/* Your stats */}
                        <div className="card">
                            <h3 className="text-lg font-semibold mb-4">👤 Dina resultat</h3>
                            <div className="space-y-3 text-sm">
                                <StatRow label="Totala tips" value={stats.user_total_tips} />
                                <StatRow label="Totalpoäng" value={stats.user_total_points} accent />
                                <StatRow label="Träffsäkerhet" value={`${stats.user_accuracy}%`} />
                                <StatRow label="Vinster mot AI" value={stats.user_wins} />
                                <StatRow label="Vinstgrad" value={`${userWinRate}%`} />
                            </div>
                        </div>

                        {/* AI stats */}
                        <div className="card">
                            <h3 className="text-lg font-semibold mb-4">🤖 AI:ns resultat</h3>
                            <div className="space-y-3 text-sm">
                                <StatRow label="Matcher analyserade" value={stats.ai_total} />
                                <StatRow label="Korrekta" value={stats.ai_correct} accent />
                                <StatRow label="Träffsäkerhet" value={`${stats.ai_accuracy}%`} />
                                <StatRow label="Vinster mot dig" value={stats.ai_wins} />
                                <StatRow label="Vinstgrad" value={`${aiWinRate}%`} />
                            </div>
                        </div>
                    </div>

                    {/* Share prompt */}
                    <div className="card border-gray-800">
                        <ShareCard
                            headline={
                                userLeading
                                    ? `Jag slog AI:n ${stats.user_wins} av ${totalMatches} gånger!`
                                    : tied
                                        ? `Jag ligger lika med AI:n — ${stats.user_wins} av ${totalMatches}!`
                                        : `AI:n leder ${stats.ai_wins}–${stats.user_wins} men jag ger inte upp!`
                            }
                            subline={`${stats.user_total_points}p totalt · ${stats.user_accuracy}% träffsäkerhet`}
                            variant={userLeading ? "ai-win" : "streak"}
                        />
                    </div>
                </>
            )}
        </div>
    );
}

function StatRow({
    label,
    value,
    accent = false,
}: {
    label: string;
    value: string | number;
    accent?: boolean;
}) {
    return (
        <div className="flex justify-between items-center">
            <span className="text-gray-400">{label}</span>
            <span className={accent ? "font-bold text-scorelock-400" : "font-medium"}>
                {value}
            </span>
        </div>
    );
}

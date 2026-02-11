"use client";

import { useEffect, useState } from "react";
import type { FixtureDetail } from "@/lib/types";
import { useLiveScores } from "@/lib/use-live-scores";
import { formatKickoff, getStatusClass } from "@/lib/utils";

interface LiveMatchHeaderProps {
    fixture: FixtureDetail;
}

/**
 * Live-updating match header with real-time score, minute ticker,
 * and goal animations.
 */
export function LiveMatchHeader({ fixture }: LiveMatchHeaderProps) {
    const { getLiveState } = useLiveScores([fixture]);
    const liveState = getLiveState(fixture);

    const homeGoals = liveState?.homeGoals ?? fixture.home_goals;
    const awayGoals = liveState?.awayGoals ?? fixture.away_goals;
    const status = liveState?.status ?? fixture.status;
    const minute = liveState?.minute;
    const goalJustScored = liveState?.goalJustScored ?? false;
    const goalSide = liveState?.goalSide;

    const isLive = status === "live" || status === "halftime";

    return (
        <div
            className={`card mb-8 relative overflow-hidden transition-all duration-500 ${goalJustScored ? "animate-goal-flash" : ""
                }`}
        >
            {/* Goal flash overlay */}
            {goalJustScored && (
                <div className="absolute inset-0 bg-gradient-to-r from-green-500/10 via-green-500/5 to-transparent animate-goal-wave pointer-events-none z-10" />
            )}

            <div className="flex items-center justify-between mb-2">
                <a
                    href="/standings"
                    className="text-sm text-gray-500 hover:text-scorelock-400"
                >
                    {fixture.league.name} · {fixture.round}
                </a>
                <div className="flex items-center gap-2">
                    {isLive && minute !== null && (
                        <span className="font-mono text-sm text-red-400 animate-minute-tick">
                            {minute}&apos;
                        </span>
                    )}
                    <span className={getStatusClass(status)}>
                        {isLive && status !== "halftime" && "● "}
                        {status === "halftime" ? "HT" : status.toUpperCase()}
                    </span>
                </div>
            </div>

            <div className="flex items-center justify-between py-6">
                <TeamDisplay
                    name={fixture.home_team.name}
                    logoUrl={fixture.home_team.logo_url}
                    goalScored={goalJustScored && goalSide === "home"}
                />
                <div className="text-center">
                    {homeGoals !== null && awayGoals !== null ? (
                        <div
                            className={`text-4xl font-bold font-mono tabular-nums transition-all duration-300 ${goalJustScored
                                    ? "text-green-400 animate-score-pop"
                                    : ""
                                }`}
                        >
                            {homeGoals} – {awayGoals}
                        </div>
                    ) : (
                        <div className="text-2xl text-gray-500">vs</div>
                    )}
                    <div className="text-xs text-gray-500 mt-2">
                        {formatKickoff(fixture.kickoff)}
                    </div>
                    {/* Halftime score */}
                    {fixture.home_goals_ht !== null &&
                        fixture.away_goals_ht !== null && (
                            <div className="text-xs text-gray-600 mt-1">
                                HT: {fixture.home_goals_ht} – {fixture.away_goals_ht}
                            </div>
                        )}
                </div>
                <TeamDisplay
                    name={fixture.away_team.name}
                    logoUrl={fixture.away_team.logo_url}
                    goalScored={goalJustScored && goalSide === "away"}
                />
            </div>

            {/* Live match progress bar */}
            {isLive && minute !== null && (
                <div className="mt-2">
                    <div className="h-1 bg-white/[0.06] rounded-full overflow-hidden">
                        <div
                            className="h-full bg-gradient-to-r from-red-500 to-red-400 rounded-full transition-all duration-1000"
                            style={{
                                width: `${Math.min(((minute ?? 0) / 90) * 100, 100)}%`,
                            }}
                        />
                    </div>
                    <div className="flex justify-between text-[10px] text-gray-600 mt-1">
                        <span>0&apos;</span>
                        <span>45&apos;</span>
                        <span>90&apos;</span>
                    </div>
                </div>
            )}
        </div>
    );
}

function TeamDisplay({
    name,
    logoUrl,
    goalScored,
}: {
    name: string;
    logoUrl: string | null;
    goalScored?: boolean;
}) {
    return (
        <div className="flex flex-col items-center gap-2 w-28 sm:w-32">
            {logoUrl ? (
                <img
                    src={logoUrl}
                    alt={name}
                    className={`w-14 h-14 sm:w-16 sm:h-16 object-contain transition-transform duration-500 ${goalScored ? "scale-110" : ""
                        }`}
                />
            ) : (
                <div className="w-14 h-14 sm:w-16 sm:h-16 bg-white/[0.04] rounded-full flex items-center justify-center text-2xl">
                    ⚽
                </div>
            )}
            <span
                className={`text-sm font-medium text-center transition-colors duration-300 ${goalScored ? "text-green-400 font-semibold" : ""
                    }`}
            >
                {name}
            </span>
        </div>
    );
}

/**
 * Auto-refreshing match stats widget.
 * Polls the fixture detail endpoint every 30s during live matches.
 */
export function LiveMatchStats({ fixtureId }: { fixtureId: number }) {
    const [stats, setStats] = useState<Record<string, unknown> | null>(null);
    const [isLive, setIsLive] = useState(false);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const apiBase =
                    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
                const resp = await fetch(
                    `${apiBase}/api/v1/fixtures/${fixtureId}`,
                    { signal: AbortSignal.timeout(5000) },
                );
                if (resp.ok) {
                    const data: FixtureDetail = await resp.json();
                    setStats(data.stats);
                    setIsLive(
                        data.status === "live" || data.status === "halftime",
                    );
                }
            } catch {
                /* ignore */
            }
        };

        fetchStats();
        const interval = setInterval(fetchStats, 30000);
        return () => clearInterval(interval);
    }, [fixtureId]);

    if (!stats || Object.keys(stats).length === 0) return null;

    return (
        <div className="card">
            <h2 className="text-base font-semibold mb-4 text-white flex items-center gap-2">
                📊 Matchstatistik
                {isLive && (
                    <span className="badge-live text-[10px]">LIVE</span>
                )}
            </h2>
            <div className="space-y-3">
                {Object.entries(stats).map(([key, value]) => (
                    <StatRow key={key} label={key} value={String(value)} />
                ))}
            </div>
        </div>
    );
}

function StatRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400 capitalize">
                {label.replace(/_/g, " ")}
            </span>
            <span className="font-mono text-white">{value}</span>
        </div>
    );
}

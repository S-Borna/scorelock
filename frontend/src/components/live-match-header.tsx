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

    // VM-chip: "Grupp F · Omgång 1" när stage-data finns (omgång plockas ur round-etiketten).
    const omgang = fixture.round?.match(/Omgång\s*\d+/)?.[0] ?? null;
    const stageLabel = fixture.stage_name
        ? [
              fixture.group_letter
                  ? `Grupp ${fixture.group_letter}`
                  : fixture.stage_name,
              omgang,
          ]
              .filter(Boolean)
              .join(" · ")
        : null;

    return (
        <div
            className={`relative mb-8 overflow-hidden rounded-2xl border border-white/[0.07] bg-surface-900/80 backdrop-blur-sm shadow-elevated transition-all duration-500 ${goalJustScored ? "animate-goal-flash" : ""}`}
        >
            {/* Atmosfär — subtil radial som ger kortet tyngd */}
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(120%_130%_at_50%_-20%,rgba(9,206,95,0.10),transparent_55%)]" />
            {goalJustScored && (
                <div className="absolute inset-0 bg-gradient-to-r from-green-500/10 via-green-500/5 to-transparent animate-goal-wave pointer-events-none z-10" />
            )}

            <div className="relative p-4 sm:p-6 md:p-8 overflow-hidden">
                {/* Liga-rad med logga + status */}
                <div className="flex items-center justify-between mb-5 sm:mb-7 gap-2">
                    <a href="/standings" className="flex items-center gap-2 text-xs sm:text-sm text-gray-400 hover:text-scorelock-400 transition-colors min-w-0">
                        {fixture.league.logo_url && (
                            <img src={fixture.league.logo_url} alt="" className="w-4 h-4 sm:w-5 sm:h-5 object-contain flex-shrink-0" />
                        )}
                        <span className="font-medium text-gray-300 truncate">{fixture.league.name}</span>
                        {fixture.round && !stageLabel && <span className="text-gray-600 truncate">· {fixture.round}</span>}
                    </a>
                    <div className="flex items-center gap-2 flex-shrink-0">
                        {stageLabel && (
                            <span className="inline-flex items-center rounded-full border border-yellow-400/25 bg-gradient-to-r from-blue-900/70 to-blue-950/70 px-2.5 py-0.5 text-[10px] sm:text-[11px] font-medium uppercase tracking-wider text-yellow-300 whitespace-nowrap">
                                {stageLabel}
                            </span>
                        )}
                        {isLive && minute !== null && (
                            <span className="font-mono text-xs sm:text-sm font-bold text-red-400 animate-minute-tick">{minute}&apos;</span>
                        )}
                        <span className={isLive ? "badge-live" : `badge ${getStatusClass(status)}`}>
                            {status === "halftime" ? "HT" : status === "finished" ? "Slut" : status === "scheduled" ? "Kommande" : status.toUpperCase()}
                        </span>
                    </div>
                </div>

                {/* Scoreboard — stora crests, fet scoreline */}
                <div className="flex items-start justify-between gap-1 sm:gap-2">
                    <TeamDisplay
                        name={fixture.home_team.short_name ?? fixture.home_team.name}
                        logoUrl={fixture.home_team.logo_url}
                        goalScored={goalJustScored && goalSide === "home"}
                    />
                    <div className="text-center px-0 sm:px-1 pt-2 sm:pt-3 flex-shrink-0">
                        {homeGoals !== null && awayGoals !== null ? (
                            <div className={`text-4xl sm:text-5xl md:text-6xl font-bold font-mono tabular-nums leading-none transition-all duration-300 ${goalJustScored ? "text-green-400 animate-score-pop" : "text-white"}`}>
                                {homeGoals}<span className="text-gray-600 mx-1 sm:mx-2">–</span>{awayGoals}
                            </div>
                        ) : (
                            <div className="text-2xl sm:text-3xl font-display italic text-gray-500">vs</div>
                        )}
                        <div className="text-[10px] sm:text-xs text-gray-500 mt-2 sm:mt-3 font-mono whitespace-nowrap">{formatKickoff(fixture.kickoff)}</div>
                        {fixture.home_goals_ht !== null && fixture.away_goals_ht !== null && (
                            <div className="text-[10px] sm:text-[11px] text-gray-600 mt-1">HT {fixture.home_goals_ht}–{fixture.away_goals_ht}</div>
                        )}
                    </div>
                    <TeamDisplay
                        name={fixture.away_team.short_name ?? fixture.away_team.name}
                        logoUrl={fixture.away_team.logo_url}
                        goalScored={goalJustScored && goalSide === "away"}
                    />
                </div>

                {/* Live-progress */}
                {isLive && minute !== null && (
                    <div className="mt-7">
                        <div className="h-1 bg-white/[0.06] rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-red-500 to-red-400 rounded-full transition-all duration-1000"
                                style={{ width: `${Math.min(((minute ?? 0) / 90) * 100, 100)}%` }} />
                        </div>
                        <div className="flex justify-between text-[10px] text-gray-600 mt-1 font-mono">
                            <span>0&apos;</span><span>45&apos;</span><span>90&apos;</span>
                        </div>
                    </div>
                )}
            </div>
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
        <div className="flex flex-col items-center gap-2 sm:gap-3 w-20 sm:w-28 md:w-36 min-w-0 flex-shrink">
            <div className={`flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 md:w-24 md:h-24 rounded-2xl bg-white/[0.03] border border-white/[0.05] transition-transform duration-500 ${goalScored ? "scale-110" : ""}`}>
                {logoUrl ? (
                    <img src={logoUrl} alt={name} className="w-11 h-11 sm:w-14 sm:h-14 md:w-16 md:h-16 object-contain" />
                ) : (
                    <span className="text-2xl sm:text-3xl">⚽</span>
                )}
            </div>
            <span className={`text-xs sm:text-sm md:text-lg font-semibold md:font-display md:tracking-tight text-center leading-tight transition-colors duration-300 break-words ${goalScored ? "text-green-400" : "text-gray-200"}`}>
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

"use client";

import type { Fixture, League, Prediction, ValueBet } from "@/lib/types";
import { useLiveScores } from "@/lib/use-live-scores";
import { useEffect, useState } from "react";

interface MatchesClientProps {
    initialFixtures: Fixture[];
    predictions: Prediction[];
    valueBets: ValueBet[];
}

// League display order (top leagues first)
const LEAGUE_ORDER: Record<string, number> = {
    "Premier League": 1,
    "premier_league": 1,
    "La Liga": 2,
    "la_liga": 2,
    "Serie A": 3,
    "serie_a": 3,
    "Bundesliga": 4,
    "bundesliga": 4,
    "Ligue 1": 5,
    "ligue_1": 5,
    "Champions League": 6,
    "champions_league": 6,
    "Europa League": 7,
    "europa_league": 7,
    "Conference League": 8,
    "conference_league": 8,
    "Allsvenskan": 9,
    "allsvenskan": 9,
};

type TabKey = "live" | "upcoming" | "finished";

/**
 * Flashscore-style matches page — fixtures grouped by league.
 */
export function MatchesClient({
    initialFixtures,
    predictions,
    valueBets,
}: MatchesClientProps) {
    const [fixtures, setFixtures] = useState(initialFixtures);
    const { getLiveState } = useLiveScores(initialFixtures);
    const [activeTab, setActiveTab] = useState<TabKey>("upcoming");
    const [collapsedLeagues, setCollapsedLeagues] = useState<Set<number>>(new Set());

    // Auto-refresh every 60s
    useEffect(() => {
        const interval = setInterval(async () => {
            try {
                const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
                const resp = await fetch(`${apiBase}/api/v1/fixtures`, {
                    signal: AbortSignal.timeout(5000),
                });
                if (resp.ok) {
                    const data: Fixture[] = await resp.json();
                    setFixtures(data);
                }
            } catch { /* ignore */ }
        }, 60000);
        return () => clearInterval(interval);
    }, []);

    const predMap = new Map(predictions.map((p) => [p.fixture_id, p]));
    const vbMap = new Map(valueBets.map((vb) => [vb.fixture.id, vb]));

    const live = fixtures.filter((f) => f.status === "live" || f.status === "halftime");
    const scheduled = fixtures.filter((f) => f.status === "scheduled")
        .sort((a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime());
    const finished = fixtures.filter((f) => f.status === "finished")
        .sort((a, b) => new Date(b.kickoff).getTime() - new Date(a.kickoff).getTime());

    // Auto-switch to live tab when there are live matches
    useEffect(() => {
        if (live.length > 0) setActiveTab("live");
    }, [live.length]);

    const currentFixtures =
        activeTab === "live" ? live :
        activeTab === "upcoming" ? scheduled :
        finished.slice(0, 100);

    // Group by league
    const leagueGroups = groupByLeague(currentFixtures);

    const toggleLeague = (leagueId: number) => {
        setCollapsedLeagues((prev) => {
            const next = new Set(prev);
            if (next.has(leagueId)) next.delete(leagueId);
            else next.add(leagueId);
            return next;
        });
    };

    return (
        <div className="max-w-3xl mx-auto px-4 py-6">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-2xl font-bold mb-1">Matcher</h1>
                <p className="text-sm text-gray-500">
                    Live resultat, kommande matcher och AI-analys
                </p>
            </div>

            {/* Tab bar */}
            <div className="flex gap-1 mb-5 bg-white/[0.03] p-1 rounded-xl border border-white/[0.06]">
                <TabButton
                    active={activeTab === "live"}
                    onClick={() => setActiveTab("live")}
                    count={live.length}
                    isLive
                >
                    Live
                </TabButton>
                <TabButton
                    active={activeTab === "upcoming"}
                    onClick={() => setActiveTab("upcoming")}
                    count={scheduled.length}
                >
                    Kommande
                </TabButton>
                <TabButton
                    active={activeTab === "finished"}
                    onClick={() => setActiveTab("finished")}
                    count={finished.length}
                >
                    Resultat
                </TabButton>
            </div>

            {/* League groups */}
            {leagueGroups.length === 0 ? (
                <div className="text-center py-16">
                    <div className="w-14 h-14 rounded-2xl bg-white/[0.03] flex items-center justify-center text-2xl mx-auto mb-3">
                        {activeTab === "live" ? "📡" : activeTab === "upcoming" ? "📅" : "✅"}
                    </div>
                    <p className="text-gray-500 text-sm">
                        {activeTab === "live"
                            ? "Inga livematcher just nu"
                            : activeTab === "upcoming"
                            ? "Inga kommande matcher"
                            : "Inga resultat"}
                    </p>
                </div>
            ) : (
                <div className="space-y-3">
                    {leagueGroups.map(({ league, fixtures: groupFixtures }) => {
                        const collapsed = collapsedLeagues.has(league.id);
                        return (
                            <div
                                key={league.id}
                                className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden"
                            >
                                {/* League header */}
                                <button
                                    onClick={() => toggleLeague(league.id)}
                                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/[0.03] transition-colors"
                                >
                                    {league.logo_url ? (
                                        <img
                                            src={league.logo_url}
                                            alt=""
                                            className="w-5 h-5 object-contain flex-shrink-0"
                                        />
                                    ) : (
                                        <div className="w-5 h-5 rounded bg-white/[0.06] flex items-center justify-center flex-shrink-0">
                                            <span className="text-[10px]">🏆</span>
                                        </div>
                                    )}
                                    <div className="flex items-center gap-2 min-w-0">
                                        <span className="font-semibold text-sm text-white truncate">
                                            {league.name}
                                        </span>
                                        {league.country && (
                                            <span className="text-xs text-gray-500 hidden sm:inline">
                                                {league.country}
                                            </span>
                                        )}
                                    </div>
                                    <span className="ml-auto text-xs text-gray-500">
                                        {groupFixtures.length}
                                    </span>
                                    <svg
                                        className={`w-4 h-4 text-gray-500 transition-transform ${collapsed ? "" : "rotate-180"}`}
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                        strokeWidth={2}
                                    >
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                                    </svg>
                                </button>

                                {/* Match rows */}
                                {!collapsed && (
                                    <div className="border-t border-white/[0.04]">
                                        {groupFixtures.map((f) => (
                                            <MatchRow
                                                key={f.id}
                                                fixture={f}
                                                prediction={predMap.get(f.id)}
                                                valueBet={vbMap.get(f.id)}
                                                liveState={getLiveState(f)}
                                            />
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

/* ── Compact match row (flashscore style) ─────────────── */

import type { LiveFixtureState } from "@/lib/use-live-scores";

function MatchRow({
    fixture,
    prediction,
    valueBet,
    liveState,
}: {
    fixture: Fixture;
    prediction?: Prediction;
    valueBet?: ValueBet;
    liveState?: LiveFixtureState | null;
}) {
    const homeGoals = liveState?.homeGoals ?? fixture.home_goals;
    const awayGoals = liveState?.awayGoals ?? fixture.away_goals;
    const status = liveState?.status ?? fixture.status;
    const minute = liveState?.minute;
    const isLive = status === "live" || status === "halftime";
    const isFinished = status === "finished";
    const homeWin = isFinished && (homeGoals ?? 0) > (awayGoals ?? 0);
    const awayWin = isFinished && (awayGoals ?? 0) > (homeGoals ?? 0);

    const kickoff = new Date(fixture.kickoff);
    const timeStr = kickoff.toLocaleTimeString("sv-SE", { hour: "2-digit", minute: "2-digit" });
    const dateStr = kickoff.toLocaleDateString("sv-SE", { day: "numeric", month: "short" });

    return (
        <a
            href={`/matches/${fixture.id}`}
            className="flex items-center px-4 py-2.5 hover:bg-white/[0.03] transition-colors border-b border-white/[0.03] last:border-b-0 group"
        >
            {/* Time / Status column */}
            <div className="w-14 flex-shrink-0 text-center mr-3">
                {isLive ? (
                    <div className="flex flex-col items-center">
                        <span className="text-xs font-bold text-red-400">
                            {minute ? `${minute}'` : status === "halftime" ? "HT" : "LIVE"}
                        </span>
                    </div>
                ) : isFinished ? (
                    <span className="text-xs text-gray-500">FT</span>
                ) : (
                    <div className="flex flex-col items-center">
                        <span className="text-xs font-medium text-gray-300">{timeStr}</span>
                        <span className="text-[10px] text-gray-600">{dateStr}</span>
                    </div>
                )}
            </div>

            {/* Teams */}
            <div className="flex-1 min-w-0 space-y-1">
                {/* Home */}
                <div className="flex items-center gap-2">
                    {fixture.home_team.logo_url ? (
                        <img src={fixture.home_team.logo_url} alt="" className="w-4 h-4 object-contain flex-shrink-0" />
                    ) : (
                        <div className="w-4 h-4 rounded-full bg-white/[0.06] flex-shrink-0" />
                    )}
                    <span className={`text-sm truncate ${homeWin ? "font-semibold text-white" : "text-gray-300"}`}>
                        {fixture.home_team.name}
                    </span>
                </div>
                {/* Away */}
                <div className="flex items-center gap-2">
                    {fixture.away_team.logo_url ? (
                        <img src={fixture.away_team.logo_url} alt="" className="w-4 h-4 object-contain flex-shrink-0" />
                    ) : (
                        <div className="w-4 h-4 rounded-full bg-white/[0.06] flex-shrink-0" />
                    )}
                    <span className={`text-sm truncate ${awayWin ? "font-semibold text-white" : "text-gray-300"}`}>
                        {fixture.away_team.name}
                    </span>
                </div>
            </div>

            {/* Score */}
            {(isLive || isFinished) && homeGoals !== null && awayGoals !== null ? (
                <div className="w-10 flex-shrink-0 text-right space-y-1">
                    <div className={`text-sm font-mono tabular-nums ${isLive ? "text-red-400 font-bold" : homeWin ? "font-bold text-white" : "text-gray-400"}`}>
                        {homeGoals}
                    </div>
                    <div className={`text-sm font-mono tabular-nums ${isLive ? "text-red-400 font-bold" : awayWin ? "font-bold text-white" : "text-gray-400"}`}>
                        {awayGoals}
                    </div>
                </div>
            ) : (
                <div className="w-10 flex-shrink-0 text-right">
                    <span className="text-xs text-gray-600">—</span>
                </div>
            )}

            {/* Value bet indicator */}
            {valueBet && valueBet.edge_percent > 0 && (
                <div className="ml-2 flex-shrink-0">
                    <span className="inline-block w-2 h-2 rounded-full bg-scorelock-500" title={`Value: +${valueBet.edge_percent.toFixed(0)}%`} />
                </div>
            )}

            {/* Arrow */}
            <svg
                className="w-4 h-4 text-gray-700 group-hover:text-gray-400 transition-colors ml-2 flex-shrink-0 hidden sm:block"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
            >
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
        </a>
    );
}

/* ── Helpers ──────────────────────────────────────────── */

function groupByLeague(fixtures: Fixture[]): { league: League; fixtures: Fixture[] }[] {
    const map = new Map<number, { league: League; fixtures: Fixture[] }>();

    for (const f of fixtures) {
        const existing = map.get(f.league.id);
        if (existing) {
            existing.fixtures.push(f);
        } else {
            map.set(f.league.id, { league: f.league, fixtures: [f] });
        }
    }

    return Array.from(map.values()).sort((a, b) => {
        const orderA = LEAGUE_ORDER[a.league.name] ?? 99;
        const orderB = LEAGUE_ORDER[b.league.name] ?? 99;
        return orderA - orderB;
    });
}

function TabButton({
    active,
    onClick,
    count,
    isLive,
    children,
}: {
    active: boolean;
    onClick: () => void;
    count: number;
    isLive?: boolean;
    children: React.ReactNode;
}) {
    return (
        <button
            onClick={onClick}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                active
                    ? "bg-white/[0.08] text-white shadow-sm"
                    : "text-gray-400 hover:text-gray-300 hover:bg-white/[0.03]"
            }`}
        >
            {isLive && count > 0 && (
                <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
            )}
            {children}
            {count > 0 && (
                <span className={`text-xs px-1.5 py-0.5 rounded-md ${
                    active
                        ? isLive ? "bg-red-500/20 text-red-400" : "bg-white/[0.08] text-gray-300"
                        : "bg-white/[0.04] text-gray-500"
                }`}>
                    {count}
                </span>
            )}
        </button>
    );
}

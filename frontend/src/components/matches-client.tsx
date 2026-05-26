"use client";

import type { Fixture, League, Prediction, ValueBet } from "@/lib/types";
import { useLiveScores, type LiveFixtureState } from "@/lib/use-live-scores";
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

// ── Datum-helpers (dag-axeln) ──────────────────────────────
function startOfDay(d: Date): Date {
    const x = new Date(d);
    x.setHours(0, 0, 0, 0);
    return x;
}
function addDays(d: Date, n: number): Date {
    const x = new Date(d);
    x.setDate(x.getDate() + n);
    return startOfDay(x);
}
function sameDay(a: Date, b: Date): boolean {
    return startOfDay(a).getTime() === startOfDay(b).getTime();
}
function dayLabel(d: Date, today: Date): string {
    const diff = Math.round((startOfDay(d).getTime() - today.getTime()) / 86_400_000);
    if (diff === 0) return "Idag";
    if (diff === -1) return "Igår";
    if (diff === 1) return "Imorgon";
    return d.toLocaleDateString("sv-SE", { weekday: "short", day: "numeric", month: "short" });
}
function toInputValue(d: Date): string {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/**
 * Matchsida — dag-axel (datum-strip) som primär navigation, matcher grupperade
 * per liga inom dagen, live-matcher pinnade överst oavsett vald dag.
 */
export function MatchesClient({
    initialFixtures,
    predictions,
    valueBets,
}: MatchesClientProps) {
    const [fixtures, setFixtures] = useState(initialFixtures);
    const { getLiveState } = useLiveScores(initialFixtures);
    const [today] = useState(() => startOfDay(new Date()));
    const [selectedDate, setSelectedDate] = useState<Date>(() => startOfDay(new Date()));
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
    const liveIds = new Set(live.map((f) => f.id));

    // Matcher på vald dag (live exkluderade — de pinnas separat överst).
    const dayFixtures = fixtures
        .filter((f) => !liveIds.has(f.id) && sameDay(new Date(f.kickoff), selectedDate))
        .sort((a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime());
    const dayGroups = groupByLeague(dayFixtures);
    const isToday = sameDay(selectedDate, today);

    const toggleLeague = (leagueId: number) => {
        setCollapsedLeagues((prev) => {
            const next = new Set(prev);
            if (next.has(leagueId)) next.delete(leagueId);
            else next.add(leagueId);
            return next;
        });
    };

    const renderRow = (f: Fixture) => (
        <MatchRow
            key={f.id}
            fixture={f}
            prediction={predMap.get(f.id)}
            valueBet={vbMap.get(f.id)}
            liveState={getLiveState(f)}
        />
    );

    return (
        <div className="max-w-3xl mx-auto px-4 py-6">
            {/* Header */}
            <div className="mb-5">
                <h1 className="text-2xl font-bold mb-1">Matcher</h1>
                <p className="text-sm text-gray-500">
                    Live resultat, kommande matcher och AI-analys
                </p>
            </div>

            {/* Datum-strip — primär dag-navigation */}
            <div className="flex items-center gap-2 mb-5" suppressHydrationWarning>
                <button
                    onClick={() => setSelectedDate(addDays(selectedDate, -1))}
                    className="btn-ghost px-2 py-2"
                    aria-label="Föregående dag"
                >
                    ‹
                </button>
                <div className="flex gap-1 flex-1 overflow-x-auto">
                    {[-1, 0, 1].map((offset) => {
                        const d = addDays(today, offset);
                        const active = sameDay(d, selectedDate);
                        return (
                            <button
                                key={offset}
                                onClick={() => setSelectedDate(d)}
                                className={`flex-1 min-w-[5rem] px-3 py-2 rounded-lg text-sm font-medium transition-all ${active
                                    ? "bg-white/[0.08] text-white shadow-sm"
                                    : "text-gray-400 hover:text-gray-300 hover:bg-white/[0.03]"
                                    }`}
                            >
                                {dayLabel(d, today)}
                            </button>
                        );
                    })}
                </div>
                <button
                    onClick={() => setSelectedDate(addDays(selectedDate, 1))}
                    className="btn-ghost px-2 py-2"
                    aria-label="Nästa dag"
                >
                    ›
                </button>
                <label className="relative">
                    <input
                        type="date"
                        value={toInputValue(selectedDate)}
                        onChange={(e) => {
                            if (e.target.value) setSelectedDate(startOfDay(new Date(e.target.value)));
                        }}
                        className="bg-white/[0.04] border border-white/[0.08] rounded-lg px-2.5 py-2 text-sm text-gray-300 [color-scheme:dark]"
                        aria-label="Välj datum"
                    />
                </label>
            </div>

            {/* Live nu — pinnad överst, oavsett vald dag */}
            {live.length > 0 && (
                <div className="mb-3 rounded-xl border border-red-500/20 bg-red-500/[0.04] overflow-hidden">
                    <div className="flex items-center gap-2 px-4 py-3 border-b border-red-500/10">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                        <span className="font-semibold text-sm text-red-300">Live nu</span>
                        <span className="ml-auto text-xs text-red-400/70">{live.length}</span>
                    </div>
                    <div>{live.map(renderRow)}</div>
                </div>
            )}

            {/* Dagens matcher grupperade per liga */}
            {dayGroups.length === 0 ? (
                live.length === 0 ? (
                    <div className="text-center py-16">
                        <div className="w-14 h-14 rounded-2xl bg-white/[0.03] flex items-center justify-center text-2xl mx-auto mb-3">
                            📅
                        </div>
                        <p className="text-gray-500 text-sm">
                            Inga matcher {isToday ? "idag" : "denna dag"}
                        </p>
                    </div>
                ) : null
            ) : (
                <div className="space-y-3">
                    {dayGroups.map(({ league, fixtures: groupFixtures }) => {
                        const collapsed = collapsedLeagues.has(league.id);
                        return (
                            <div
                                key={league.id}
                                className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden"
                            >
                                <button
                                    onClick={() => toggleLeague(league.id)}
                                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/[0.03] transition-colors"
                                >
                                    {league.logo_url ? (
                                        <img src={league.logo_url} alt="" className="w-5 h-5 object-contain flex-shrink-0" />
                                    ) : (
                                        <div className="w-5 h-5 rounded bg-white/[0.06] flex items-center justify-center flex-shrink-0">
                                            <span className="text-[10px]">🏆</span>
                                        </div>
                                    )}
                                    <div className="flex items-center gap-2 min-w-0">
                                        <span className="font-semibold text-sm text-white truncate">{league.name}</span>
                                        {league.country && (
                                            <span className="text-xs text-gray-500 hidden sm:inline">{league.country}</span>
                                        )}
                                    </div>
                                    <span className="ml-auto text-xs text-gray-500">{groupFixtures.length}</span>
                                    <svg
                                        className={`w-4 h-4 text-gray-500 transition-transform ${collapsed ? "" : "rotate-180"}`}
                                        fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                                    >
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                                    </svg>
                                </button>
                                {!collapsed && (
                                    <div className="border-t border-white/[0.04]">{groupFixtures.map(renderRow)}</div>
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

    // ScoreLock-intelligens inline: modellens favorit + konfidens, value-edge.
    const pick = prediction
        ? prediction.home_win_prob >= prediction.draw_prob &&
          prediction.home_win_prob >= prediction.away_win_prob
            ? { label: "1", prob: prediction.home_win_prob }
            : prediction.away_win_prob >= prediction.draw_prob
                ? { label: "2", prob: prediction.away_win_prob }
                : { label: "X", prob: prediction.draw_prob }
        : null;

    return (
        <a
            href={`/matches/${fixture.id}`}
            className="flex items-center px-4 py-2.5 hover:bg-white/[0.03] transition-colors border-b border-white/[0.03] last:border-b-0 group"
        >
            {/* Time / Status column */}
            <div className="w-14 flex-shrink-0 text-center mr-3">
                {isLive ? (
                    <span className="text-xs font-bold text-red-400">
                        {minute ? `${minute}'` : status === "halftime" ? "HT" : "LIVE"}
                    </span>
                ) : isFinished ? (
                    <span className="text-xs text-gray-500">FT</span>
                ) : (
                    <span className="text-xs font-medium text-gray-300 font-mono tabular-nums">{timeStr}</span>
                )}
            </div>

            {/* Teams */}
            <div className="flex-1 min-w-0 space-y-1">
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

            {/* ScoreLock-intelligens: AI-tips + konfidens + value-edge */}
            <div className="hidden sm:flex items-center gap-1.5 ml-3 w-24 justify-end flex-shrink-0">
                {pick && (
                    <span className="badge bg-scorelock-500/10 text-scorelock-400 border border-scorelock-500/20 font-mono tabular-nums">
                        {pick.label} {Math.round(pick.prob * 100)}%
                    </span>
                )}
                {valueBet && valueBet.edge_percent > 0 && (
                    <span className="badge bg-accent-amber/10 text-amber-400 border border-amber-500/20 font-mono tabular-nums" title="Value-edge">
                        +{valueBet.edge_percent.toFixed(0)}%
                    </span>
                )}
            </div>

            <svg
                className="w-4 h-4 text-gray-700 group-hover:text-gray-400 transition-colors ml-2 flex-shrink-0 hidden sm:block"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}
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
        if (existing) existing.fixtures.push(f);
        else map.set(f.league.id, { league: f.league, fixtures: [f] });
    }
    return Array.from(map.values()).sort((a, b) => {
        const orderA = LEAGUE_ORDER[a.league.name] ?? 99;
        const orderB = LEAGUE_ORDER[b.league.name] ?? 99;
        return orderA - orderB;
    });
}

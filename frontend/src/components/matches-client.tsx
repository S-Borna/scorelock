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
    "Premier League": 1, "premier_league": 1,
    "La Liga": 2, "la_liga": 2,
    "Serie A": 3, "serie_a": 3,
    "Bundesliga": 4, "bundesliga": 4,
    "Ligue 1": 5, "ligue_1": 5,
    "Champions League": 6, "champions_league": 6,
    "Europa League": 7, "europa_league": 7,
    "Conference League": 8, "conference_league": 8,
    "Allsvenskan": 9, "allsvenskan": 9,
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

type ViewMode = "day" | "league";

/**
 * Matchsida — två axlar (som fans tänker): DAG (datum-strip + liga-grupper, live
 * pinnat) och LIGA (vald liga → matcher per omgång + tabell-länk).
 */
export function MatchesClient({ initialFixtures, predictions, valueBets }: MatchesClientProps) {
    const [fixtures, setFixtures] = useState(initialFixtures);
    const { getLiveState } = useLiveScores(initialFixtures);
    const [today] = useState(() => startOfDay(new Date()));
    // Default: hoppa till första dagen med fixtures om "idag" är tomt. Pre-VM
    // hade default "idag" 7 jun (0 fixtures) → tom EmptyState dolde alla
    // kommande VM-matcher från användaren.
    const [selectedDate, setSelectedDate] = useState<Date>(() => {
        const startToday = startOfDay(new Date());
        const future = initialFixtures
            .map((f) => startOfDay(new Date(f.kickoff)).getTime())
            .filter((t) => t >= startToday.getTime())
            .sort((a, b) => a - b);
        const todayHas = initialFixtures.some((f) =>
            sameDay(new Date(f.kickoff), startToday),
        );
        return todayHas || future.length === 0
            ? startToday
            : new Date(future[0]);
    });
    const [mode, setMode] = useState<ViewMode>("day");
    const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

    useEffect(() => {
        const interval = setInterval(async () => {
            try {
                const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
                const resp = await fetch(`${apiBase}/api/v1/fixtures`, { signal: AbortSignal.timeout(5000) });
                if (resp.ok) setFixtures(await resp.json());
            } catch { /* ignore */ }
        }, 60000);
        return () => clearInterval(interval);
    }, []);

    const predMap = new Map(predictions.map((p) => [p.fixture_id, p]));
    const vbMap = new Map(valueBets.map((vb) => [vb.fixture.id, vb]));

    const live = fixtures.filter((f) => f.status === "live" || f.status === "halftime");
    const liveIds = new Set(live.map((f) => f.id));

    // Ligor som finns i datan (ordnade) — för liga-väljaren.
    const leagues: League[] = Array.from(
        new Map(fixtures.map((f) => [f.league.id, f.league])).values(),
    ).sort((a, b) => (LEAGUE_ORDER[a.name] ?? 99) - (LEAGUE_ORDER[b.name] ?? 99));
    const [leagueId, setLeagueId] = useState<number | null>(null);
    const activeLeagueId = leagueId ?? leagues[0]?.id ?? null;

    const toggle = (key: string) =>
        setCollapsed((prev) => {
            const next = new Set(prev);
            next.has(key) ? next.delete(key) : next.add(key);
            return next;
        });

    const renderRow = (f: Fixture) => (
        <MatchRow key={f.id} fixture={f} prediction={predMap.get(f.id)} valueBet={vbMap.get(f.id)} liveState={getLiveState(f)} />
    );

    // ── DAG-vy ──
    const dayFixtures = fixtures
        .filter((f) => !liveIds.has(f.id) && sameDay(new Date(f.kickoff), selectedDate))
        .sort((a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime());
    const dayGroups = groupBy(dayFixtures, (f) => f.league.id, (f) => f.league.name, LEAGUE_ORDER);

    // ── LIGA-vy ──
    const leagueFixtures = fixtures
        .filter((f) => f.league.id === activeLeagueId)
        .sort((a, b) => new Date(b.kickoff).getTime() - new Date(a.kickoff).getTime());
    const roundGroups = groupRounds(leagueFixtures);

    return (
        <div className="max-w-3xl mx-auto px-4 py-6">
            <div className="mb-5 flex items-end justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-bold mb-1">Matcher</h1>
                    <p className="text-sm text-gray-500">Live resultat, kommande matcher och AI-analys</p>
                </div>
                {/* Vy-toggle: Dag ↔ Liga */}
                <div className="flex gap-1 bg-white/[0.03] p-1 rounded-xl border border-white/[0.06] flex-shrink-0">
                    {(["day", "league"] as const).map((m) => (
                        <button
                            key={m}
                            onClick={() => setMode(m)}
                            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${mode === m ? "bg-white/[0.08] text-white shadow-sm" : "text-gray-400 hover:text-gray-300"}`}
                        >
                            {m === "day" ? "📅 Dag" : "🏆 Liga"}
                        </button>
                    ))}
                </div>
            </div>

            {mode === "day" ? (
                <>
                    {/* Datum-strip */}
                    <div className="flex items-center gap-2 mb-5" suppressHydrationWarning>
                        <button onClick={() => setSelectedDate(addDays(selectedDate, -1))} className="btn-ghost px-2 py-2" aria-label="Föregående dag">‹</button>
                        <div className="flex gap-1 flex-1 overflow-x-auto">
                            {[-1, 0, 1, 2, 3, 4, 5, 6, 7].map((offset) => {
                                const d = addDays(today, offset);
                                const active = sameDay(d, selectedDate);
                                return (
                                    <button key={offset} onClick={() => setSelectedDate(d)}
                                        className={`flex-shrink-0 min-w-[5rem] px-3 py-2 rounded-lg text-sm font-medium transition-all ${active ? "bg-white/[0.08] text-white shadow-sm" : "text-gray-400 hover:text-gray-300 hover:bg-white/[0.03]"}`}>
                                        {dayLabel(d, today)}
                                    </button>
                                );
                            })}
                        </div>
                        <button onClick={() => setSelectedDate(addDays(selectedDate, 1))} className="btn-ghost px-2 py-2" aria-label="Nästa dag">›</button>
                        <input type="date" value={toInputValue(selectedDate)}
                            onChange={(e) => { if (e.target.value) setSelectedDate(startOfDay(new Date(e.target.value))); }}
                            className="bg-white/[0.04] border border-white/[0.08] rounded-lg px-2.5 py-2 text-sm text-gray-300 [color-scheme:dark]" aria-label="Välj datum" />
                    </div>

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

                    {dayGroups.length === 0 ? (
                        live.length === 0 ? <EmptyState text={`Inga matcher ${sameDay(selectedDate, today) ? "idag" : "denna dag"}`} /> : null
                    ) : (
                        <div className="space-y-3">
                            {dayGroups.map((g) => (
                                <GroupCard key={g.key} title={g.title} count={g.fixtures.length} logoUrl={g.logoUrl} country={g.country}
                                    collapsed={collapsed.has(g.key)} onToggle={() => toggle(g.key)}>
                                    {g.fixtures.map(renderRow)}
                                </GroupCard>
                            ))}
                        </div>
                    )}
                </>
            ) : (
                <>
                    {/* Liga-väljare + tabell-länk */}
                    <div className="flex items-center gap-2 mb-5">
                        <select value={activeLeagueId ?? ""} onChange={(e) => setLeagueId(Number(e.target.value))}
                            className="flex-1 bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white [color-scheme:dark]">
                            {leagues.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
                        </select>
                        {activeLeagueId && (
                            <a href={`/standings`} className="btn-secondary whitespace-nowrap">🏆 Tabell</a>
                        )}
                    </div>

                    {roundGroups.length === 0 ? (
                        <EmptyState text="Inga matcher i den här ligan" />
                    ) : (
                        <div className="space-y-3">
                            {roundGroups.map((g) => (
                                <GroupCard key={g.key} title={g.title} count={g.fixtures.length}
                                    collapsed={collapsed.has(g.key)} onToggle={() => toggle(g.key)}>
                                    {g.fixtures.map(renderRow)}
                                </GroupCard>
                            ))}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

/* ── Generisk kollaps-grupp ───────────────────────────── */
function GroupCard({
    title, subtitle, count, logoUrl, country, collapsed, onToggle, children,
}: {
    title: string; subtitle?: string; count: number; logoUrl?: string | null; country?: string | null;
    collapsed: boolean; onToggle: () => void; children: React.ReactNode;
}) {
    return (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
            <button onClick={onToggle} className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/[0.03] transition-colors">
                {logoUrl ? (
                    <img src={logoUrl} alt="" className="w-5 h-5 object-contain flex-shrink-0" />
                ) : (
                    <div className="w-5 h-5 rounded bg-white/[0.06] flex items-center justify-center flex-shrink-0"><span className="text-[10px]">🏆</span></div>
                )}
                <div className="flex items-center gap-2 min-w-0">
                    <span className="font-semibold text-sm text-white truncate">{title}</span>
                    {(subtitle || country) && <span className="text-xs text-gray-500 hidden sm:inline">{subtitle || country}</span>}
                </div>
                <span className="ml-auto text-xs text-gray-500">{count}</span>
                <svg className={`w-4 h-4 text-gray-500 transition-transform ${collapsed ? "" : "rotate-180"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
            </button>
            {!collapsed && <div className="border-t border-white/[0.04]">{children}</div>}
        </div>
    );
}

function EmptyState({ text }: { text: string }) {
    return (
        <div className="text-center py-16">
            <div className="w-14 h-14 rounded-2xl bg-white/[0.03] flex items-center justify-center text-2xl mx-auto mb-3">📅</div>
            <p className="text-gray-500 text-sm">{text}</p>
        </div>
    );
}

/* ── Compact match row ─────────────────────────────────── */
function MatchRow({
    fixture, prediction, valueBet, liveState,
}: {
    fixture: Fixture; prediction?: Prediction; valueBet?: ValueBet; liveState?: LiveFixtureState | null;
}) {
    const homeGoals = liveState?.homeGoals ?? fixture.home_goals;
    const awayGoals = liveState?.awayGoals ?? fixture.away_goals;
    const status = liveState?.status ?? fixture.status;
    const minute = liveState?.minute;
    const isLive = status === "live" || status === "halftime";
    const isFinished = status === "finished";
    const homeWin = isFinished && (homeGoals ?? 0) > (awayGoals ?? 0);
    const awayWin = isFinished && (awayGoals ?? 0) > (homeGoals ?? 0);
    const timeStr = new Date(fixture.kickoff).toLocaleTimeString("sv-SE", { hour: "2-digit", minute: "2-digit" });

    const pick = prediction
        ? prediction.home_win_prob >= prediction.draw_prob && prediction.home_win_prob >= prediction.away_win_prob
            ? { label: "1", prob: prediction.home_win_prob }
            : prediction.away_win_prob >= prediction.draw_prob
                ? { label: "2", prob: prediction.away_win_prob }
                : { label: "X", prob: prediction.draw_prob }
        : null;

    return (
        <a href={`/matches/${fixture.id}`} className="flex items-center px-4 py-2.5 hover:bg-white/[0.03] transition-colors border-b border-white/[0.03] last:border-b-0 group">
            <div className="w-14 flex-shrink-0 text-center mr-3">
                {isLive ? (
                    <span className="text-xs font-bold text-red-400">{minute ? `${minute}'` : status === "halftime" ? "HT" : "LIVE"}</span>
                ) : isFinished ? (
                    <span className="text-xs text-gray-500">FT</span>
                ) : (
                    <span className="text-xs font-medium text-gray-300 font-mono tabular-nums">{timeStr}</span>
                )}
            </div>
            <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center gap-2">
                    {fixture.home_team.logo_url ? <img src={fixture.home_team.logo_url} alt="" className="w-4 h-4 object-contain flex-shrink-0" /> : <div className="w-4 h-4 rounded-full bg-white/[0.06] flex-shrink-0" />}
                    <span className={`text-sm truncate ${homeWin ? "font-semibold text-white" : "text-gray-300"}`}>{fixture.home_team.name}</span>
                </div>
                <div className="flex items-center gap-2">
                    {fixture.away_team.logo_url ? <img src={fixture.away_team.logo_url} alt="" className="w-4 h-4 object-contain flex-shrink-0" /> : <div className="w-4 h-4 rounded-full bg-white/[0.06] flex-shrink-0" />}
                    <span className={`text-sm truncate ${awayWin ? "font-semibold text-white" : "text-gray-300"}`}>{fixture.away_team.name}</span>
                </div>
            </div>
            {(isLive || isFinished) && homeGoals !== null && awayGoals !== null ? (
                <div className="w-10 flex-shrink-0 text-right space-y-1">
                    <div className={`text-sm font-mono tabular-nums ${isLive ? "text-red-400 font-bold" : homeWin ? "font-bold text-white" : "text-gray-400"}`}>{homeGoals}</div>
                    <div className={`text-sm font-mono tabular-nums ${isLive ? "text-red-400 font-bold" : awayWin ? "font-bold text-white" : "text-gray-400"}`}>{awayGoals}</div>
                </div>
            ) : (
                <div className="w-10 flex-shrink-0 text-right"><span className="text-xs text-gray-600">—</span></div>
            )}
            <div className="hidden sm:flex items-center gap-1.5 ml-3 w-24 justify-end flex-shrink-0">
                {pick && <span className="badge bg-scorelock-500/10 text-scorelock-400 border border-scorelock-500/20 font-mono tabular-nums">{pick.label} {Math.round(pick.prob * 100)}%</span>}
                {valueBet && valueBet.edge_percent > 0 && <span className="badge bg-accent-amber/10 text-amber-400 border border-amber-500/20 font-mono tabular-nums" title="Value-edge">+{valueBet.edge_percent.toFixed(0)}%</span>}
            </div>
            <svg className="w-4 h-4 text-gray-700 group-hover:text-gray-400 transition-colors ml-2 flex-shrink-0 hidden sm:block" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
        </a>
    );
}

/* ── Helpers ──────────────────────────────────────────── */
interface Group { key: string; title: string; logoUrl?: string | null; country?: string | null; fixtures: Fixture[] }

function groupBy(
    fixtures: Fixture[],
    keyFn: (f: Fixture) => number,
    titleFn: (f: Fixture) => string,
    order: Record<string, number>,
): Group[] {
    const map = new Map<number, Group>();
    for (const f of fixtures) {
        const k = keyFn(f);
        const existing = map.get(k);
        if (existing) existing.fixtures.push(f);
        else map.set(k, { key: String(k), title: titleFn(f), logoUrl: f.league.logo_url, country: f.league.country, fixtures: [f] });
    }
    return Array.from(map.values()).sort((a, b) => (order[a.title] ?? 99) - (order[b.title] ?? 99));
}

// Gruppera en ligas matcher per omgång, senaste omgången först (efter avspark).
function groupRounds(fixtures: Fixture[]): Group[] {
    const map = new Map<string, Group & { latest: number }>();
    for (const f of fixtures) {
        const round = f.round?.trim() || "Övrigt";
        const ko = new Date(f.kickoff).getTime();
        const existing = map.get(round);
        if (existing) {
            existing.fixtures.push(f);
            existing.latest = Math.max(existing.latest, ko);
        } else {
            const title = /^\d+$/.test(round) ? `Omgång ${round}` : round;
            map.set(round, { key: round, title, fixtures: [f], latest: ko });
        }
    }
    return Array.from(map.values()).sort((a, b) => b.latest - a.latest);
}

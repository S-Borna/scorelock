"use client";

import { useLocale } from "@/components/locale-provider";
import type { Article, Fixture, League, Prediction, ValueBet, WeeklyTopTipper } from "@/lib/types";
import Link from "next/link";

interface HomeContentProps {
    articles: Article[];
    fixtures: Fixture[];
    allFixtures: Fixture[];
    predictions: Prediction[];
    valueBets: ValueBet[];
    weeklyTop: WeeklyTopTipper | null;
}

const LEAGUE_ORDER: Record<string, number> = {
    "World Cup": 0, "world_cup": 0,  // VM 2026 — överst under VM-fönstret
    "Premier League": 1, "premier_league": 1,
    "La Liga": 2, "la_liga": 2,
    "Serie A": 3, "serie_a": 3,
    "Bundesliga": 4, "bundesliga": 4,
    "Ligue 1": 5, "ligue_1": 5,
    "Champions League": 6, "champions_league": 6,
    "Allsvenskan": 7, "allsvenskan": 7,
};

// Sverige + VM identifieras via NAMN (stabilt från providern) — aldrig
// lokala auto-increment-id:n som skiljer mellan dev- och prod-DB.
const SWEDEN_NAME = "Sweden";

function isSwedenTeam(t: { name: string }): boolean {
    return t.name === SWEDEN_NAME;
}

function isWorldCupLeague(l: { name: string }): boolean {
    return l.name.toLowerCase().replace(/[_\s]/g, " ").includes("world cup");
}

export function HomeContent({
    articles,
    fixtures,
    allFixtures,
    predictions,
    valueBets,
    weeklyTop,
}: HomeContentProps) {
    const { t } = useLocale();

    const predMap = new Map(predictions.map((p) => [p.fixture_id, p]));
    const vbMap = new Map(valueBets.map((vb) => [vb.fixture.id, vb]));

    // Sverige-VM: nästa Sverige-match som inte är spelad
    const nextSwedenMatch = allFixtures
        .filter(
            (f) =>
                (isSwedenTeam(f.home_team) || isSwedenTeam(f.away_team)) &&
                isWorldCupLeague(f.league) &&
                (f.status === "scheduled" || f.status === "live"),
        )
        .sort((a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime())[0];

    // Live matches
    const liveFixtures = allFixtures.filter((f) => f.status === "live" || f.status === "halftime");

    // Upcoming, sorted by kickoff
    const upcoming = allFixtures
        .filter((f) => f.status === "scheduled")
        .sort((a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime())
        .slice(0, 20);

    // Recent results
    const recentResults = allFixtures
        .filter((f) => f.status === "finished")
        .sort((a, b) => new Date(b.kickoff).getTime() - new Date(a.kickoff).getTime())
        .slice(0, 15);

    // Use live if available, otherwise upcoming, otherwise results
    const displayFixtures = liveFixtures.length > 0 ? liveFixtures :
        upcoming.length > 0 ? upcoming :
            recentResults;

    const sectionTitle = liveFixtures.length > 0 ? "Live" :
        upcoming.length > 0 ? "Kommande matcher" :
            "Senaste resultat";

    // Group by league
    const leagueGroups = groupByLeague(displayFixtures);

    return (
        <div>
            {/* VM-hero — överst ovanför fold när Sverige har kommande VM-match */}
            {nextSwedenMatch && <VMHeroBanner match={nextSwedenMatch} />}

            {/* Compact hero */}
            <section className="border-b border-white/[0.04] bg-gradient-to-b from-white/[0.02] to-transparent">
                <div className="max-w-3xl mx-auto px-4 py-10 sm:py-14 text-center">
                    <div className="inline-flex items-center gap-2 text-xs font-medium text-scorelock-400 bg-scorelock-500/10 border border-scorelock-500/20 rounded-full px-3 py-1 mb-4">
                        <span className="w-1.5 h-1.5 rounded-full bg-scorelock-500 animate-pulse" />
                        {t("hero.badge")}
                    </div>
                    <h1 className="text-3xl sm:text-4xl font-bold mb-3">
                        {t("hero.title.prefix")}{" "}
                        <span className="text-gradient">{t("hero.title.highlight")}</span>
                    </h1>
                    <p className="text-gray-400 text-sm sm:text-base max-w-md mx-auto mb-4">
                        {t("hero.subtitle")}
                    </p>
                    {/* Levande puls — dagens slate + moaten (AI-tips) */}
                    <div className="flex items-center justify-center gap-4 text-xs font-mono text-gray-500 mb-6">
                        {liveFixtures.length > 0 && (
                            <span className="text-red-400 inline-flex items-center gap-1.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                                {liveFixtures.length} live nu
                            </span>
                        )}
                        <span>{upcoming.length} kommande</span>
                        {predictions.length > 0 && (
                            <span className="text-scorelock-400">{predictions.length} AI-tips</span>
                        )}
                    </div>
                    <div className="flex items-center justify-center gap-3">
                        <Link href="/vm" className="btn-primary text-sm">
                            VM 2026 → Kom igen Sverige
                        </Link>
                        <Link href="/matches" className="btn-secondary text-sm">
                            {t("hero.cta.primary")}
                        </Link>
                    </div>
                </div>
            </section>

            <div className="max-w-3xl mx-auto px-4 py-8">
                {/* Match section — grouped by league */}
                <section className="mb-10">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                            {liveFixtures.length > 0 && (
                                <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                            )}
                            <h2 className="text-lg font-bold">{sectionTitle}</h2>
                            {liveFixtures.length > 0 && (
                                <span className="text-xs bg-red-500/20 text-red-400 rounded-md px-1.5 py-0.5">
                                    {liveFixtures.length}
                                </span>
                            )}
                        </div>
                        <Link href="/matches" className="text-sm text-scorelock-400 hover:text-scorelock-300 transition-colors">
                            Alla matcher →
                        </Link>
                    </div>

                    {leagueGroups.length > 0 ? (
                        <div className="space-y-3">
                            {leagueGroups.map(({ league, fixtures: groupFixtures }) => (
                                <div key={league.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
                                    {/* League header */}
                                    <div className="flex items-center gap-3 px-4 py-2.5 bg-white/[0.01]">
                                        {league.logo_url ? (
                                            <img src={league.logo_url} alt="" className="w-4 h-4 object-contain" />
                                        ) : (
                                            <div className="w-4 h-4 rounded bg-white/[0.06] flex items-center justify-center">
                                                <span className="text-[8px]">🏆</span>
                                            </div>
                                        )}
                                        <span className="text-xs font-semibold text-gray-300">{league.name}</span>
                                        {league.country && (
                                            <span className="text-[10px] text-gray-600">{league.country}</span>
                                        )}
                                    </div>

                                    {/* Match rows */}
                                    <div className="border-t border-white/[0.04]">
                                        {groupFixtures.map((f) => (
                                            <CompactMatchRow key={f.id} fixture={f} prediction={predMap.get(f.id)} />
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12 rounded-xl border border-white/[0.06] bg-white/[0.02]">
                            <p className="text-gray-500 text-sm">Inga matcher just nu</p>
                        </div>
                    )}
                </section>

                {/* Value bets callout */}
                {valueBets.length > 0 && (
                    <section className="mb-10">
                        <Link
                            href="/value-bets"
                            className="block p-4 rounded-xl border border-scorelock-500/10 bg-scorelock-500/[0.03] hover:border-scorelock-500/20 transition-all group"
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-9 h-9 rounded-lg bg-scorelock-500/10 flex items-center justify-center">
                                        <svg className="w-4 h-4 text-scorelock-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                    </div>
                                    <div>
                                        <p className="text-sm font-semibold text-white">
                                            {valueBets.length} value bets
                                        </p>
                                        <p className="text-[11px] text-gray-500">AI-modellen hittar värde</p>
                                    </div>
                                </div>
                                <svg className="w-4 h-4 text-gray-600 group-hover:text-scorelock-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                                </svg>
                            </div>
                        </Link>
                    </section>
                )}

                {/* Weekly top tipper */}
                {weeklyTop && (
                    <section className="mb-10">
                        <Link href="/leaderboard" className="block p-4 rounded-xl border border-amber-500/10 bg-amber-500/[0.03] hover:border-amber-500/20 transition-all group">
                            <div className="flex items-center gap-3">
                                <div className="w-9 h-9 rounded-lg bg-amber-500/10 flex items-center justify-center text-lg">
                                    👑
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-[11px] text-amber-400 font-semibold uppercase tracking-wider">{t("section.weeklyTipper")}</p>
                                    <p className="text-sm font-bold truncate">{weeklyTop.user_name || "Anonym"}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-lg font-bold text-scorelock-400">{weeklyTop.points_this_week}p</p>
                                    <p className="text-[10px] text-gray-500">{weeklyTop.tips_this_week} tips</p>
                                </div>
                            </div>
                        </Link>
                    </section>
                )}

                {/* Standings preview — quick links */}
                <section className="mb-10">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-bold">Tabeller</h2>
                        <Link href="/standings" className="text-sm text-scorelock-400 hover:text-scorelock-300 transition-colors">
                            Alla tabeller →
                        </Link>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1", "Allsvenskan"].map((name) => (
                            <Link
                                key={name}
                                href="/standings"
                                className="flex items-center gap-2 p-3 rounded-xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/[0.1] transition-all"
                            >
                                <span className="text-sm font-medium text-gray-300">{name}</span>
                            </Link>
                        ))}
                    </div>
                </section>
            </div>
        </div>
    );
}

/* ── VM-Hero — Sverige-spektakel ovanför fold ───────── */

function VMHeroBanner({ match }: { match: Fixture }) {
    const isSwedenHome = isSwedenTeam(match.home_team);
    const opponent = isSwedenHome ? match.away_team : match.home_team;
    const kickoff = new Date(match.kickoff);

    // Pre-calculated days/hours till kickoff för stabilitet vid SSR
    const now = new Date();
    const msToKickoff = kickoff.getTime() - now.getTime();
    const daysToKickoff = Math.max(0, Math.floor(msToKickoff / (1000 * 60 * 60 * 24)));
    const hoursToKickoff = Math.max(
        0,
        Math.floor((msToKickoff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
    );

    return (
        <Link
            href={`/matches/${match.id}`}
            className="block relative overflow-hidden border-b border-yellow-500/15 group"
        >
            {/* Sverige-flagg-bakgrund: blå-bas + gult kors */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-blue-950 to-blue-900" />
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(252,211,77,0.18),transparent_55%)]" />
            <div className="absolute top-0 bottom-0 left-1/3 w-px bg-yellow-300/30" />

            <div className="relative max-w-5xl mx-auto px-4 py-8 sm:py-10">
                <div className="flex items-center justify-between gap-4 flex-wrap">
                    <div className="flex items-center gap-4">
                        <div className="text-5xl sm:text-6xl">🇸🇪</div>
                        <div>
                            <div className="text-[10px] sm:text-xs font-bold uppercase tracking-[0.3em] text-yellow-300 mb-1">
                                VM 2026{match.group_letter ? ` · GRUPP ${match.group_letter}` : ""} · NÄSTA MATCH
                            </div>
                            <div className="font-serif text-2xl sm:text-3xl text-white leading-tight">
                                Sverige vs {opponent.name}
                            </div>
                            <div className="text-sm text-blue-100/80 mt-1">
                                {kickoff.toLocaleDateString("sv-SE", {
                                    weekday: "long",
                                    day: "numeric",
                                    month: "long",
                                })}{" "}
                                kl.{" "}
                                {kickoff.toLocaleTimeString("sv-SE", {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                })}
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="text-right">
                            <div className="text-[10px] uppercase tracking-widest text-yellow-200/70 mb-1">
                                Spark om
                            </div>
                            <div className="font-mono text-xl sm:text-2xl text-yellow-300 font-bold tabular-nums">
                                {daysToKickoff > 0
                                    ? `${daysToKickoff}d ${hoursToKickoff}h`
                                    : `${hoursToKickoff}h`}
                            </div>
                        </div>
                        <div className="text-yellow-300/50 group-hover:text-yellow-300 group-hover:translate-x-1 transition-transform text-2xl">
                            →
                        </div>
                    </div>
                </div>
            </div>
        </Link>
    );
}

/* ── Compact match row for homepage ───────────────────── */

function CompactMatchRow({ fixture, prediction }: { fixture: Fixture; prediction?: Prediction }) {
    const isLive = fixture.status === "live" || fixture.status === "halftime";
    const isFinished = fixture.status === "finished";
    const homeWin = isFinished && (fixture.home_goals ?? 0) > (fixture.away_goals ?? 0);
    const awayWin = isFinished && (fixture.away_goals ?? 0) > (fixture.home_goals ?? 0);

    const kickoff = new Date(fixture.kickoff);
    const timeStr = kickoff.toLocaleTimeString("sv-SE", { hour: "2-digit", minute: "2-digit" });

    // Moaten på front-dörren: modellens favorit + konfidens.
    const pick = prediction
        ? prediction.home_win_prob >= prediction.draw_prob && prediction.home_win_prob >= prediction.away_win_prob
            ? { label: "1", prob: prediction.home_win_prob }
            : prediction.away_win_prob >= prediction.draw_prob
                ? { label: "2", prob: prediction.away_win_prob }
                : { label: "X", prob: prediction.draw_prob }
        : null;

    return (
        <a
            href={`/matches/${fixture.id}`}
            className="flex items-center px-4 py-2 hover:bg-white/[0.03] transition-colors border-b border-white/[0.03] last:border-b-0 group"
        >
            {/* Time */}
            <div className="w-12 flex-shrink-0 text-center mr-3">
                {isLive ? (
                    <span className="text-xs font-bold text-red-400">LIVE</span>
                ) : isFinished ? (
                    <span className="text-xs text-gray-500">FT</span>
                ) : (
                    <span className="text-xs text-gray-400">{timeStr}</span>
                )}
            </div>

            {/* Teams */}
            <div className="flex-1 min-w-0 space-y-0.5">
                <div className="flex items-center gap-2">
                    {fixture.home_team.logo_url ? (
                        <img src={fixture.home_team.logo_url} alt="" className="w-3.5 h-3.5 object-contain flex-shrink-0" />
                    ) : (
                        <div className="w-3.5 h-3.5 rounded-full bg-white/[0.06] flex-shrink-0" />
                    )}
                    <span className={`text-xs truncate ${homeWin ? "font-semibold text-white" : "text-gray-300"}`}>
                        {fixture.home_team.name}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    {fixture.away_team.logo_url ? (
                        <img src={fixture.away_team.logo_url} alt="" className="w-3.5 h-3.5 object-contain flex-shrink-0" />
                    ) : (
                        <div className="w-3.5 h-3.5 rounded-full bg-white/[0.06] flex-shrink-0" />
                    )}
                    <span className={`text-xs truncate ${awayWin ? "font-semibold text-white" : "text-gray-300"}`}>
                        {fixture.away_team.name}
                    </span>
                </div>
            </div>

            {/* Score */}
            {(isLive || isFinished) && fixture.home_goals !== null && fixture.away_goals !== null ? (
                <div className="w-8 flex-shrink-0 text-right space-y-0.5">
                    <div className={`text-xs font-mono ${isLive ? "text-red-400 font-bold" : homeWin ? "font-bold text-white" : "text-gray-400"}`}>
                        {fixture.home_goals}
                    </div>
                    <div className={`text-xs font-mono ${isLive ? "text-red-400 font-bold" : awayWin ? "font-bold text-white" : "text-gray-400"}`}>
                        {fixture.away_goals}
                    </div>
                </div>
            ) : (
                <div className="w-8 flex-shrink-0 text-right">
                    <span className="text-[10px] text-gray-600">—</span>
                </div>
            )}

            {/* AI-tips — moaten, även på startsidan */}
            {pick && (
                <span className="hidden sm:inline-flex badge bg-scorelock-500/10 text-scorelock-400 border border-scorelock-500/20 font-mono tabular-nums ml-2 flex-shrink-0">
                    {pick.label} {Math.round(pick.prob * 100)}%
                </span>
            )}
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

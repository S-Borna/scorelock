"use client";

import { LiveBoard } from "@/components/live-board";
import { Reveal } from "@/components/reveal";
import { VMCountdown } from "@/components/vm-countdown";
import type {
    Article,
    Fixture,
    League,
    MatchIntelligenceBundle,
    Prediction,
    ValueBet,
    WeeklyTopTipper,
} from "@/lib/types";
import Link from "next/link";

import { fmtDayCompact, fmtDateShort, fmtTime, parseUTC } from "@/lib/time";

interface HomeContentProps {
    articles: Article[];
    fixtures: Fixture[];
    allFixtures: Fixture[];
    predictions: Prediction[];
    valueBets: ValueBet[];
    weeklyTop: WeeklyTopTipper | null;
    swedenMatch: Fixture | null;
    swedenIntelligence: MatchIntelligenceBundle | null;
}

const LEAGUE_ORDER: Record<string, number> = {
    "World Cup": 0, "world_cup": 0,
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
    allFixtures,
    predictions,
    valueBets,
    swedenMatch,
    swedenIntelligence,
}: HomeContentProps) {
    const predMap = new Map(predictions.map((p) => [p.fixture_id, p]));

    const liveFixtures = allFixtures.filter(
        (f) => f.status === "live" || f.status === "halftime",
    );
    const upcoming = allFixtures
        .filter((f) => f.status === "scheduled")
        .sort((a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime());

    // "Härnäst på VM": de närmaste VM-matcherna (eller alla ligor om VM saknas)
    const vmUpcoming = upcoming.filter((f) => isWorldCupLeague(f.league));
    const nextBand = (vmUpcoming.length > 0 ? vmUpcoming : upcoming).slice(0, 8);

    // Sveriges tre gruppspels-matcher för tidslinjen
    const swedenFixtures = allFixtures
        .filter(
            (f) =>
                (isSwedenTeam(f.home_team) || isSwedenTeam(f.away_team)) &&
                isWorldCupLeague(f.league),
        )
        .sort((a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime());

    const displayFixtures =
        liveFixtures.length > 0 ? liveFixtures : upcoming.slice(0, 20);
    const sectionTitle = liveFixtures.length > 0 ? "Live just nu" : "Programmet";
    const leagueGroups = groupByLeague(displayFixtures);

    const aiText = swedenIntelligence?.pre_match ?? null;

    return (
        <div>
            {/* ════════ AKT 1 · SÄNDNINGSSTART ════════ */}
            <section className="relative overflow-hidden grain min-h-[92svh] flex flex-col justify-center border-b border-white/[0.06]">
                {/* Natthimmel */}
                <div className="absolute inset-0 bg-gradient-to-b from-[#050810] via-blue-950 to-surface-950 pointer-events-none" />
                {/* Stadionljuset som stiger bakom horisonten */}
                <div className="horizon-glow absolute -bottom-40 left-1/2 -translate-x-1/2 w-[140%] h-[420px] bg-[radial-gradient(ellipse_at_center,rgba(252,211,77,0.20),rgba(252,211,77,0.05)_45%,transparent_70%)] pointer-events-none" />
                <div className="horizon-band absolute -bottom-24 left-1/2 -translate-x-1/2 w-[120%] h-[280px] bg-[radial-gradient(ellipse_at_center,rgba(37,99,235,0.28),transparent_65%)] pointer-events-none" />
                {/* Gult kors-band — flaggan som ljusstråk */}
                <div className="absolute top-0 bottom-0 left-[18%] w-px bg-gradient-to-b from-transparent via-yellow-300/25 to-transparent pointer-events-none" />

                <div className="container-main relative py-20 stagger">
                    <p className="text-[11px] sm:text-xs font-bold uppercase tracking-[0.4em] text-yellow-300/90 mb-6">
                        ScoreLock direkt · VM 2026 · USA Kanada Mexico
                    </p>

                    <h1 className="font-serif tracking-tight leading-[0.92] mb-7">
                        <span className="block text-5xl sm:text-7xl md:text-8xl text-white">
                            Hela VM.
                        </span>
                        <span className="block text-5xl sm:text-7xl md:text-8xl text-white">
                            Varje minut.
                        </span>
                        <span className="block text-5xl sm:text-7xl md:text-8xl text-yellow-300 [text-shadow:0_0_32px_rgba(253,224,71,0.3),0_0_90px_rgba(253,224,71,0.12)]">
                            Förklarat.
                        </span>
                    </h1>

                    <p className="text-base sm:text-lg text-blue-100/85 max-w-xl mb-10 leading-relaxed">
                        Livescore-sajterna visar siffrorna. ScoreLock förklarar dem —
                        AI-analys före, under och efter varje match. På svenska.
                    </p>

                    {/* Sverige-modulen: nedräkningen är kvällens hjärtslag */}
                    {swedenMatch && <HeroSwedenModule match={swedenMatch} />}

                    {/* Puls + CTA */}
                    <div className="flex flex-wrap items-center gap-x-6 gap-y-3 mt-10">
                        <Link href="/vm" className="btn-primary">
                            Följ VM hos oss →
                        </Link>
                        <Link href="/landslag/sverige" className="btn-secondary">
                            🇸🇪 Sveriges resa
                        </Link>
                        <div className="flex items-center gap-4 text-xs font-mono text-blue-200/60 tabular-nums">
                            {liveFixtures.length > 0 && (
                                <span className="text-red-400 inline-flex items-center gap-1.5">
                                    <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                                    {liveFixtures.length} live
                                </span>
                            )}
                            <span>{upcoming.length} matcher väntar</span>
                            {predictions.length > 0 && (
                                <span className="text-yellow-300/80">
                                    {predictions.length} AI-analyser redo
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            </section>

            {/* ════════ AKT 1.5 · LIVESCORE-BOARDEN (kärnan) ════════ */}
            <LiveBoard initialFixtures={allFixtures} />

            {/* ════════ AKT 2 · HÄRNÄST PÅ VM ════════ */}
            {nextBand.length > 0 && (
                <section className="border-b border-white/[0.04] py-12 overflow-hidden">
                    <div className="container-main mb-6 flex items-baseline justify-between">
                        <Reveal>
                            <h2 className="font-serif text-2xl sm:text-3xl tracking-tight">
                                Härnäst på VM
                            </h2>
                        </Reveal>
                        <Link
                            href="/matches"
                            className="text-sm text-scorelock-400 hover:text-scorelock-300 transition-colors"
                        >
                            Hela spelschemat →
                        </Link>
                    </div>
                    <Reveal>
                        <div className="flex gap-3 overflow-x-auto pb-4 px-4 sm:px-6 lg:px-8 snap-x [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                            {nextBand.map((f) => (
                                <BandCard
                                    key={f.id}
                                    fixture={f}
                                    prediction={predMap.get(f.id)}
                                />
                            ))}
                        </div>
                    </Reveal>
                </section>
            )}

            {/* ════════ AKT 3 · AI-BEVISET ════════ */}
            {aiText && swedenMatch && (
                <section className="relative border-b border-white/[0.04] py-20 overflow-hidden">
                    <div className="absolute top-0 right-0 w-[50%] h-full bg-[radial-gradient(ellipse_at_top_right,rgba(252,211,77,0.05),transparent_60%)] pointer-events-none" />
                    <div className="container-main relative">
                        <Reveal>
                            <p className="text-[11px] font-bold uppercase tracking-[0.35em] text-yellow-300/80 mb-3">
                                Det här är skillnaden
                            </p>
                            <h2 className="font-serif text-3xl sm:text-4xl tracking-tight mb-10 max-w-2xl">
                                Vår AI har redan läst in sig på{" "}
                                <span className="text-yellow-300">
                                    Sverige–
                                    {opponentOf(swedenMatch).name === "Tunisia"
                                        ? "Tunisien"
                                        : opponentOf(swedenMatch).name}
                                </span>
                            </h2>
                        </Reveal>

                        <Reveal delay={80}>
                            <blockquote className="relative max-w-3xl">
                                <div className="absolute -left-3 sm:-left-6 top-0 bottom-0 w-px bg-gradient-to-b from-yellow-300/60 via-yellow-300/20 to-transparent" />
                                <p className="font-serif text-xl sm:text-2xl md:text-[1.7rem] leading-snug text-gray-100 mb-6 pl-4 sm:pl-8">
                                    ”{aiText.summary}”
                                </p>
                                <p className="text-sm sm:text-base text-gray-400 leading-relaxed max-w-2xl pl-4 sm:pl-8 mb-6">
                                    {firstParagraph(aiText.body)}
                                </p>
                                <div className="flex flex-wrap items-center gap-4 pl-4 sm:pl-8">
                                    <Link
                                        href={`/matches/${swedenMatch.id}`}
                                        className="btn-secondary text-sm"
                                    >
                                        Läs hela analysen →
                                    </Link>
                                    <span className="text-[10px] font-mono uppercase tracking-widest text-gray-600">
                                        ScoreLock AI · grundad i odds + form
                                    </span>
                                </div>
                            </blockquote>
                        </Reveal>
                    </div>
                </section>
            )}

            {/* ════════ AKT 4 · SVERIGES VÄG ════════ */}
            {swedenFixtures.length > 0 && (
                <section className="border-b border-white/[0.04] py-20">
                    <div className="container-main">
                        <Reveal>
                            <p className="text-[11px] font-bold uppercase tracking-[0.35em] text-yellow-300/80 mb-3">
                                Grupp F
                            </p>
                            <h2 className="font-serif text-3xl sm:text-4xl tracking-tight mb-12">
                                Sveriges väg genom gruppspelet
                            </h2>
                        </Reveal>
                        <div className="relative">
                            {/* Tidslinjens ryggrad */}
                            <div className="absolute left-0 right-0 top-[34px] hidden md:block h-px bg-gradient-to-r from-yellow-300/40 via-white/10 to-white/5" />
                            <div className="grid md:grid-cols-3 gap-8 md:gap-6">
                                {swedenFixtures.map((f, i) => (
                                    <Reveal key={f.id} delay={i * 90}>
                                        <TimelineMatch fixture={f} index={i} />
                                    </Reveal>
                                ))}
                            </div>
                        </div>
                    </div>
                </section>
            )}

            {/* ════════ AKT 5 · VAD DU FÅR ════════ */}
            <section className="border-b border-white/[0.04] py-20">
                <div className="container-main">
                    <Reveal>
                        <h2 className="font-serif text-3xl sm:text-4xl tracking-tight mb-12 max-w-xl">
                            Byggt för dig som vill{" "}
                            <span className="text-scorelock-400">förstå</span> matchen
                        </h2>
                    </Reveal>
                    <div className="grid sm:grid-cols-3 gap-4">
                        <Reveal>
                            <FeatureCard
                                glyph="✦"
                                title="AI som läst på"
                                body="Grundad analys före, under och efter varje match — citerar odds, form och vår modell. Aldrig magkänsla."
                                href="/vm"
                                accent="yellow"
                            />
                        </Reveal>
                        <Reveal delay={80}>
                            <FeatureCard
                                glyph="◈"
                                title="Value-radar"
                                body={`Modellen mot marknaden — just nu ${valueBets.length > 0 ? `${valueBets.length} lägen` : "skannar vi oddsen"} där bookmakers kan ha fel.`}
                                href="/value-bets"
                                accent="green"
                            />
                        </Reveal>
                        <Reveal delay={160}>
                            <FeatureCard
                                glyph="●"
                                title="Livepuls"
                                body="Mål, momentum och AI-uppdateringar i realtid. Matchen förklarad medan den spelas."
                                href="/matches"
                                accent="red"
                            />
                        </Reveal>
                    </div>
                </div>
            </section>

            {/* ════════ AKT 6 · PROGRAMMET ════════ */}
            <section className="py-16">
                <div className="max-w-3xl mx-auto px-4">
                    <div className="flex items-center justify-between mb-6">
                        <Reveal>
                            <div className="flex items-center gap-2">
                                {liveFixtures.length > 0 && (
                                    <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                                )}
                                <h2 className="font-serif text-2xl tracking-tight">
                                    {sectionTitle}
                                </h2>
                            </div>
                        </Reveal>
                        <Link
                            href="/matches"
                            className="text-sm text-scorelock-400 hover:text-scorelock-300 transition-colors"
                        >
                            Alla matcher →
                        </Link>
                    </div>

                    {leagueGroups.length > 0 ? (
                        <div className="space-y-3">
                            {leagueGroups.map(({ league, fixtures: groupFixtures }, gi) => (
                                <Reveal key={league.id} delay={Math.min(gi * 60, 240)}>
                                    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden transition-all duration-200 hover:border-white/[0.1]">
                                        <div className="flex items-center gap-3 px-4 py-2.5 bg-white/[0.01]">
                                            {league.logo_url ? (
                                                // eslint-disable-next-line @next/next/no-img-element
                                                <img src={league.logo_url} alt="" className="w-4 h-4 object-contain" />
                                            ) : (
                                                <span className="w-4 h-4 rounded bg-white/[0.06] inline-flex items-center justify-center text-[8px]">⚽</span>
                                            )}
                                            <span className="text-xs font-semibold text-gray-300">
                                                {displayLeague(league.name)}
                                            </span>
                                        </div>
                                        <div className="border-t border-white/[0.04]">
                                            {groupFixtures.map((f) => (
                                                <CompactMatchRow
                                                    key={f.id}
                                                    fixture={f}
                                                    prediction={predMap.get(f.id)}
                                                />
                                            ))}
                                        </div>
                                    </div>
                                </Reveal>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-12 rounded-xl border border-white/[0.06] bg-white/[0.02]">
                            <p className="text-gray-500 text-sm">Inga matcher just nu</p>
                        </div>
                    )}
                </div>
            </section>

            {/* ════════ FINAL · AVSPARK ════════ */}
            <section className="relative overflow-hidden border-t border-white/[0.06] py-24 grain">
                <div className="absolute inset-0 bg-gradient-to-t from-blue-950/60 to-transparent pointer-events-none" />
                <div className="horizon-glow absolute -bottom-32 left-1/2 -translate-x-1/2 w-[120%] h-[300px] bg-[radial-gradient(ellipse_at_center,rgba(252,211,77,0.14),transparent_65%)] pointer-events-none" />
                <div className="container-main relative text-center">
                    <Reveal>
                        <p className="font-serif text-4xl sm:text-6xl tracking-tight mb-3">
                            <span className="text-white">Avspark.</span>
                        </p>
                        <p className="text-blue-100/70 mb-10 max-w-md mx-auto">
                            Mexico–Sydafrika öppnar turneringen. Sverige kliver in den 15:e.
                            Vi är med hela vägen till finalen 19 juli.
                        </p>
                        <div className="flex items-center justify-center gap-3">
                            <Link href="/vm" className="btn-primary">
                                Till VM-centret →
                            </Link>
                            <Link href="/signup" className="btn-secondary">
                                Skapa konto
                            </Link>
                        </div>
                    </Reveal>
                </div>
            </section>
        </div>
    );
}

/* ── Hero: Sverige-modulen ─────────────────────────────── */

function HeroSwedenModule({ match }: { match: Fixture }) {
    const opponent = opponentOf(match);
    return (
        <div className="inline-block rounded-2xl border border-yellow-300/20 bg-blue-950/40 backdrop-blur-sm px-5 sm:px-7 py-5">
            <div className="flex items-center gap-3 mb-4">
                <span className="text-2xl">🇸🇪</span>
                <div>
                    <p className="text-[10px] uppercase tracking-[0.3em] text-yellow-200/70 font-bold">
                        Sverige spelar om
                    </p>
                    <p className="text-sm text-blue-100/80">
                        vs {opponent.name === "Tunisia" ? "Tunisien" : opponent.name} ·{" "}
                        <span className="font-mono tabular-nums" suppressHydrationWarning>
                            {fmtDateShort(match.kickoff)} {fmtTime(match.kickoff)}
                        </span>
                    </p>
                </div>
            </div>
            <Link href={`/matches/${match.id}`} className="block group">
                <VMCountdown kickoff={match.kickoff} />
                <span className="inline-block mt-3 text-xs text-yellow-300/80 group-hover:text-yellow-200 transition-colors">
                    Matchcentret med AI-analys →
                </span>
            </Link>
        </div>
    );
}

/* ── Härnäst-bandet ────────────────────────────────────── */

function BandCard({ fixture, prediction }: { fixture: Fixture; prediction?: Prediction }) {
    const pick = pickOf(prediction);
    const sweden = isSwedenTeam(fixture.home_team) || isSwedenTeam(fixture.away_team);
    return (
        <Link
            href={`/matches/${fixture.id}`}
            className={
                "snap-start flex-shrink-0 w-[230px] rounded-2xl border p-4 transition-all duration-300 hover:-translate-y-1 " +
                (sweden
                    ? "border-yellow-400/40 bg-gradient-to-br from-yellow-500/[0.08] to-blue-950/30 shadow-[0_0_24px_rgba(253,224,71,0.06)]"
                    : "border-white/[0.07] bg-white/[0.02] hover:border-white/[0.14]")
            }
        >
            <p className="text-[10px] font-mono uppercase tracking-wider text-gray-500 mb-3 tabular-nums" suppressHydrationWarning>
                {fmtDayCompact(fixture.kickoff)} {fmtTime(fixture.kickoff)}
                {fixture.group_letter ? ` · Grupp ${fixture.group_letter}` : ""}
            </p>
            <BandTeam team={fixture.home_team} />
            <BandTeam team={fixture.away_team} />
            <div className="mt-3 pt-3 border-t border-white/[0.05] flex items-center justify-between">
                <span className="text-[10px] text-gray-600 uppercase tracking-wider">
                    {sweden ? "🇸🇪 Sverige-match" : "AI-analys klar"}
                </span>
                {pick && (
                    <span className="text-[10px] font-mono text-scorelock-400 tabular-nums">
                        {pick.label} {Math.round(pick.prob * 100)}%
                    </span>
                )}
            </div>
        </Link>
    );
}

function BandTeam({ team }: { team: { name: string; logo_url: string | null } }) {
    return (
        <div className="flex items-center gap-2.5 py-1">
            {team.logo_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={team.logo_url} alt="" className="w-6 h-6 rounded-sm object-cover" />
            ) : (
                <span className="w-6 h-6 rounded-sm bg-white/[0.06]" />
            )}
            <span
                className={
                    "text-sm truncate " +
                    (isSwedenTeam(team) ? "text-yellow-200 font-semibold" : "text-gray-200")
                }
            >
                {team.name}
            </span>
        </div>
    );
}

/* ── Sverige-tidslinjen ────────────────────────────────── */

function TimelineMatch({ fixture, index }: { fixture: Fixture; index: number }) {
    const opponent = opponentOf(fixture);
    const home = isSwedenTeam(fixture.home_team);
    return (
        <Link href={`/matches/${fixture.id}`} className="block group">
            {/* Nod på ryggraden */}
            <div className="hidden md:flex items-center gap-3 mb-5">
                <span className="w-[17px] h-[17px] rounded-full border-2 border-yellow-300/70 bg-surface-950 group-hover:bg-yellow-300/20 transition-colors" />
                <span className="font-mono text-xs text-yellow-300/70 tabular-nums uppercase tracking-wider" suppressHydrationWarning>
                    {fmtDateShort(fixture.kickoff)}
                </span>
            </div>
            <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-5 transition-all duration-300 group-hover:border-yellow-400/40 group-hover:-translate-y-1">
                <p className="text-[10px] uppercase tracking-[0.25em] text-gray-500 font-bold mb-3">
                    Match {index + 1} · {home ? "”Hemma”" : "”Borta”"}
                </p>
                <div className="flex items-center gap-3 mb-2">
                    {opponent.logo_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={opponent.logo_url} alt="" className="w-10 h-10 rounded-lg object-cover" />
                    ) : (
                        <span className="w-10 h-10 rounded-lg bg-white/[0.06]" />
                    )}
                    <div>
                        <p className="font-serif text-xl text-white leading-tight">
                            {opponent.name === "Tunisia" ? "Tunisien" : opponent.name}
                        </p>
                        <p className="text-xs text-gray-500 font-mono tabular-nums md:hidden" suppressHydrationWarning>
                            {fmtDateShort(fixture.kickoff)}
                        </p>
                    </div>
                </div>
                <p className="text-xs text-yellow-200/60 group-hover:text-yellow-200 transition-colors mt-3">
                    AI-analys + odds →
                </p>
            </div>
        </Link>
    );
}

/* ── Funktionskort ─────────────────────────────────────── */

function FeatureCard({
    glyph,
    title,
    body,
    href,
    accent,
}: {
    glyph: string;
    title: string;
    body: string;
    href: string;
    accent: "yellow" | "green" | "red";
}) {
    const accentCls =
        accent === "yellow"
            ? "text-yellow-300 group-hover:[text-shadow:0_0_18px_rgba(253,224,71,0.5)]"
            : accent === "green"
              ? "text-scorelock-400 group-hover:[text-shadow:0_0_18px_rgba(9,206,95,0.5)]"
              : "text-red-400 group-hover:[text-shadow:0_0_18px_rgba(248,113,113,0.5)]";
    return (
        <Link
            href={href}
            className="group block h-full rounded-2xl border border-white/[0.07] bg-white/[0.02] p-6 transition-all duration-300 hover:border-white/[0.14] hover:-translate-y-1"
        >
            <span className={`block text-2xl mb-4 transition-all duration-300 ${accentCls}`}>
                {glyph}
            </span>
            <h3 className="font-serif text-xl mb-2">{title}</h3>
            <p className="text-sm text-gray-400 leading-relaxed">{body}</p>
        </Link>
    );
}

/* ── Programmet: kompakt matchrad (behållen) ───────────── */

function CompactMatchRow({ fixture, prediction }: { fixture: Fixture; prediction?: Prediction }) {
    const isLive = fixture.status === "live" || fixture.status === "halftime";
    const isFinished = fixture.status === "finished";
    const homeWin = isFinished && (fixture.home_goals ?? 0) > (fixture.away_goals ?? 0);
    const awayWin = isFinished && (fixture.away_goals ?? 0) > (fixture.home_goals ?? 0);
    const timeStr = fmtTime(fixture.kickoff);
    const pick = pickOf(prediction);

    return (
        <a
            href={`/matches/${fixture.id}`}
            className="flex items-center px-4 py-2 hover:bg-white/[0.03] transition-colors border-b border-white/[0.03] last:border-b-0"
        >
            <div className="w-12 flex-shrink-0 text-center mr-3">
                {isLive ? (
                    <span className="text-xs font-bold text-red-400">LIVE</span>
                ) : isFinished ? (
                    <span className="text-xs text-gray-500">FT</span>
                ) : (
                    <span className="text-xs text-gray-400 font-mono tabular-nums" suppressHydrationWarning>{timeStr}</span>
                )}
            </div>
            <div className="flex-1 min-w-0 space-y-0.5">
                {[fixture.home_team, fixture.away_team].map((t, i) => (
                    <div key={i} className="flex items-center gap-2">
                        {t.logo_url ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={t.logo_url} alt="" className="w-3.5 h-3.5 object-contain flex-shrink-0" />
                        ) : (
                            <span className="w-3.5 h-3.5 rounded-full bg-white/[0.06] flex-shrink-0" />
                        )}
                        <span
                            className={`text-xs truncate ${
                                (i === 0 ? homeWin : awayWin)
                                    ? "font-semibold text-white"
                                    : "text-gray-300"
                            }`}
                        >
                            {t.name}
                        </span>
                    </div>
                ))}
            </div>
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
            {pick && (
                <span className="hidden sm:inline-flex badge bg-scorelock-500/10 text-scorelock-400 border border-scorelock-500/20 font-mono tabular-nums ml-2 flex-shrink-0">
                    {pick.label} {Math.round(pick.prob * 100)}%
                </span>
            )}
        </a>
    );
}

/* ── Helpers ───────────────────────────────────────────── */

function opponentOf(f: Fixture): { name: string; logo_url: string | null } {
    return isSwedenTeam(f.home_team) ? f.away_team : f.home_team;
}

function firstParagraph(body: string): string {
    const p = body.split(/\n\s*\n/).map((s) => s.trim()).filter(Boolean)[0] ?? body;
    return p.length > 320 ? p.slice(0, 317).trimEnd() + "…" : p;
}

function pickOf(p?: Prediction): { label: string; prob: number } | null {
    // Ärlighets-grind: visa aldrig modellens platta landslagsbaseline som om
    // den vore en per-match-pick. Konf >= 0.2 = modellen har riktig täckning.
    if (!p || p.confidence < 0.2) return null;
    if (p.home_win_prob >= p.draw_prob && p.home_win_prob >= p.away_win_prob)
        return { label: "1", prob: p.home_win_prob };
    if (p.away_win_prob >= p.draw_prob) return { label: "2", prob: p.away_win_prob };
    return { label: "X", prob: p.draw_prob };
}

function displayLeague(name: string): string {
    if (name.toLowerCase().replace(/[_\s]/g, " ").includes("world cup")) return "VM 2026";
    return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function groupByLeague(fixtures: Fixture[]): { league: League; fixtures: Fixture[] }[] {
    const map = new Map<number, { league: League; fixtures: Fixture[] }>();
    for (const f of fixtures) {
        const existing = map.get(f.league.id);
        if (existing) existing.fixtures.push(f);
        else map.set(f.league.id, { league: f.league, fixtures: [f] });
    }
    return Array.from(map.values()).sort(
        (a, b) => (LEAGUE_ORDER[a.league.name] ?? 99) - (LEAGUE_ORDER[b.league.name] ?? 99),
    );
}

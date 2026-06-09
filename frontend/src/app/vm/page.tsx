import { fetchApi } from "@/lib/api";
import type { TournamentStructure, Fixture, Team, TournamentGroup } from "@/lib/types";
import type { Metadata } from "next";
import Link from "next/link";

// Miljö-oberoende referenser: slug resolvas i backend via SportMonks-ext-id,
// Sverige identifieras via lag-NAMN (stabilt från providern) — aldrig via
// lokala auto-increment-id:n som skiljer mellan dev och prod.
const WC_SLUG = "world-cup";
const SWEDEN_NAME = "Sweden";

function isSwedenTeam(t: Team): boolean {
    return t.name === SWEDEN_NAME;
}

export const metadata: Metadata = {
    title: "VM 2026 — Forza Sverige | ScoreLock",
    description:
        "Sverige är i Grupp F med Tunisia, Nederländerna och Japan. ScoreLocks AI-driven VM-täckning — varje minut, varje match. Forza Sverige.",
};

export const revalidate = 300;

export default async function VMPage() {
    let structure: TournamentStructure | null = null;
    try {
        structure = await fetchApi<TournamentStructure>(
            `/api/v1/tournaments/${WC_SLUG}/structure`,
        );
    } catch {
        // Visa tom-state nedan
    }

    if (!structure) {
        return (
            <div className="container-main py-16 text-center">
                <h1 className="text-display-md mb-3">VM 2026</h1>
                <p className="text-gray-400">
                    Turneringsdata laddas — kom tillbaka om en stund.
                </p>
            </div>
        );
    }

    // Hitta Sveriges grupp via lag-namn (inte hårdkodad bokstav/id)
    const swedenGroup =
        structure.groups.find((g) =>
            g.standings.some((s) => isSwedenTeam(s.team)),
        ) ?? null;
    const otherGroups = structure.groups.filter((g) => g !== swedenGroup);

    const swedenFixtures: Fixture[] = swedenGroup
        ? swedenGroup.fixtures.filter(
              (f) => isSwedenTeam(f.home_team) || isSwedenTeam(f.away_team),
          )
        : [];

    const nextSwedenMatch = swedenFixtures
        .filter((f) => f.status === "scheduled" || f.status === "live")
        .sort((a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime())[0];

    return (
        <div>
            {/* ── HERO: FORZA SVERIGE ───────────────────────────── */}
            <section className="relative overflow-hidden border-b border-white/[0.06]">
                {/* Svenska flaggans toning — blå-bas, gul accent */}
                <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-blue-950 to-surface-950 pointer-events-none" />
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(252,211,77,0.18),transparent_55%)] pointer-events-none" />
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,rgba(37,99,235,0.25),transparent_60%)] pointer-events-none" />
                {/* Gult kors-band — abstrakt referens till flaggan */}
                <div className="absolute top-0 bottom-0 left-1/3 w-1 bg-gradient-to-b from-yellow-400/40 via-yellow-300/20 to-transparent pointer-events-none" />

                <div className="container-main py-20 md:py-28 relative">
                    <div className="inline-flex items-center gap-2 mb-5 text-xs font-bold text-yellow-300 tracking-[0.3em] uppercase">
                        <span className="w-2 h-2 rounded-full bg-yellow-300 animate-pulse" />
                        VM 2026{swedenGroup ? ` · GRUPP ${swedenGroup.letter}` : ""}
                    </div>
                    <h1 className="font-serif text-6xl md:text-8xl tracking-tight leading-[0.9] mb-5">
                        <span className="block text-yellow-300">FORZA</span>
                        <span className="block text-white">SVERIGE</span>
                    </h1>
                    <p className="text-lg md:text-2xl text-blue-100 max-w-3xl mb-8 leading-snug">
                        Tre matcher mot Tunisia, Nederländerna och Japan. AI-analys före,
                        under och efter varje match. ScoreLock följer landslaget hela vägen.
                    </p>
                    {nextSwedenMatch && (
                        <CountdownCallout fixture={nextSwedenMatch} />
                    )}
                    <div className="mt-8">
                        <Link
                            href="/landslag/sverige"
                            className="inline-flex items-center gap-2 text-sm text-yellow-200 hover:text-yellow-100 transition font-semibold border-b border-yellow-300/40 hover:border-yellow-200 pb-0.5"
                        >
                            🇸🇪 Hela Sveriges VM-resa →
                        </Link>
                    </div>
                </div>
            </section>

            <div className="container-main py-10 space-y-12">
                {/* ── Sverige-matcherna ──────────────────────────── */}
                {swedenFixtures.length > 0 && (
                    <section>
                        <SectionHeading
                            title="🇸🇪 Sveriges tre gruppspels-matcher"
                            subtitle="Allt vi kan om varje motståndare — uppdateras kontinuerligt under turneringen"
                        />
                        <div className="grid md:grid-cols-3 gap-4">
                            {swedenFixtures
                                .sort(
                                    (a, b) =>
                                        new Date(a.kickoff).getTime() -
                                        new Date(b.kickoff).getTime(),
                                )
                                .map((f, idx) => (
                                    <SwedenMatchCard
                                        key={f.id}
                                        fixture={f}
                                        matchNumber={idx + 1}
                                    />
                                ))}
                        </div>
                    </section>
                )}

                {/* ── Sveriges grupp detaljerat ───────────────────── */}
                {swedenGroup && (
                    <section>
                        <SectionHeading
                            title={`Grupp ${swedenGroup.letter} — Sveriges grupp`}
                            subtitle="Två bästa lagen går direkt till sextondelar · de åtta bästa treorna också"
                        />
                        <SwedenGroupTableLarge group={swedenGroup} />
                    </section>
                )}

                {/* ── Övriga grupper ─────────────────────────────── */}
                <section>
                    <SectionHeading
                        title="Övriga grupper"
                        subtitle="11 grupper, 44 lag, vägen mot finalen 19 juli"
                    />
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {otherGroups.map((g) => (
                            <GroupCard key={g.letter} group={g} />
                        ))}
                    </div>
                </section>

                {/* ── Slutspel ───────────────────────────────────── */}
                {structure.knockouts.length > 0 && (
                    <section>
                        <SectionHeading
                            title="Slutspel"
                            subtitle="Sextondelar → Åttondelar → Kvartsfinaler → Semis → Final · 19 juli"
                        />
                        <div className="space-y-6">
                            {structure.knockouts.map((stage) => (
                                <KnockoutSection key={stage.stage_name} stage={stage} />
                            ))}
                        </div>
                    </section>
                )}
            </div>
        </div>
    );
}

/* ── Components ──────────────────────────────────────────────── */

function SectionHeading({ title, subtitle }: { title: string; subtitle?: string }) {
    return (
        <div className="mb-5">
            <h2 className="font-serif text-3xl md:text-4xl tracking-tight">{title}</h2>
            {subtitle && <p className="text-sm text-gray-400 mt-1">{subtitle}</p>}
        </div>
    );
}

function CountdownCallout({ fixture }: { fixture: Fixture }) {
    const isSwedenHome = isSwedenTeam(fixture.home_team);
    const opponent = isSwedenHome ? fixture.away_team : fixture.home_team;
    const where = isSwedenHome ? "Hemma" : "Borta";
    return (
        <div className="inline-flex flex-col gap-3 bg-yellow-300/10 border border-yellow-300/20 rounded-2xl px-5 py-4 backdrop-blur-sm">
            <div className="text-[11px] uppercase tracking-[0.3em] text-yellow-200/80 font-semibold">
                Nästa match
            </div>
            <div className="flex items-baseline gap-3 flex-wrap">
                <span className="font-serif text-3xl md:text-4xl text-white">
                    Sverige
                </span>
                <span className="text-yellow-300/70 text-xl">vs</span>
                <span className="font-serif text-3xl md:text-4xl text-white">
                    {opponent.name}
                </span>
            </div>
            <div className="flex items-center gap-4 text-sm text-blue-100">
                <span>{formatKickoffLong(fixture.kickoff)}</span>
                <span className="text-blue-300/50">·</span>
                <span>{where}</span>
            </div>
            <Link
                href={`/matches/${fixture.id}`}
                className="mt-2 inline-flex items-center gap-2 text-sm text-yellow-300 hover:text-yellow-200 transition font-semibold"
            >
                Till matchsidan + AI-analys →
            </Link>
        </div>
    );
}

function SwedenMatchCard({
    fixture,
    matchNumber,
}: {
    fixture: Fixture;
    matchNumber: number;
}) {
    const isSwedenHome = isSwedenTeam(fixture.home_team);
    const opponent = isSwedenHome ? fixture.away_team : fixture.home_team;
    return (
        <Link
            href={`/matches/${fixture.id}`}
            className="block rounded-2xl border border-yellow-500/20 bg-gradient-to-br from-yellow-500/[0.06] to-blue-900/20 p-5 hover:border-yellow-400/40 transition group"
        >
            <div className="flex items-baseline justify-between mb-4">
                <div className="text-[10px] uppercase tracking-[0.25em] text-yellow-200/70 font-bold">
                    Match {matchNumber}{fixture.group_letter ? ` · Grupp ${fixture.group_letter}` : ""}
                </div>
                <div className="text-xs text-blue-200/60">
                    {isSwedenHome ? "Hemma" : "Borta"}
                </div>
            </div>
            <div className="flex items-center gap-3 mb-3">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                    src="https://cdn.sportmonks.com/images/soccer/teams/4/18564.png"
                    alt="Sverige"
                    className="w-10 h-10 rounded-lg"
                />
                <div className="text-2xl text-blue-200/40">vs</div>
                {opponent.logo_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                        src={opponent.logo_url}
                        alt={opponent.name}
                        className="w-10 h-10 rounded-lg"
                    />
                ) : (
                    <div className="w-10 h-10 rounded-lg bg-white/[0.06]" />
                )}
                <div className="font-serif text-xl text-white">{opponent.name}</div>
            </div>
            <div className="text-sm text-blue-100 mb-1">
                {formatKickoffLong(fixture.kickoff)}
            </div>
            <div className="text-xs text-yellow-200/70 group-hover:text-yellow-200 transition">
                Till AI-analys →
            </div>
        </Link>
    );
}

function SwedenGroupTableLarge({ group }: { group: TournamentGroup }) {
    const anyPlayed = group.standings.some((s) => s.played > 0);
    return (
        <div className="rounded-2xl border border-yellow-500/20 bg-gradient-to-br from-blue-950/40 to-surface-900/40 p-3 sm:p-6">
            <div className="overflow-x-auto -mx-3 sm:mx-0 px-3 sm:px-0">
                <table className="w-full min-w-[420px]">
                    <thead>
                        <tr className="text-[10px] sm:text-[11px] uppercase tracking-[0.15em] sm:tracking-[0.2em] text-yellow-200/70 border-b border-yellow-500/15 font-bold">
                            <th className="text-left py-3 font-normal w-6 sm:w-8">#</th>
                            <th className="text-left py-3 font-normal">Lag</th>
                            <th className="text-center py-3 font-normal w-10 sm:w-12">Sp</th>
                            <th className="text-center py-3 font-normal w-8 sm:w-10">V</th>
                            <th className="text-center py-3 font-normal w-8 sm:w-10">O</th>
                            <th className="text-center py-3 font-normal w-8 sm:w-10">F</th>
                            <th className="text-center py-3 font-normal w-12 sm:w-14">Mskill</th>
                            <th className="text-center py-3 font-normal w-10 sm:w-12">P</th>
                        </tr>
                    </thead>
                    <tbody>
                        {group.standings.map((s, idx) => {
                            const isSweden = isSwedenTeam(s.team);
                            return (
                                <tr
                                    key={s.team.id}
                                    className={
                                        "border-b border-white/[0.04] " +
                                        (isSweden
                                            ? "bg-yellow-500/[0.06]"
                                            : "")
                                    }
                                >
                                    <td
                                        className={
                                            "py-3 font-mono text-xs sm:text-sm " +
                                            (idx < 2
                                                ? "text-yellow-300 font-bold"
                                                : "text-gray-500")
                                        }
                                    >
                                        {idx + 1}
                                    </td>
                                    <td className="py-3">
                                        <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                                            {s.team.logo_url && (
                                                // eslint-disable-next-line @next/next/no-img-element
                                                <img
                                                    src={s.team.logo_url}
                                                    alt=""
                                                    className="w-5 h-5 sm:w-6 sm:h-6 rounded-sm flex-shrink-0"
                                                />
                                            )}
                                            <span
                                                className={
                                                    "truncate " +
                                                    (isSweden
                                                        ? "font-serif text-base sm:text-lg text-yellow-200"
                                                        : "text-sm sm:text-base text-gray-200")
                                                }
                                            >
                                                {isSweden ? `🇸🇪 ${s.team.name}` : s.team.name}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="text-center py-3 text-xs sm:text-sm">{anyPlayed ? s.played : "—"}</td>
                                    <td className="text-center py-3 text-xs sm:text-sm">{anyPlayed ? s.won : "—"}</td>
                                    <td className="text-center py-3 text-xs sm:text-sm">{anyPlayed ? s.drawn : "—"}</td>
                                    <td className="text-center py-3 text-xs sm:text-sm">{anyPlayed ? s.lost : "—"}</td>
                                    <td
                                        className={
                                            "text-center py-3 text-xs sm:text-sm " +
                                            (anyPlayed
                                                ? s.goal_diff > 0
                                                    ? "text-emerald-400"
                                                    : s.goal_diff < 0
                                                      ? "text-rose-400"
                                                      : "text-gray-400"
                                                : "text-gray-600")
                                        }
                                    >
                                        {anyPlayed
                                            ? `${s.goal_diff > 0 ? "+" : ""}${s.goal_diff}`
                                            : "—"}
                                    </td>
                                    <td
                                        className={
                                            "text-center py-3 text-xs sm:text-sm font-bold " +
                                            (isSweden ? "text-yellow-300" : "text-white")
                                        }
                                    >
                                        {anyPlayed ? s.points : "—"}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
            {!anyPlayed && (
                <p className="text-xs text-blue-200/60 mt-4 italic">
                    Gruppspelet startar 11 juni — tabellen fylls allt eftersom matcher avgörs.
                </p>
            )}
        </div>
    );
}

function GroupCard({ group }: { group: TournamentGroup }) {
    const anyPlayed = group.standings.some((s) => s.played > 0);
    return (
        <div className="rounded-xl border border-white/[0.06] bg-surface-900/40 p-4">
            <div className="flex items-baseline justify-between mb-3">
                <div className="font-serif text-2xl tracking-tight">
                    Grupp {group.letter}
                </div>
                <div className="text-[11px] text-gray-500">
                    {group.fixtures.length} matcher
                </div>
            </div>
            <div className="space-y-1.5">
                {group.standings.map((s, idx) => (
                    <div
                        key={s.team.id}
                        className={
                            "flex items-center justify-between gap-2 text-sm " +
                            (idx < 2 ? "text-gray-100" : "text-gray-400")
                        }
                    >
                        <div className="flex items-center gap-2 min-w-0">
                            {s.team.logo_url && (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img
                                    src={s.team.logo_url}
                                    alt=""
                                    className="w-4 h-4 rounded-sm flex-shrink-0"
                                />
                            )}
                            <span className="truncate">{s.team.name}</span>
                        </div>
                        {anyPlayed && (
                            <span className="text-xs text-gray-500 font-mono">
                                {s.points}p
                            </span>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}

function KnockoutSection({
    stage,
}: {
    stage: import("@/lib/types").TournamentKnockoutStage;
}) {
    return (
        <div>
            <div className="flex items-baseline gap-3 mb-3">
                <h3 className="font-serif text-xl">{translateStage(stage.stage_name)}</h3>
                <span className="text-xs text-gray-500">
                    {stage.fixtures.length} matcher
                </span>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {stage.fixtures.map((f) => (
                    <KnockoutFixtureCard key={f.id} fixture={f} />
                ))}
            </div>
        </div>
    );
}

function KnockoutFixtureCard({ fixture }: { fixture: Fixture }) {
    const isSwedenInvolved =
        isSwedenTeam(fixture.home_team) || isSwedenTeam(fixture.away_team);
    return (
        <Link
            href={`/matches/${fixture.id}`}
            className={
                "block rounded-xl p-4 border transition " +
                (isSwedenInvolved
                    ? "border-yellow-500/30 bg-yellow-500/[0.04] hover:border-yellow-400/50"
                    : "border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04]")
            }
        >
            <div className="text-[11px] uppercase tracking-wider text-gray-500 mb-2">
                {translateStage(fixture.stage_name || "")}
            </div>
            <div className="space-y-2 mb-3">
                <TeamRow team={fixture.home_team.name} flag={fixture.home_team.logo_url} swedenHighlight={isSwedenTeam(fixture.home_team)} />
                <TeamRow team={fixture.away_team.name} flag={fixture.away_team.logo_url} swedenHighlight={isSwedenTeam(fixture.away_team)} />
            </div>
            <div className="text-xs text-gray-400">{formatKickoffLong(fixture.kickoff)}</div>
        </Link>
    );
}

function TeamRow({
    team,
    flag,
    swedenHighlight,
}: {
    team: string;
    flag: string | null;
    swedenHighlight?: boolean;
}) {
    const isPlaceholder =
        team.toLowerCase().startsWith("winner") || team.toLowerCase().startsWith("loser");
    return (
        <div className="flex items-center gap-2">
            {flag ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={flag} alt="" className="w-5 h-5 rounded-sm object-cover" />
            ) : (
                <span className="w-5 h-5 rounded-sm bg-white/[0.06]" />
            )}
            <span
                className={
                    "text-sm truncate " +
                    (swedenHighlight
                        ? "text-yellow-300 font-semibold"
                        : isPlaceholder
                          ? "italic text-gray-500"
                          : "text-gray-200")
                }
            >
                {swedenHighlight ? `🇸🇪 ${team}` : team}
            </span>
        </div>
    );
}

/* ── Helpers ──────────────────────────────────────────────── */

function translateStage(s: string): string {
    const map: Record<string, string> = {
        "Group Stage": "Gruppspel",
        "Round of 32": "Sextondelsfinal",
        "Round of 16": "Åttondelsfinal",
        "Quarter-finals": "Kvartsfinal",
        "Semi-finals": "Semifinal",
        Final: "Final",
        "3rd Place Final": "Bronsmatch",
    };
    return map[s] || s;
}

function formatKickoffLong(iso: string): string {
    try {
        const d = new Date(iso);
        return d.toLocaleString("sv-SE", {
            weekday: "long",
            day: "numeric",
            month: "long",
            hour: "2-digit",
            minute: "2-digit",
        });
    } catch {
        return iso;
    }
}

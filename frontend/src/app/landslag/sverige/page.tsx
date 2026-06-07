import { fetchApi } from "@/lib/api";
import type { TournamentStructure, Fixture, TournamentGroup } from "@/lib/types";
import type { Metadata } from "next";
import Link from "next/link";

const WC_LEAGUE_ID = 12;
const SWEDEN_TEAM_ID = 1021;
const SWEDEN_GROUP = "F";

export const metadata: Metadata = {
    title: "Sverige · VM 2026 — Forza Sverige | ScoreLock",
    description:
        "Allt om Sveriges VM 2026: 3 matcher i Grupp F mot Tunisia, Nederländerna och Japan. AI-analys, odds, ställning. Forza Sverige.",
};

export const revalidate = 300;

export default async function SwedenPage() {
    let structure: TournamentStructure | null = null;
    try {
        structure = await fetchApi<TournamentStructure>(
            `/api/v1/tournaments/${WC_LEAGUE_ID}/structure`,
        );
    } catch {}

    const swedenGroup =
        structure?.groups.find((g) => g.letter === SWEDEN_GROUP) ?? null;
    const swedenFixtures: Fixture[] =
        swedenGroup?.fixtures
            .filter(
                (f) =>
                    f.home_team.id === SWEDEN_TEAM_ID ||
                    f.away_team.id === SWEDEN_TEAM_ID,
            )
            .sort(
                (a, b) =>
                    new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime(),
            ) ?? [];

    const nextMatch = swedenFixtures.find(
        (f) => f.status === "scheduled" || f.status === "live",
    );

    return (
        <div>
            {/* ── HERO ─────────────────────────────────────────── */}
            <section className="relative overflow-hidden border-b border-yellow-500/15">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-blue-950 to-surface-950" />
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(252,211,77,0.22),transparent_55%)]" />
                <div className="absolute top-0 bottom-0 left-1/4 w-px bg-gradient-to-b from-yellow-300/30 to-transparent" />

                <div className="container-main py-16 md:py-24 relative">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="text-7xl md:text-8xl">🇸🇪</div>
                        <div>
                            <div className="text-xs font-bold uppercase tracking-[0.3em] text-yellow-300 mb-1">
                                LANDSLAGET · VM 2026
                            </div>
                            <h1 className="font-serif text-5xl md:text-7xl tracking-tight leading-none text-white">
                                Sverige
                            </h1>
                        </div>
                    </div>
                    <p className="text-lg md:text-xl text-blue-100 max-w-2xl leading-snug">
                        Tre matcher i Grupp F. En öppning mot Tunisia, en
                        avgörande mot Nederländerna, en avslutning mot Japan.
                        ScoreLocks AI följer varje minut.
                    </p>
                </div>
            </section>

            <div className="container-main py-10 space-y-12">
                {/* ── Stat-line ───────────────────────────────── */}
                <div className="grid sm:grid-cols-3 gap-4">
                    <StatBox
                        label="Gruppspels-matcher"
                        value={String(swedenFixtures.length)}
                        sub="Tunisia · Nederländerna · Japan"
                    />
                    <StatBox
                        label="Grupp F"
                        value={swedenGroup?.standings.length.toString() ?? "—"}
                        sub="lag · 2 bästa går till slutspel"
                    />
                    <StatBox
                        label="Premiär"
                        value="15 juni"
                        sub={nextMatch ? matchTimeDay(nextMatch) : "Sverige vs Tunisia"}
                    />
                </div>

                {/* ── Tre matcher ──────────────────────────────── */}
                {swedenFixtures.length > 0 && (
                    <section>
                        <SectionHeading
                            title="Resan genom Grupp F"
                            subtitle="Klick in på matchsidan för AI-analys, odds och live-data när kickoff närmar sig"
                        />
                        <div className="grid md:grid-cols-3 gap-4">
                            {swedenFixtures.map((f, i) => (
                                <SwedenMatchHeroCard
                                    key={f.id}
                                    fixture={f}
                                    matchNumber={i + 1}
                                    isNext={f.id === nextMatch?.id}
                                />
                            ))}
                        </div>
                    </section>
                )}

                {/* ── Grupp F-tabell ──────────────────────────── */}
                {swedenGroup && (
                    <section>
                        <SectionHeading
                            title="Grupp F-ställningen"
                            subtitle="Uppdateras live när gruppspels-matcher avgörs"
                        />
                        <GroupFTable group={swedenGroup} />
                    </section>
                )}

                {/* ── Narrativ ────────────────────────────────── */}
                <section className="rounded-2xl border border-yellow-500/15 bg-gradient-to-br from-yellow-500/[0.04] to-blue-950/30 p-6 md:p-10">
                    <h2 className="font-serif text-3xl md:text-4xl tracking-tight mb-4">
                        Varför ScoreLock följer Sverige
                    </h2>
                    <div className="space-y-4 text-base md:text-lg text-gray-200 leading-relaxed max-w-3xl">
                        <p>
                            Det här är Sveriges första VM-äventyr på flera år. Tre
                            matcher avgör allt — gruppspelet är slutspel-stil från
                            första minuten. ScoreLocks AI bygger en grundad analys
                            före varje match, uppdaterar live när momentum vänder,
                            och summerar vad som faktiskt avgjorde efter slutsignalen.
                        </p>
                        <p>
                            Vi citerar marknadens odds, vår modells siffror och hur de
                            två skiljer sig — det är där värdet ligger. Vi flaggar
                            också när data saknas. Inga clickbait-rubriker. Inga
                            magkänsla-tips. Bara siffror, dossiér och svenskspråkig
                            sport-journalistik på modernt vis.
                        </p>
                    </div>
                </section>
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

function StatBox({
    label,
    value,
    sub,
}: {
    label: string;
    value: string;
    sub: string;
}) {
    return (
        <div className="rounded-2xl border border-yellow-500/10 bg-yellow-500/[0.03] p-5">
            <div className="text-[10px] uppercase tracking-[0.25em] text-yellow-200/70 mb-2 font-bold">
                {label}
            </div>
            <div className="font-serif text-4xl text-yellow-300 mb-2 tracking-tight">
                {value}
            </div>
            <div className="text-xs text-blue-100/70">{sub}</div>
        </div>
    );
}

function SwedenMatchHeroCard({
    fixture,
    matchNumber,
    isNext,
}: {
    fixture: Fixture;
    matchNumber: number;
    isNext: boolean;
}) {
    const isSwedenHome = fixture.home_team.id === SWEDEN_TEAM_ID;
    const opponent = isSwedenHome ? fixture.away_team : fixture.home_team;
    const kickoff = new Date(fixture.kickoff);

    return (
        <Link
            href={`/matches/${fixture.id}`}
            className={
                "block rounded-2xl border p-5 transition-all group " +
                (isNext
                    ? "border-yellow-400/40 bg-gradient-to-br from-yellow-500/[0.08] to-blue-900/30 ring-1 ring-yellow-400/20"
                    : "border-yellow-500/15 bg-gradient-to-br from-yellow-500/[0.03] to-blue-950/20 hover:border-yellow-400/30")
            }
        >
            <div className="flex items-baseline justify-between mb-4">
                <div className="text-[10px] uppercase tracking-[0.25em] text-yellow-200/70 font-bold">
                    Match {matchNumber} · Grupp F
                </div>
                {isNext && (
                    <div className="text-[10px] uppercase tracking-[0.25em] text-yellow-300 font-bold">
                        Nästa
                    </div>
                )}
            </div>
            <div className="flex items-center gap-3 mb-3">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                    src="https://cdn.sportmonks.com/images/soccer/teams/4/18564.png"
                    alt="Sverige"
                    className="w-10 h-10 rounded-lg"
                />
                <div className="text-xl text-blue-200/40">vs</div>
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
            <div className="text-sm text-blue-100/80 mb-1">
                {kickoff.toLocaleDateString("sv-SE", {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                })}
            </div>
            <div className="text-sm text-blue-100/60 mb-3">
                kl. {kickoff.toLocaleTimeString("sv-SE", { hour: "2-digit", minute: "2-digit" })} · {isSwedenHome ? "Hemma" : "Borta"}
            </div>
            <div className="text-xs text-yellow-200/70 group-hover:text-yellow-200 transition pt-3 border-t border-yellow-500/10">
                AI-analys + odds + broadcasts →
            </div>
        </Link>
    );
}

function GroupFTable({ group }: { group: TournamentGroup }) {
    const anyPlayed = group.standings.some((s) => s.played > 0);
    return (
        <div className="rounded-2xl border border-yellow-500/20 bg-gradient-to-br from-blue-950/40 to-surface-900/40 p-4 md:p-6 overflow-x-auto">
            <table className="w-full min-w-[400px]">
                <thead>
                    <tr className="text-[11px] uppercase tracking-[0.2em] text-yellow-200/70 border-b border-yellow-500/15 font-bold">
                        <th className="text-left py-3 font-normal w-6">#</th>
                        <th className="text-left py-3 font-normal">Lag</th>
                        <th className="text-center py-3 font-normal w-10">Sp</th>
                        <th className="text-center py-3 font-normal w-8">V</th>
                        <th className="text-center py-3 font-normal w-8">O</th>
                        <th className="text-center py-3 font-normal w-8">F</th>
                        <th className="text-center py-3 font-normal w-12">±</th>
                        <th className="text-center py-3 font-normal w-10">P</th>
                    </tr>
                </thead>
                <tbody>
                    {group.standings.map((s, idx) => {
                        const isSweden = s.team.id === SWEDEN_TEAM_ID;
                        return (
                            <tr
                                key={s.team.id}
                                className={
                                    "border-b border-white/[0.04] " +
                                    (isSweden ? "bg-yellow-500/[0.06]" : "")
                                }
                            >
                                <td
                                    className={
                                        "py-3 font-mono text-sm " +
                                        (idx < 2
                                            ? "text-yellow-300 font-bold"
                                            : "text-gray-500")
                                    }
                                >
                                    {idx + 1}
                                </td>
                                <td className="py-3 flex items-center gap-3">
                                    {s.team.logo_url && (
                                        // eslint-disable-next-line @next/next/no-img-element
                                        <img
                                            src={s.team.logo_url}
                                            alt=""
                                            className="w-6 h-6 rounded-sm flex-shrink-0"
                                        />
                                    )}
                                    <span
                                        className={
                                            isSweden
                                                ? "font-serif text-lg text-yellow-200 truncate"
                                                : "text-gray-200 truncate"
                                        }
                                    >
                                        {isSweden ? `🇸🇪 ${s.team.name}` : s.team.name}
                                    </span>
                                </td>
                                <td className="text-center py-3 text-sm">{anyPlayed ? s.played : "—"}</td>
                                <td className="text-center py-3 text-sm">{anyPlayed ? s.won : "—"}</td>
                                <td className="text-center py-3 text-sm">{anyPlayed ? s.drawn : "—"}</td>
                                <td className="text-center py-3 text-sm">{anyPlayed ? s.lost : "—"}</td>
                                <td className="text-center py-3 text-sm">
                                    {anyPlayed
                                        ? `${s.goal_diff > 0 ? "+" : ""}${s.goal_diff}`
                                        : "—"}
                                </td>
                                <td
                                    className={
                                        "text-center py-3 font-bold " +
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
    );
}

function matchTimeDay(f: Fixture): string {
    const d = new Date(f.kickoff);
    return d.toLocaleDateString("sv-SE", { day: "numeric", month: "long" });
}

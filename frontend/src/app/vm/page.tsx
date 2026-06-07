import { fetchApi } from "@/lib/api";
import { formatKickoff } from "@/lib/utils";
import type { TournamentStructure, Fixture } from "@/lib/types";
import type { Metadata } from "next";
import Link from "next/link";

const WC_LEAGUE_ID = 12;

export const metadata: Metadata = {
    title: "VM 2026 — Grupper, slutspel, AI-analys | ScoreLock",
    description:
        "FIFA World Cup 2026 i USA, Kanada och Mexico. Alla 12 grupper, 32 slutspelsmatcher och AI-driven analys före, under och efter varje match.",
};

// Pre-tournament: revalidera var 5 min så standings uppdateras nästan-live när
// gruppspelet kör. När matcher avgörs visar GroupTable de senaste poängen.
export const revalidate = 300;

export default async function VMPage() {
    let structure: TournamentStructure | null = null;
    try {
        structure = await fetchApi<TournamentStructure>(
            `/api/v1/tournaments/${WC_LEAGUE_ID}/structure`,
        );
    } catch {
        // Visa tom-state i UI nedan; logga inte krasch
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

    // Nästa kommande matcher (alla stages) — för "Nästa match"-strip
    const allFixtures: Fixture[] = [
        ...structure.groups.flatMap((g) => g.fixtures),
        ...structure.knockouts.flatMap((k) => k.fixtures),
    ];
    const upcoming = allFixtures
        .filter((f) => f.status === "scheduled" || f.status === "live")
        .sort((a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime())
        .slice(0, 5);

    return (
        <div>
            {/* ── Hero ─────────────────────────────────────────── */}
            <section className="relative overflow-hidden border-b border-white/[0.06]">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(59,130,246,0.12),transparent_60%)] pointer-events-none" />
                <div className="container-main py-16 md:py-24 relative">
                    <div className="inline-flex items-center gap-2 mb-5 text-xs font-medium text-scorelock-300 tracking-widest uppercase">
                        <span className="w-2 h-2 rounded-full bg-scorelock-400 animate-pulse" />
                        {structure.season_label} · {dateRangeLabel(structure)}
                    </div>
                    <h1 className="font-serif text-5xl md:text-7xl tracking-tight leading-[0.95] mb-4">
                        VM 2026
                    </h1>
                    <p className="text-lg md:text-xl text-gray-300 max-w-2xl mb-8">
                        Hela turneringen — 48 lag, 12 grupper, 104 matcher. AI-analys före,
                        under och efter varje match. Sverige saknas, vi följer ändå.
                    </p>
                    <div className="flex flex-wrap gap-3 text-sm">
                        <span className="px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.08]">
                            🇺🇸🇨🇦🇲🇽 USA · Kanada · Mexico
                        </span>
                        <span className="px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.08]">
                            ⚽ 48 lag
                        </span>
                        <span className="px-3 py-1.5 rounded-full bg-white/[0.04] border border-white/[0.08]">
                            🏆 12 grupper
                        </span>
                    </div>
                </div>
            </section>

            <div className="container-main py-10 space-y-12">
                {/* ── Sverige-card ───────────────────────────────── */}
                <SwedishLensCard />

                {/* ── Nästa matcher-strip ────────────────────────── */}
                {upcoming.length > 0 && (
                    <section>
                        <SectionHeading title="Nästa matcher" />
                        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-3">
                            {upcoming.map((f) => (
                                <NextMatchCard key={f.id} fixture={f} />
                            ))}
                        </div>
                    </section>
                )}

                {/* ── Grupper ────────────────────────────────────── */}
                <section>
                    <SectionHeading title="Gruppspel" subtitle="12 grupper × 4 lag · de två bästa går till slutspel + de 8 bästa treorna" />
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {structure.groups.map((g) => (
                            <GroupCard key={g.letter} group={g} />
                        ))}
                    </div>
                </section>

                {/* ── Slutspel ───────────────────────────────────── */}
                {structure.knockouts.length > 0 && (
                    <section>
                        <SectionHeading
                            title="Slutspel"
                            subtitle="Sextondelar → Åttondelar → Kvartsfinaler → Semis → Final"
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
            {subtitle && (
                <p className="text-sm text-gray-400 mt-1">{subtitle}</p>
            )}
        </div>
    );
}

function SwedishLensCard() {
    return (
        <section className="rounded-2xl border border-yellow-500/15 bg-gradient-to-br from-yellow-500/[0.04] to-transparent p-6 md:p-8">
            <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-yellow-500/10 border border-yellow-500/20 flex items-center justify-center flex-shrink-0 text-2xl">
                    🇸🇪
                </div>
                <div className="flex-1">
                    <h3 className="font-serif text-2xl mb-2">
                        Sverige saknas — vi följer ändå
                    </h3>
                    <p className="text-gray-300 mb-4 max-w-3xl">
                        Sverige kvalade inte in. Vi följer Norge (första VM på 26 år, med
                        Haaland som drag-lok), Danmarks gruppspel och svenska spelare i
                        andra landslag. Allsvenskan rullar parallellt — vi täcker bägge.
                    </p>
                    <div className="flex flex-wrap gap-2">
                        <Link
                            href="/matches"
                            className="px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm hover:bg-white/[0.08] transition"
                        >
                            Allsvenskan denna helg →
                        </Link>
                        <Link
                            href="/standings"
                            className="px-3 py-1.5 rounded-lg bg-white/[0.04] border border-white/[0.08] text-sm hover:bg-white/[0.08] transition"
                        >
                            Allsvenskan-tabellen →
                        </Link>
                    </div>
                </div>
            </div>
        </section>
    );
}

function NextMatchCard({ fixture }: { fixture: Fixture }) {
    return (
        <Link
            href={`/matches/${fixture.id}`}
            className="block rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 hover:bg-white/[0.04] hover:border-white/[0.12] transition"
        >
            <div className="text-[11px] uppercase tracking-wider text-gray-500 mb-2">
                {stageLabel(fixture)}
            </div>
            <div className="space-y-2 mb-3">
                <TeamRow team={fixture.home_team.name} flag={fixture.home_team.logo_url} />
                <TeamRow team={fixture.away_team.name} flag={fixture.away_team.logo_url} />
            </div>
            <div className="text-xs text-gray-400">{formatKickoff(fixture.kickoff)}</div>
        </Link>
    );
}

function TeamRow({ team, flag }: { team: string; flag: string | null }) {
    const isPlaceholder = team.toLowerCase().startsWith("winner") || team.toLowerCase().startsWith("loser");
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
                    (isPlaceholder ? "italic text-gray-500" : "text-gray-200")
                }
            >
                {team}
            </span>
        </div>
    );
}

function GroupCard({ group }: { group: import("@/lib/types").TournamentGroup }) {
    const anyPlayed = group.standings.some((s) => s.played > 0);
    return (
        <div className="rounded-xl border border-white/[0.06] bg-surface-900/40 p-4">
            <div className="flex items-baseline justify-between mb-3">
                <div className="font-serif text-2xl tracking-tight">Grupp {group.letter}</div>
                <div className="text-[11px] text-gray-500">{group.fixtures.length} matcher</div>
            </div>
            {anyPlayed ? (
                <table className="w-full text-sm">
                    <thead>
                        <tr className="text-[10px] uppercase tracking-wider text-gray-500 border-b border-white/[0.04]">
                            <th className="text-left py-2 font-normal">Lag</th>
                            <th className="text-center py-2 font-normal w-8">Sp</th>
                            <th className="text-center py-2 font-normal w-8">P</th>
                            <th className="text-center py-2 font-normal w-10">±</th>
                        </tr>
                    </thead>
                    <tbody>
                        {group.standings.map((s, idx) => (
                            <tr
                                key={s.team.id}
                                className={
                                    "border-b border-white/[0.04] " +
                                    (idx < 2 ? "text-gray-100" : "text-gray-400")
                                }
                            >
                                <td className="py-2 flex items-center gap-2">
                                    {s.team.logo_url && (
                                        // eslint-disable-next-line @next/next/no-img-element
                                        <img
                                            src={s.team.logo_url}
                                            alt=""
                                            className="w-4 h-4 rounded-sm"
                                        />
                                    )}
                                    <span className="truncate">{s.team.name}</span>
                                </td>
                                <td className="text-center py-2">{s.played}</td>
                                <td className="text-center py-2 font-semibold">{s.points}</td>
                                <td
                                    className={
                                        "text-center py-2 " +
                                        (s.goal_diff > 0
                                            ? "text-emerald-400"
                                            : s.goal_diff < 0
                                              ? "text-rose-400"
                                              : "text-gray-400")
                                    }
                                >
                                    {s.goal_diff > 0 ? "+" : ""}
                                    {s.goal_diff}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) : (
                <div className="space-y-2">
                    {group.standings.map((s) => (
                        <div
                            key={s.team.id}
                            className="flex items-center gap-2 text-sm text-gray-300"
                        >
                            {s.team.logo_url && (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img
                                    src={s.team.logo_url}
                                    alt=""
                                    className="w-4 h-4 rounded-sm"
                                />
                            )}
                            <span className="truncate">{s.team.name}</span>
                        </div>
                    ))}
                </div>
            )}
            <Link
                href={`/matches?league_id=12&group=${group.letter}`}
                className="block mt-3 pt-3 border-t border-white/[0.04] text-xs text-gray-500 hover:text-gray-300 transition"
            >
                Alla matcher i grupp {group.letter} →
            </Link>
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
                <span className="text-xs text-gray-500">{stage.fixtures.length} matcher</span>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {stage.fixtures.map((f) => (
                    <NextMatchCard key={f.id} fixture={f} />
                ))}
            </div>
        </div>
    );
}

/* ── Helpers ──────────────────────────────────────────────── */

function stageLabel(f: Fixture): string {
    if (f.group_letter) return `Grupp ${f.group_letter}`;
    return translateStage(f.stage_name || "");
}

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

function dateRangeLabel(s: TournamentStructure): string {
    if (!s.season_start || !s.season_end) return "";
    const start = new Date(s.season_start);
    const end = new Date(s.season_end);
    const fmt = (d: Date) =>
        d.toLocaleDateString("sv-SE", { day: "numeric", month: "long" });
    return `${fmt(start)} – ${fmt(end)}`;
}

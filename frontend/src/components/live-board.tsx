"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useLiveScores } from "@/lib/use-live-scores";
import type { Fixture } from "@/lib/types";
import { fmtTime, sameStockholmDay } from "@/lib/time";

/**
 * Live-boarden — livescore-upplevelsen som ÄR ScoreLocks kärna.
 *
 * Live-läge: stora score-kort som tickar i realtid (WebSocket + klient-klocka),
 * mål-flash när någon näter. Vilo-läge: dagens kommande matcher med avsparks-
 * tider. Renderar null bara när dagen är helt tom (Härnäst-bandet täcker då).
 *
 * Status-övergångar (scheduled → live) fångas av 60s-pollen mot /fixtures/live.
 */
export function LiveBoard({ initialFixtures }: { initialFixtures: Fixture[] }) {
    const [fixtures, setFixtures] = useState<Fixture[]>(initialFixtures);
    const { getLiveState, liveStates } = useLiveScores(initialFixtures);

    useEffect(() => {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "";
        let cancelled = false;

        async function poll() {
            try {
                const res = await fetch(`${apiBase}/api/v1/fixtures/live`, {
                    signal: AbortSignal.timeout(6000),
                });
                if (!res.ok || cancelled) return;
                const liveNow: Fixture[] = await res.json();
                if (liveNow.length === 0) return;
                // Merga in live-statusar i dagens lista (fångar scheduled→live)
                setFixtures((prev) => {
                    const byId = new Map(prev.map((f) => [f.id, f]));
                    for (const lf of liveNow) byId.set(lf.id, lf);
                    return Array.from(byId.values());
                });
            } catch {
                /* boarden får aldrig krascha — behåll senaste kända */
            }
        }

        poll(); // direkt vid mount — sim/server-rendern kan ligga före live-läget
        const id = setInterval(poll, 60_000);
        return () => {
            cancelled = true;
            clearInterval(id);
        };
    }, []);

    const isLiveNow = (f: Fixture) =>
        f.status === "live" || f.status === "halftime" || liveStates.has(f.id);

    const live = fixtures.filter(isLiveNow);

    // Dagens kommande (lokal dygnsgräns), sorterade på avspark
    const today = new Date();
    const upcomingToday = fixtures
        .filter(
            (f) =>
                f.status === "scheduled" &&
                !liveStates.has(f.id) &&
                sameStockholmDay(f.kickoff, today),
        )
        .sort((a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime());

    if (live.length === 0 && upcomingToday.length === 0) return null;

    return (
        <section className="border-b border-white/[0.04] py-10">
            <div className="container-main">
                <div className="flex items-baseline justify-between mb-5">
                    <h2 className="font-serif text-2xl sm:text-3xl tracking-tight flex items-center gap-3">
                        {live.length > 0 ? (
                            <>
                                <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
                                Live just nu
                            </>
                        ) : (
                            "Avspark idag"
                        )}
                    </h2>
                    <Link
                        href="/matches"
                        className="text-sm text-scorelock-400 hover:text-scorelock-300 transition-colors"
                    >
                        Alla matcher →
                    </Link>
                </div>

                {live.length > 0 ? (
                    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {live.map((f) => (
                            <LiveCard key={f.id} fixture={f} state={getLiveState(f)} />
                        ))}
                    </div>
                ) : (
                    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
                        {upcomingToday.slice(0, 8).map((f) => (
                            <UpcomingTodayCard key={f.id} fixture={f} />
                        ))}
                    </div>
                )}
            </div>
        </section>
    );
}

/* ── Live-kortet: scoren är hjälten ───────────────────────── */

function LiveCard({
    fixture,
    state,
}: {
    fixture: Fixture;
    state: ReturnType<ReturnType<typeof useLiveScores>["getLiveState"]>;
}) {
    const hg = state?.homeGoals ?? fixture.home_goals ?? 0;
    const ag = state?.awayGoals ?? fixture.away_goals ?? 0;
    const minute = state?.minute;
    const flash = state?.goalJustScored ?? false;

    return (
        <Link
            href={`/matches/${fixture.id}`}
            className={
                "block rounded-2xl border p-5 transition-all duration-300 hover:-translate-y-1 " +
                (flash
                    ? "border-yellow-400/60 animate-goal-flash"
                    : "border-red-500/25 bg-red-950/[0.12] hover:border-red-400/40")
            }
        >
            <div className="flex items-center justify-between mb-4">
                <span className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.25em] text-red-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                    {fixture.status === "halftime" ? "Halvtid" : "Live"}
                </span>
                {minute != null && fixture.status !== "halftime" && (
                    <span className="font-mono text-sm text-red-300 tabular-nums">
                        {minute}′
                    </span>
                )}
            </div>

            <div className="space-y-2.5">
                <TeamScoreRow
                    team={fixture.home_team}
                    goals={hg}
                    scored={flash && state?.goalSide === "home"}
                />
                <TeamScoreRow
                    team={fixture.away_team}
                    goals={ag}
                    scored={flash && state?.goalSide === "away"}
                />
            </div>

            <p className="mt-4 pt-3 border-t border-white/[0.05] text-[11px] text-gray-500">
                {fixture.group_letter
                    ? `VM · Grupp ${fixture.group_letter} · `
                    : ""}
                Livepuls + AI-uppdateringar →
            </p>
        </Link>
    );
}

function TeamScoreRow({
    team,
    goals,
    scored,
}: {
    team: { name: string; logo_url: string | null };
    goals: number;
    scored: boolean;
}) {
    return (
        <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 min-w-0">
                {team.logo_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={team.logo_url} alt="" className="w-7 h-7 rounded-sm object-cover flex-shrink-0" />
                ) : (
                    <span className="w-7 h-7 rounded-sm bg-white/[0.06] flex-shrink-0" />
                )}
                <span className="text-base text-gray-100 truncate">{team.name}</span>
            </div>
            <span
                className={
                    "font-mono text-3xl font-bold tabular-nums " +
                    (scored ? "text-yellow-300 animate-score-pop" : "text-white")
                }
            >
                {goals}
            </span>
        </div>
    );
}

/* ── Dagens kommande ──────────────────────────────────────── */

function UpcomingTodayCard({ fixture }: { fixture: Fixture }) {
    return (
        <Link
            href={`/matches/${fixture.id}`}
            className="block rounded-xl border border-white/[0.07] bg-white/[0.02] p-4 transition-all duration-300 hover:border-white/[0.14] hover:-translate-y-0.5"
        >
            <p className="font-mono text-lg text-scorelock-400 tabular-nums mb-3" suppressHydrationWarning>
                {fmtTime(fixture.kickoff)}
            </p>
            <MiniTeam team={fixture.home_team} />
            <MiniTeam team={fixture.away_team} />
            {fixture.group_letter && (
                <p className="mt-2.5 text-[10px] uppercase tracking-wider text-gray-600">
                    Grupp {fixture.group_letter}
                </p>
            )}
        </Link>
    );
}

function MiniTeam({ team }: { team: { name: string; logo_url: string | null } }) {
    return (
        <div className="flex items-center gap-2 py-0.5">
            {team.logo_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={team.logo_url} alt="" className="w-5 h-5 rounded-sm object-cover" />
            ) : (
                <span className="w-5 h-5 rounded-sm bg-white/[0.06]" />
            )}
            <span className="text-sm text-gray-200 truncate">{team.name}</span>
        </div>
    );
}


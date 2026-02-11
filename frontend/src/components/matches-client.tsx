"use client";

import { LiveMatchCard } from "@/components/live-match-card";
import type { Fixture, Prediction, ValueBet } from "@/lib/types";
import { useLiveScores } from "@/lib/use-live-scores";
import { useEffect, useState } from "react";
import Link from "next/link";

interface MatchesClientProps {
    initialFixtures: Fixture[];
    predictions: Prediction[];
    valueBets: ValueBet[];
}

/**
 * Client-side wrapper for the Matches page.
 *
 * Connects to WebSocket for live score updates and auto-refreshes
 * fixture data every 60 seconds to catch new matches.
 */
export function MatchesClient({
    initialFixtures,
    predictions,
    valueBets,
}: MatchesClientProps) {
    const [fixtures, setFixtures] = useState(initialFixtures);
    const { getLiveState } = useLiveScores(initialFixtures);

    // Auto-refresh fixture list every 60 seconds
    useEffect(() => {
        const interval = setInterval(async () => {
            try {
                const apiBase =
                    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
                const resp = await fetch(`${apiBase}/api/v1/fixtures`, {
                    signal: AbortSignal.timeout(5000),
                });
                if (resp.ok) {
                    const data: Fixture[] = await resp.json();
                    setFixtures(data);
                }
            } catch {
                /* ignore refresh errors */
            }
        }, 60000);

        return () => clearInterval(interval);
    }, []);

    // Build lookup maps
    const predMap = new Map(predictions.map((p) => [p.fixture_id, p]));
    const vbMap = new Map(valueBets.map((vb) => [vb.fixture.id, vb]));

    const live = fixtures.filter(
        (f) => f.status === "live" || f.status === "halftime",
    );
    const scheduled = fixtures.filter((f) => f.status === "scheduled");
    const finished = fixtures
        .filter((f) => f.status === "finished")
        .sort(
            (a, b) =>
                new Date(b.kickoff).getTime() - new Date(a.kickoff).getTime(),
        );

    const leagues = [
        ...new Map(fixtures.map((f) => [f.league.id, f.league])).values(),
    ];
    const valueBetCount = scheduled.filter((f) => vbMap.has(f.id)).length;

    return (
        <div className="container-main py-10">
            {/* Page header with stats */}
            <div className="mb-8">
                <h1 className="text-display-md mb-2">Matcher</h1>
                <p className="text-gray-400 mb-6">
                    Live resultat, kommande matcher och AI-analys — allt på ett
                    ställe.
                </p>

                {/* Quick stats bar */}
                <div className="flex flex-wrap gap-3">
                    {live.length > 0 && (
                        <div className="badge-live">{live.length} live</div>
                    )}
                    <div className="badge bg-white/[0.04] text-gray-300 border-white/[0.06]">
                        {scheduled.length} kommande
                    </div>
                    {valueBetCount > 0 && (
                        <div className="badge-value">
                            {valueBetCount} value bets
                        </div>
                    )}
                    {predictions.length > 0 && (
                        <div className="badge bg-accent-blue/10 text-blue-400 border-blue-500/15">
                            <svg
                                className="w-3 h-3"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                                strokeWidth={2}
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3"
                                />
                            </svg>
                            {predictions.length} AI-prediktioner
                        </div>
                    )}
                    <div className="badge bg-white/[0.04] text-gray-400 border-white/[0.06]">
                        {leagues.length} ligor
                    </div>
                </div>
            </div>

            {/* LIVE section — prominent */}
            {live.length > 0 && (
                <Section
                    title="Live nu"
                    icon={
                        <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                    }
                >
                    {live.map((f) => (
                        <LiveMatchCard
                            key={f.id}
                            fixture={f}
                            prediction={predMap.get(f.id)}
                            valueBet={vbMap.get(f.id)}
                            liveState={getLiveState(f)}
                        />
                    ))}
                </Section>
            )}

            {/* Value Bets callout */}
            {valueBetCount > 0 && (
                <div className="mb-10 p-4 rounded-2xl border border-scorelock-500/10 bg-scorelock-500/[0.03]">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-scorelock-500/10 flex items-center justify-center">
                                <svg
                                    className="w-5 h-5 text-scorelock-400"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    strokeWidth={1.5}
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z"
                                    />
                                </svg>
                            </div>
                            <div>
                                <p className="text-sm font-semibold text-white">
                                    {valueBetCount} value bets identifierade
                                </p>
                                <p className="text-xs text-gray-400">
                                    AI-modellen hittar värde i kommande matcher
                                </p>
                            </div>
                        </div>
                        <Link
                            href="/value-bets"
                            className="btn-ghost text-scorelock-400 text-sm"
                        >
                            Alla value bets →
                        </Link>
                    </div>
                </div>
            )}

            {/* Scheduled / Upcoming */}
            <Section title="Kommande" icon={<span className="text-gray-500">📅</span>}>
                {scheduled.length > 0 ? (
                    scheduled.map((f) => (
                        <LiveMatchCard
                            key={f.id}
                            fixture={f}
                            prediction={predMap.get(f.id)}
                            valueBet={vbMap.get(f.id)}
                        />
                    ))
                ) : (
                    <EmptyState icon="📅" text="Inga kommande matcher just nu." />
                )}
            </Section>

            {/* Finished — recent results */}
            <Section
                title="Resultat"
                icon={<span className="text-gray-500">✅</span>}
            >
                {finished.length > 0 ? (
                    finished.slice(0, 20).map((f) => (
                        <LiveMatchCard
                            key={f.id}
                            fixture={f}
                            prediction={predMap.get(f.id)}
                            compact
                        />
                    ))
                ) : (
                    <EmptyState icon="⏱" text="Inga avslutade matcher." />
                )}
            </Section>
        </div>
    );
}

function Section({
    title,
    icon,
    children,
}: {
    title: string;
    icon?: React.ReactNode;
    children: React.ReactNode;
}) {
    return (
        <section className="mb-12">
            <div className="flex items-center gap-2.5 mb-5">
                {icon}
                <h2 className="text-display-sm">{title}</h2>
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {children}
            </div>
        </section>
    );
}

function EmptyState({ icon, text }: { icon: string; text: string }) {
    return (
        <div className="col-span-full card text-center py-12">
            <div className="w-12 h-12 rounded-2xl bg-white/[0.03] flex items-center justify-center text-2xl mx-auto mb-3">
                {icon}
            </div>
            <p className="text-gray-400 text-sm">{text}</p>
        </div>
    );
}

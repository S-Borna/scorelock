"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useLiveScores } from "@/lib/use-live-scores";
import type { Fixture } from "@/lib/types";

/**
 * Site-wide live-ticker — livescore-DNA:t i en tunn rad under headern.
 *
 * Pollar /fixtures/live var 45:e sekund (fångar matcher som GÅR live) och
 * lyssnar på WebSocket-flödet för score/minut i realtid däremellan.
 * Renderar null när inget är live — tar noll plats utanför matchfönster.
 */
export function LiveTicker() {
    const [live, setLive] = useState<Fixture[]>([]);
    const { getLiveState } = useLiveScores(live);

    useEffect(() => {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "";
        let cancelled = false;

        async function poll() {
            try {
                const res = await fetch(`${apiBase}/api/v1/fixtures/live`, {
                    signal: AbortSignal.timeout(6000),
                });
                if (res.ok && !cancelled) setLive(await res.json());
            } catch {
                /* behåll senaste kända — tickern får aldrig krascha sidan */
            }
        }

        poll();
        const id = setInterval(poll, 45_000);
        return () => {
            cancelled = true;
            clearInterval(id);
        };
    }, []);

    if (live.length === 0) return null;

    return (
        <div className="border-b border-red-500/15 bg-red-950/20 backdrop-blur-sm">
            <div className="container-main flex items-center gap-3 h-9 overflow-hidden">
                <span className="flex items-center gap-1.5 flex-shrink-0 text-[10px] font-bold uppercase tracking-[0.25em] text-red-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                    Live
                </span>
                <div className="flex gap-5 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                    {live.map((f) => {
                        const ls = getLiveState(f);
                        const hg = ls?.homeGoals ?? f.home_goals ?? 0;
                        const ag = ls?.awayGoals ?? f.away_goals ?? 0;
                        const min = ls?.minute;
                        return (
                            <Link
                                key={f.id}
                                href={`/matches/${f.id}`}
                                className="flex items-center gap-1.5 flex-shrink-0 text-xs font-mono tabular-nums text-gray-300 hover:text-white transition-colors"
                            >
                                <span className="truncate max-w-[72px]">{short(f.home_team.name)}</span>
                                <span className={"font-bold " + (ls?.goalJustScored ? "text-yellow-300 animate-score-pop" : "text-white")}>
                                    {hg}–{ag}
                                </span>
                                <span className="truncate max-w-[72px]">{short(f.away_team.name)}</span>
                                {min != null && (
                                    <span className="text-red-400">{min}′</span>
                                )}
                            </Link>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

function short(name: string): string {
    // Kompakt lagnamn för tickern: 'Manchester City FC' → 'Man City'-stil
    return name
        .replace(/ FC$| AFC$| CF$/i, "")
        .replace(/^AFC /i, "")
        .slice(0, 14);
}

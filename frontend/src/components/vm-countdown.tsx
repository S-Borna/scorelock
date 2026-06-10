"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Fixture } from "@/lib/types";

const SWEDEN_NAME = "Sweden";

type Parts = { days: number; hours: number; minutes: number; seconds: number };

function partsUntil(targetMs: number): Parts | null {
    const diff = targetMs - Date.now();
    if (diff <= 0) return null;
    const totalSeconds = Math.floor(diff / 1000);
    return {
        days: Math.floor(totalSeconds / 86400),
        hours: Math.floor((totalSeconds % 86400) / 3600),
        minutes: Math.floor((totalSeconds % 3600) / 60),
        seconds: totalSeconds % 60,
    };
}

/** Levande nedräkning till kickoff — D/T/M/S i mono med micro-labels. */
export function VMCountdown({ kickoff }: { kickoff: string }) {
    // undefined = ej hydrerad ännu (visa "--"), null = avspark passerad.
    const [parts, setParts] = useState<Parts | null | undefined>(undefined);

    useEffect(() => {
        const target = new Date(kickoff).getTime();
        const tick = () => setParts(partsUntil(target));
        const raf = requestAnimationFrame(tick);
        const id = setInterval(tick, 1000);
        return () => {
            cancelAnimationFrame(raf);
            clearInterval(id);
        };
    }, [kickoff]);

    if (parts === null) {
        return (
            <div className="font-mono text-sm font-semibold text-yellow-300 uppercase tracking-[0.2em]">
                Avspark — matchen är igång
            </div>
        );
    }

    return (
        <div className="flex items-start gap-2.5 sm:gap-3.5">
            <CountdownUnit value={parts?.days} label="Dagar" />
            <Separator />
            <CountdownUnit value={parts?.hours} label="Tim" />
            <Separator />
            <CountdownUnit value={parts?.minutes} label="Min" />
            <Separator />
            <CountdownUnit value={parts?.seconds} label="Sek" />
        </div>
    );
}

function CountdownUnit({
    value,
    label,
}: {
    value: number | undefined;
    label: string;
}) {
    return (
        <div className="flex flex-col items-center min-w-[2.5ch]">
            <span className="font-mono text-2xl md:text-3xl text-white tabular-nums leading-none">
                {value === undefined ? "--" : String(value).padStart(2, "0")}
            </span>
            <span className="mt-1.5 text-[9px] uppercase tracking-[0.25em] text-yellow-200/60 font-bold">
                {label}
            </span>
        </div>
    );
}

function Separator() {
    return (
        <span className="font-mono text-2xl md:text-3xl text-yellow-300/40 leading-none select-none">
            :
        </span>
    );
}

/** Hero-callout: nästa Sverige-match med live nedräkning + länk till matchsidan. */
export function CountdownCallout({ fixture }: { fixture: Fixture }) {
    const isSwedenHome = fixture.home_team.name === SWEDEN_NAME;
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
            <VMCountdown kickoff={fixture.kickoff} />
            <div className="flex items-center gap-4 text-sm text-blue-100">
                <span className="font-mono text-xs tabular-nums" suppressHydrationWarning>
                    {formatKickoffLong(fixture.kickoff)}
                </span>
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

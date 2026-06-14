"use client";

import { buildICS, downloadICS, type CalEvent } from "@/lib/calendar";

export interface CalMatch {
    id: number;
    title: string;
    kickoff: string;
}

/**
 * "Lägg till i kalender" — laddar ner en .ics med matcherna helt klient-sidigt
 * (ingen backend). Funkar i Apple Kalender, Google Calendar och Outlook.
 */
export function AddToCalendarButton({
    matches,
    calName = "ScoreLock",
    filename = "scorelock.ics",
    label = "Lägg till i kalender",
}: {
    matches: CalMatch[];
    calName?: string;
    filename?: string;
    label?: string;
}) {
    if (matches.length === 0) return null;

    function handle() {
        const events: CalEvent[] = matches.map((m) => ({
            uid: `scorelock-${m.id}@scorelock.saidborna.com`,
            title: m.title,
            start: m.kickoff,
            durationMinutes: 120,
            url: `https://scorelock.saidborna.com/matches/${m.id}`,
        }));
        downloadICS(filename, buildICS(events, calName));
    }

    return (
        <button
            type="button"
            onClick={handle}
            className="inline-flex items-center gap-2 rounded-lg border border-white/15 bg-white/[0.04] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-white/[0.08]"
        >
            <span aria-hidden>📅</span>
            {label}
        </button>
    );
}

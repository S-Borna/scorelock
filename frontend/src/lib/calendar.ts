import { parseUTC } from "@/lib/time";

export interface CalEvent {
    /** Stabil unik identifierare per match */
    uid: string;
    title: string;
    /** Naiv UTC-ISO från API:t (tolkas som UTC via parseUTC) */
    start: string;
    durationMinutes: number;
    description?: string;
    url?: string;
}

function pad(n: number): string {
    return String(n).padStart(2, "0");
}

/** Date → iCalendar UTC-stämpel (YYYYMMDDTHHMMSSZ). */
function icsStamp(d: Date): string {
    return (
        `${d.getUTCFullYear()}${pad(d.getUTCMonth() + 1)}${pad(d.getUTCDate())}` +
        `T${pad(d.getUTCHours())}${pad(d.getUTCMinutes())}${pad(d.getUTCSeconds())}Z`
    );
}

function escapeICS(s: string): string {
    return s
        .replace(/\\/g, "\\\\")
        .replace(/;/g, "\\;")
        .replace(/,/g, "\\,")
        .replace(/\n/g, "\\n");
}

/** Bygg ett RFC 5545 VCALENDAR-dokument från matchhändelser. */
export function buildICS(events: CalEvent[], calName = "ScoreLock"): string {
    const lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//ScoreLock//VM 2026//SV",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        `X-WR-CALNAME:${escapeICS(calName)}`,
    ];
    for (const e of events) {
        const start = parseUTC(e.start);
        const end = new Date(start.getTime() + e.durationMinutes * 60_000);
        lines.push(
            "BEGIN:VEVENT",
            `UID:${e.uid}`,
            `DTSTAMP:${icsStamp(start)}`,
            `DTSTART:${icsStamp(start)}`,
            `DTEND:${icsStamp(end)}`,
            `SUMMARY:${escapeICS(e.title)}`,
        );
        if (e.description) lines.push(`DESCRIPTION:${escapeICS(e.description)}`);
        if (e.url) lines.push(`URL:${escapeICS(e.url)}`);
        lines.push("END:VEVENT");
    }
    lines.push("END:VCALENDAR");
    return lines.join("\r\n");
}

/** Trigga nedladdning av en .ics-fil i webbläsaren. */
export function downloadICS(filename: string, ics: string): void {
    const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

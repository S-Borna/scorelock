/**
 * Tidshantering — EN sanning för hela appen.
 *
 * Backend lagrar kickoff som NAIV UTC ("2026-06-15T02:00:00", inget suffix).
 * JS-spec: datetime utan offset tolkas som LOKAL tid → servern (UTC) och
 * klienten (CEST) parsar OLIKA tidpunkter → fel tider + hydration-mismatch.
 *
 * Regel: parsa ALLTID via parseUTC, formatera ALLTID med Europe/Stockholm.
 * Då visar server och klient identiska, korrekta svenska tider.
 */

const TZ = "Europe/Stockholm";
const HAS_OFFSET = /Z|[+-]\d{2}:?\d{2}$/;

/** Tolka backend-tid som UTC oavsett körmiljö. */
export function parseUTC(iso: string): Date {
    return new Date(HAS_OFFSET.test(iso) ? iso : iso + "Z");
}

/** "04:00" */
export function fmtTime(iso: string): string {
    return parseUTC(iso).toLocaleTimeString("sv-SE", {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: TZ,
    });
}

/** "mån 15 juni" */
export function fmtDay(iso: string): string {
    return parseUTC(iso).toLocaleDateString("sv-SE", {
        weekday: "short",
        day: "numeric",
        month: "long",
        timeZone: TZ,
    });
}

/** "15 juni" */
export function fmtDateShort(iso: string): string {
    return parseUTC(iso).toLocaleDateString("sv-SE", {
        day: "numeric",
        month: "long",
        timeZone: TZ,
    });
}

/** "mån 15 juni 04:00" — kompakt kickoff-rad. */
export function fmtKickoff(iso: string): string {
    return `${fmtDay(iso)} ${fmtTime(iso)}`;
}

/** "måndag 15 juni kl. 04:00" — lång form för hero/callouts. */
export function fmtKickoffLong(iso: string): string {
    const d = parseUTC(iso);
    const date = d.toLocaleDateString("sv-SE", {
        weekday: "long",
        day: "numeric",
        month: "long",
        timeZone: TZ,
    });
    return `${date} kl. ${fmtTime(iso)}`;
}

/** "tors 11 jun" — ultrakompakt för band/kort. */
export function fmtDayCompact(iso: string): string {
    return parseUTC(iso).toLocaleDateString("sv-SE", {
        weekday: "short",
        day: "numeric",
        month: "short",
        timeZone: TZ,
    });
}

/** Kalenderdag (YYYY-MM-DD) i svensk tid — för dygnsgruppering. */
export function stockholmDayKey(input: string | Date): string {
    const d = typeof input === "string" ? parseUTC(input) : input;
    return d.toLocaleDateString("sv-SE", { timeZone: TZ }); // "2026-06-15"
}

/** Är två tidpunkter samma svenska kalenderdag? */
export function sameStockholmDay(a: string | Date, b: string | Date): boolean {
    return stockholmDayKey(a) === stockholmDayKey(b);
}

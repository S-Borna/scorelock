"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import type { FixtureEvent } from "@/lib/types";

const LIVE_STATUSES = new Set([
    "live",
    "halftime",
    "in_play",
    "in_progress_extra_time",
    "in_progress_penalties",
]);

/**
 * Pollar matchens event-timeline var 30:e sekund medan matchen är live, så mål
 * och kort dyker upp utan sidladdning (Flashscores signaturupplevelse). Vilande
 * matcher gör inga anrop — SSR-eventsen räcker och ändras inte.
 */
export function useLiveEvents(
    fixtureId: number,
    initialEvents: FixtureEvent[],
    status: string,
): FixtureEvent[] {
    const [events, setEvents] = useState<FixtureEvent[]>(initialEvents);
    const isLive = LIVE_STATUSES.has(status);

    useEffect(() => {
        if (!isLive) return;
        let cancelled = false;

        async function poll() {
            try {
                const fresh = await fetchApi<FixtureEvent[]>(
                    `/api/v1/fixtures/${fixtureId}/events`,
                );
                if (!cancelled && Array.isArray(fresh)) setEvents(fresh);
            } catch {
                /* behåll senaste kända timeline vid tillfälligt fel */
            }
        }

        poll();
        const id = setInterval(poll, 30_000);
        return () => {
            cancelled = true;
            clearInterval(id);
        };
    }, [fixtureId, isLive]);

    return events;
}

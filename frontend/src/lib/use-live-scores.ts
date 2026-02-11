"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Fixture } from "./types";

/**
 * WebSocket message from the backend `/ws/live` endpoint.
 */
export interface LiveScoreUpdate {
    type: "score_update";
    fixture_id: number;
    home_goals: number;
    away_goals: number;
    status: string;
    minute: number | null;
}

/**
 * State for a single live fixture — tracked client-side.
 */
export interface LiveFixtureState {
    homeGoals: number;
    awayGoals: number;
    status: string;
    minute: number | null;
    /** Timestamp when we last received an update */
    lastUpdate: number;
    /** Did goals change on the last update? (triggers animation) */
    goalJustScored: boolean;
    /** Which side scored last? */
    goalSide: "home" | "away" | null;
}

const WS_URL =
    typeof window !== "undefined"
        ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${process.env.NEXT_PUBLIC_API_URL
            ? new URL(process.env.NEXT_PUBLIC_API_URL).host
            : window.location.host
        }/ws/live`
        : "";

/**
 * React hook for real-time live score updates via WebSocket.
 *
 * Connects to the backend WebSocket, manages reconnection,
 * and provides a map of fixture_id → LiveFixtureState.
 *
 * Also runs a client-side match clock that increments minute
 * every 60 seconds for live matches.
 */
export function useLiveScores(initialFixtures?: Fixture[]) {
    const [liveStates, setLiveStates] = useState<Map<number, LiveFixtureState>>(
        () => {
            const map = new Map<number, LiveFixtureState>();
            if (initialFixtures) {
                for (const f of initialFixtures) {
                    if (f.status === "live" || f.status === "halftime") {
                        map.set(f.id, {
                            homeGoals: f.home_goals ?? 0,
                            awayGoals: f.away_goals ?? 0,
                            status: f.status,
                            minute: null,
                            lastUpdate: Date.now(),
                            goalJustScored: false,
                            goalSide: null,
                        });
                    }
                }
            }
            return map;
        },
    );

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
    const clockTimer = useRef<ReturnType<typeof setInterval>>();
    const connectRef = useRef<(() => void) | null>(null);

    const connect = useCallback(() => {
        if (!WS_URL || typeof window === "undefined") return;

        try {
            const ws = new WebSocket(WS_URL);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log("[ScoreLock] Live WebSocket connected");
            };

            ws.onmessage = (event) => {
                try {
                    const data: LiveScoreUpdate = JSON.parse(event.data);
                    if (data.type !== "score_update") return;

                    setLiveStates((prev) => {
                        const next = new Map(prev);
                        const existing = next.get(data.fixture_id);

                        const prevHome = existing?.homeGoals ?? 0;
                        const prevAway = existing?.awayGoals ?? 0;
                        const homeScored = data.home_goals > prevHome;
                        const awayScored = data.away_goals > prevAway;

                        next.set(data.fixture_id, {
                            homeGoals: data.home_goals,
                            awayGoals: data.away_goals,
                            status: data.status,
                            minute: data.minute,
                            lastUpdate: Date.now(),
                            goalJustScored: homeScored || awayScored,
                            goalSide: homeScored ? "home" : awayScored ? "away" : null,
                        });

                        // Clear goal animation after 3 seconds
                        if (homeScored || awayScored) {
                            setTimeout(() => {
                                setLiveStates((p) => {
                                    const m = new Map(p);
                                    const s = m.get(data.fixture_id);
                                    if (s) {
                                        m.set(data.fixture_id, {
                                            ...s,
                                            goalJustScored: false,
                                            goalSide: null,
                                        });
                                    }
                                    return m;
                                });
                            }, 3000);
                        }

                        return next;
                    });
                } catch {
                    /* ignore malformed messages */
                }
            };

            ws.onclose = () => {
                console.log("[ScoreLock] WebSocket closed, reconnecting in 5s");
                reconnectTimer.current = setTimeout(() => connectRef.current?.(), 5000);
            };

            ws.onerror = () => {
                ws.close();
            };
        } catch {
            reconnectTimer.current = setTimeout(() => connectRef.current?.(), 5000);
        }
    }, []);

    useEffect(() => {
        connectRef.current = connect;
    }, [connect]);

    // Client-side match clock — increment minute every 60s for live matches
    useEffect(() => {
        clockTimer.current = setInterval(() => {
            setLiveStates((prev) => {
                let changed = false;
                const next = new Map(prev);
                for (const [id, state] of next) {
                    if (state.status === "live" && state.minute !== null) {
                        const elapsed = (Date.now() - state.lastUpdate) / 1000;
                        if (elapsed >= 60) {
                            next.set(id, {
                                ...state,
                                minute: state.minute + 1,
                            });
                            changed = true;
                        }
                    }
                }
                return changed ? next : prev;
            });
        }, 10000); // Check every 10 seconds

        return () => {
            if (clockTimer.current) clearInterval(clockTimer.current);
        };
    }, []);

    // Connect on mount
    useEffect(() => {
        connect();
        return () => {
            if (wsRef.current) wsRef.current.close();
            if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
        };
    }, [connect]);

    /**
     * Get the live state for a fixture, falling back to its static data.
     */
    const getLiveState = useCallback(
        (fixture: Fixture): LiveFixtureState | null => {
            return liveStates.get(fixture.id) ?? null;
        },
        [liveStates],
    );

    return { liveStates, getLiveState };
}

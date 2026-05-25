"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchApi } from "./api";

/** Ett chattmeddelande i matchrummet (matchar backend RoomMessageOut). */
export interface RoomMessage {
    id: number;
    fixture_id: number;
    user_id: number;
    author_name: string;
    body: string;
    created_at: string;
}

interface RoomState {
    messages: RoomMessage[];
    presence: number;
    reactions: Record<string, number>;
    /** True kort stund efter ett mål — för explosion-animation senare. */
    goalFlash: boolean;
    connected: boolean;
}

function wsRoomUrl(fixtureId: number): string {
    if (typeof window === "undefined") return "";
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = process.env.NEXT_PUBLIC_API_URL
        ? new URL(process.env.NEXT_PUBLIC_API_URL).host
        : window.location.host;
    return `${proto}//${host}/ws/room/${fixtureId}`;
}

/**
 * Hook för en matchs hangout-rum. Laddar historik, ansluter till
 * /ws/room/{fixtureId}, och håller närvaron vid liv via heartbeat.
 * Avsändning sker via REST i komponenten (POST /room/messages).
 */
export function useMatchRoom(fixtureId: number) {
    const [state, setState] = useState<RoomState>({
        messages: [],
        presence: 0,
        reactions: {},
        goalFlash: false,
        connected: false,
    });

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
    const heartbeat = useRef<ReturnType<typeof setInterval>>();
    const connectRef = useRef<(() => void) | null>(null);

    // Historik vid mount (nyast först från API → vänd till äldst först)
    useEffect(() => {
        let cancelled = false;
        fetchApi<RoomMessage[]>(`/api/v1/fixtures/${fixtureId}/room/messages?limit=50`)
            .then((rows) => {
                if (!cancelled) {
                    // Guard: misslyckad/CORS-blockad fetch ger non-array → [...rows] kraschar
                    const arr = Array.isArray(rows) ? rows : [];
                    setState((s) => ({ ...s, messages: [...arr].reverse() }));
                }
            })
            .catch(() => {
                /* tomt rum eller offline — börja blankt */
            });
        return () => {
            cancelled = true;
        };
    }, [fixtureId]);

    const connect = useCallback(() => {
        const url = wsRoomUrl(fixtureId);
        if (!url) return;

        try {
            const ws = new WebSocket(url);
            wsRef.current = ws;

            ws.onopen = () => {
                setState((s) => ({ ...s, connected: true }));
            };

            ws.onmessage = (event) => {
                let ev: Record<string, unknown>;
                try {
                    ev = JSON.parse(event.data);
                } catch {
                    return;
                }
                setState((s) => {
                    switch (ev.type) {
                        case "message":
                            return { ...s, messages: [...s.messages, ev as unknown as RoomMessage] };
                        case "presence":
                            return { ...s, presence: (ev.count as number) ?? s.presence };
                        case "reaction":
                            return { ...s, reactions: (ev.counts as Record<string, number>) ?? s.reactions };
                        case "delete":
                            return { ...s, messages: s.messages.filter((m) => m.id !== ev.message_id) };
                        case "goal":
                            return { ...s, goalFlash: true };
                        default:
                            return s;
                    }
                });
                if (ev.type === "goal") {
                    setTimeout(() => setState((s) => ({ ...s, goalFlash: false })), 3000);
                }
            };

            ws.onclose = () => {
                setState((s) => ({ ...s, connected: false }));
                reconnectTimer.current = setTimeout(() => connectRef.current?.(), 5000);
            };

            ws.onerror = () => ws.close();
        } catch {
            reconnectTimer.current = setTimeout(() => connectRef.current?.(), 5000);
        }
    }, [fixtureId]);

    useEffect(() => {
        connectRef.current = connect;
    }, [connect]);

    useEffect(() => {
        connect();
        // Heartbeat håller närvaron vid liv (backend förnyar presence vid recv)
        heartbeat.current = setInterval(() => {
            wsRef.current?.readyState === WebSocket.OPEN && wsRef.current.send("ping");
        }, 15000);
        return () => {
            wsRef.current?.close();
            if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
            if (heartbeat.current) clearInterval(heartbeat.current);
        };
    }, [connect]);

    return state;
}

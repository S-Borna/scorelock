"use client";

import { useState } from "react";
import { fetchApiAuth } from "@/lib/api";
import { getAccessToken } from "@/lib/auth-token";
import { useMatchRoom } from "@/lib/use-match-room";

const REACTIONS = ["🔥", "😱", "💚", "😤"];

/**
 * Matchrummet (hangout) — OSKINNAD funktionell prototyp. Design kommer sist;
 * detta verifierar bara att realtidsflödet funkar end-to-end i appen.
 */
export function MatchRoom({ fixtureId }: { fixtureId: number }) {
    const { messages, presence, reactions, goalFlash, connected } =
        useMatchRoom(fixtureId);
    const [draft, setDraft] = useState("");
    const [sending, setSending] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function send() {
        const token = getAccessToken();
        const body = draft.trim();
        if (!body) return;
        if (!token) {
            setError("Logga in för att skriva i rummet.");
            return;
        }
        setSending(true);
        setError(null);
        try {
            await fetchApiAuth(
                `/api/v1/fixtures/${fixtureId}/room/messages`,
                token,
                { method: "POST", body: JSON.stringify({ body }) },
            );
            setDraft("");
        } catch {
            setError("Kunde inte skicka. Försök igen.");
        } finally {
            setSending(false);
        }
    }

    async function react(emoji: string) {
        const token = getAccessToken();
        if (!token) {
            setError("Logga in för att reagera.");
            return;
        }
        try {
            await fetchApiAuth(
                `/api/v1/fixtures/${fixtureId}/room/reactions`,
                token,
                { method: "POST", body: JSON.stringify({ emoji }) },
            );
        } catch {
            /* tyst — reaktioner är best-effort */
        }
    }

    return (
        <section className="mt-6 rounded border p-4" aria-label="Matchrum">
            <div className="mb-3 flex items-center justify-between">
                <h2 className="font-bold">
                    Rummet {goalFlash && <span>⚽ MÅÅÅL!</span>}
                </h2>
                <span className="text-sm opacity-70">
                    {connected ? "🟢" : "⚪"} {presence} här nu
                </span>
            </div>

            <div className="mb-3 flex gap-2">
                {REACTIONS.map((e) => (
                    <button
                        key={e}
                        onClick={() => react(e)}
                        className="rounded border px-2 py-1 text-sm"
                    >
                        {e} {reactions[e] ?? 0}
                    </button>
                ))}
            </div>

            <ul className="mb-3 max-h-80 space-y-1 overflow-y-auto text-sm">
                {messages.length === 0 && (
                    <li className="opacity-50">Inga meddelanden än — var först.</li>
                )}
                {messages.map((m) => (
                    <li key={m.id}>
                        <span className="font-semibold">{m.author_name}:</span> {m.body}
                    </li>
                ))}
            </ul>

            <div className="flex gap-2">
                <input
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && send()}
                    placeholder="Skriv i rummet…"
                    maxLength={500}
                    className="flex-1 rounded border px-2 py-1 text-sm"
                />
                <button
                    onClick={send}
                    disabled={sending}
                    className="rounded border px-3 py-1 text-sm"
                >
                    Skicka
                </button>
            </div>
            {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
        </section>
    );
}

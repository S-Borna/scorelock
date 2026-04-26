"use client";

import { useEffect, useState } from "react";
import { useLocale } from "@/components/locale-provider";
import { getAccessToken } from "@/lib/auth-token";
import type { MOTMTally } from "@/lib/types";

const API_BASE =
    typeof window !== "undefined"
        ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        : "http://localhost:8000";

export function MOTMPoll({
    fixtureId,
    candidates,
    initialTally,
}: {
    fixtureId: number;
    candidates: { player_id: number; display_name: string; team_label: string }[];
    initialTally: MOTMTally;
}) {
    const { t } = useLocale();
    const [tally, setTally] = useState(initialTally);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const token = getAccessToken();
        if (!token) return;
        fetch(`${API_BASE}/api/v1/fixtures/${fixtureId}/motm-tally`, {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then((r) => (r.ok ? r.json() : null))
            .then((data) => {
                if (data) setTally(data as MOTMTally);
            })
            .catch(() => { /* ignore */ });
    }, [fixtureId]);

    async function vote(playerId: number) {
        setError(null);
        const token = getAccessToken();
        if (!token) {
            setError(t("motm.must_login"));
            return;
        }
        setLoading(true);
        try {
            const res = await fetch(
                `${API_BASE}/api/v1/fixtures/${fixtureId}/motm-vote`,
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ voted_player_id: playerId }),
                },
            );
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = (await res.json()) as MOTMTally;
            setTally(data);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Något gick fel");
        } finally {
            setLoading(false);
        }
    }

    const tallyById = new Map(tally.tally.map((e) => [e.player_id, e]));

    return (
        <div className="card">
            <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
                <div>
                    <h2 className="text-base font-semibold text-white">
                        🏆 {t("motm.title")}
                    </h2>
                    <p className="text-xs text-gray-500 mt-1">
                        {t("motm.subtitle")}
                    </p>
                </div>
                <span className="text-xs text-gray-400 font-mono">
                    {tally.total_votes} {t("motm.total_votes")}
                </span>
            </div>

            {error && (
                <p className="text-red-400 text-sm mb-3 bg-red-500/5 border border-red-500/10 rounded px-3 py-2">
                    {error}
                </p>
            )}

            {candidates.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">
                    {t("motm.empty")}
                </p>
            ) : (
                <ul className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
                    {candidates.map((c) => {
                        const t_entry = tallyById.get(c.player_id);
                        const pct = t_entry?.vote_share_percent ?? 0;
                        const isVoted = tally.user_voted_player_id === c.player_id;
                        return (
                            <li key={c.player_id}>
                                <button
                                    type="button"
                                    onClick={() => vote(c.player_id)}
                                    disabled={loading}
                                    className={
                                        "w-full text-left flex items-center gap-2 px-3 py-2 rounded transition-colors relative overflow-hidden " +
                                        (isVoted
                                            ? "bg-scorelock-500/15 border border-scorelock-500/30"
                                            : "bg-white/[0.03] hover:bg-white/[0.06] border border-transparent")
                                    }
                                >
                                    <div
                                        className="absolute inset-0 bg-scorelock-500/10"
                                        style={{ width: `${pct}%` }}
                                    />
                                    <span className="relative flex-1 text-sm text-white truncate">
                                        {c.display_name}
                                    </span>
                                    <span className="relative text-xs text-gray-500 font-mono">
                                        {c.team_label}
                                    </span>
                                    <span className="relative text-xs text-gray-300 font-mono w-10 text-right">
                                        {pct.toFixed(0)}%
                                    </span>
                                    {isVoted && (
                                        <span className="relative text-xs text-scorelock-400 ml-2 font-mono">
                                            ✓
                                        </span>
                                    )}
                                </button>
                            </li>
                        );
                    })}
                </ul>
            )}
        </div>
    );
}


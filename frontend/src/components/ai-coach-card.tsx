"use client";

import { useState } from "react";
import { useLocale } from "@/components/locale-provider";
import { getAccessToken } from "@/lib/auth-token";
import type {
    AIRecommendationKind,
    FantasyAIRecommendation,
    FantasyAIRecommendationsBundle,
} from "@/lib/types";

const KIND_LABEL_KEY: Record<AIRecommendationKind, string> = {
    transfer_in: "fantasy.coach.kind.transfer_in",
    transfer_out: "fantasy.coach.kind.transfer_out",
    captain: "fantasy.coach.kind.captain",
    formation: "fantasy.coach.kind.formation",
};

const KIND_COLOR: Record<AIRecommendationKind, string> = {
    transfer_in: "bg-green-500/20 text-green-300 border-green-500/30",
    transfer_out: "bg-red-500/20 text-red-300 border-red-500/30",
    captain: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
    formation: "bg-blue-500/20 text-blue-300 border-blue-500/30",
};

const API_BASE =
    typeof window !== "undefined"
        ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        : "http://localhost:8000";

function RecRow({ rec }: { rec: FantasyAIRecommendation }) {
    const { t } = useLocale();
    const expected = rec.payload?.expected_point_diff;
    return (
        <div className="border-b border-white/[0.06] last:border-0 pb-4 last:pb-0 mb-4 last:mb-0">
            <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                <span
                    className={
                        "text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border font-mono " +
                        KIND_COLOR[rec.kind]
                    }
                >
                    {t(KIND_LABEL_KEY[rec.kind])}
                </span>
                <div className="flex items-center gap-3 text-xs font-mono text-gray-400">
                    {expected !== null && expected !== undefined && (
                        <span>
                            {expected >= 0 ? "+" : ""}
                            {Number(expected).toFixed(1)}p
                        </span>
                    )}
                    {rec.confidence_score !== null && (
                        <span>
                            {Math.round(rec.confidence_score * 100)}%
                        </span>
                    )}
                </div>
            </div>
            <p className="text-sm text-gray-200 leading-relaxed">
                {rec.reasoning_text}
            </p>
        </div>
    );
}

export function AICoachCard({
    teamId,
    initialBundle,
}: {
    teamId: number;
    initialBundle: FantasyAIRecommendationsBundle;
}) {
    const { t } = useLocale();
    const [bundle, setBundle] = useState(initialBundle);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function refresh() {
        setError(null);
        const token = getAccessToken();
        if (!token) {
            setError("Logga in först");
            return;
        }
        setLoading(true);
        try {
            const res = await fetch(
                `${API_BASE}/api/v1/fantasy/teams/${teamId}/ai/recommendations?force=true`,
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                },
            );
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = (await res.json()) as FantasyAIRecommendationsBundle;
            setBundle(data);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Något gick fel");
        } finally {
            setLoading(false);
        }
    }

    const recs = bundle.recommendations;

    return (
        <div className="card">
            <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
                <div>
                    <h2 className="text-base font-semibold text-white">
                        🤖 {t("fantasy.coach.title")}
                    </h2>
                    <p className="text-xs text-gray-500 mt-1">
                        {t("fantasy.coach.subtitle")}
                    </p>
                </div>
                <button
                    type="button"
                    onClick={refresh}
                    disabled={loading}
                    className={
                        "text-xs px-3 py-1.5 rounded font-mono uppercase tracking-wider transition-colors " +
                        (loading
                            ? "bg-white/[0.04] text-gray-500"
                            : "bg-scorelock-500/20 text-scorelock-300 hover:bg-scorelock-500/30")
                    }
                >
                    {loading
                        ? t("fantasy.coach.refreshing")
                        : t("fantasy.coach.refresh")}
                </button>
            </div>

            {error && (
                <p className="text-red-400 text-sm mb-3 bg-red-500/5 border border-red-500/10 rounded px-3 py-2">
                    {error}
                </p>
            )}

            {recs.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-6">
                    {t("fantasy.coach.empty")}
                </p>
            ) : (
                <div>
                    {recs.map((rec) => (
                        <RecRow key={rec.id} rec={rec} />
                    ))}
                </div>
            )}

            {recs.length > 0 && (
                <p className="text-[10px] text-gray-600 mt-2 font-mono uppercase tracking-wider">
                    {bundle.cached
                        ? t("fantasy.coach.cached_label")
                        : t("fantasy.coach.live_label")}{" "}
                    · {recs[0].model_version}
                </p>
            )}
        </div>
    );
}

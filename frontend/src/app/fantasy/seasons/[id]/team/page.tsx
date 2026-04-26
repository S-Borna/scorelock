"use client";

import Link from "next/link";
import { useEffect, useState, use } from "react";
import { useLocale } from "@/components/locale-provider";
import { AICoachCard } from "@/components/ai-coach-card";
import { TeamPitchView } from "@/components/team-pitch-view";
import { getAccessToken } from "@/lib/auth-token";
import type { FantasyAIRecommendationsBundle, FantasyTeam } from "@/lib/types";

interface PageProps {
    params: Promise<{ id: string }>;
}

const API_BASE =
    typeof window !== "undefined"
        ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        : "http://localhost:8000";

export default function MyTeamPage({ params }: PageProps) {
    const { t } = useLocale();
    const { id } = use(params);
    const seasonId = Number(id);
    const [team, setTeam] = useState<FantasyTeam | null>(null);
    const [aiBundle, setAiBundle] = useState<FantasyAIRecommendationsBundle | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [authMissing, setAuthMissing] = useState(false);

    useEffect(() => {
        const token = getAccessToken();
        if (!token) {
            setAuthMissing(true);
            setLoading(false);
            return;
        }
        async function load() {
            try {
                const res = await fetch(
                    `${API_BASE}/api/v1/fantasy/teams/mine?season_id=${seasonId}`,
                    {
                        headers: { Authorization: `Bearer ${token}` },
                    },
                );
                if (res.status === 404) {
                    setTeam(null);
                    return;
                }
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}`);
                }
                const data = (await res.json()) as FantasyTeam;
                setTeam(data);
                try {
                    const aiRes = await fetch(
                        `${API_BASE}/api/v1/fantasy/teams/${data.id}/ai/recommendations`,
                    );
                    if (aiRes.ok) {
                        setAiBundle(await aiRes.json());
                    }
                } catch { /* ai not critical */ }
            } catch (e) {
                setError(
                    e instanceof Error ? e.message : "Kunde inte ladda lag",
                );
            } finally {
                setLoading(false);
            }
        }
        load();
    }, [seasonId]);

    if (loading) {
        return (
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                <div className="card text-center text-gray-500 py-12">…</div>
            </div>
        );
    }

    if (authMissing) {
        return (
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                <div className="card text-center py-12">
                    <p className="text-gray-300 mb-4">
                        {t("fantasy.team.must_login")}
                    </p>
                    <Link
                        href="/login"
                        className="inline-block px-4 py-2 bg-scorelock-500 text-black rounded font-semibold hover:bg-scorelock-400"
                    >
                        {t("fantasy.team.go_login")}
                    </Link>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                <div className="card text-red-400 text-center py-12">
                    {error}
                </div>
            </div>
        );
    }

    if (!team) {
        return (
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
                <div className="card text-center py-12">
                    <p className="text-gray-300 mb-4">
                        {t("fantasy.team.no_team")}
                    </p>
                    <Link
                        href={`/fantasy/seasons/${seasonId}/players`}
                        className="inline-block px-4 py-2 bg-scorelock-500 text-black rounded font-semibold hover:bg-scorelock-400"
                    >
                        {t("fantasy.team.market_link")}
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <nav className="text-sm text-gray-500 mb-6">
                <Link href="/fantasy" className="hover:text-gray-300">
                    Tipsligan
                </Link>
                <span className="mx-2">›</span>
                <Link
                    href={`/fantasy/seasons/${seasonId}`}
                    className="hover:text-gray-300"
                >
                    Säsong
                </Link>
                <span className="mx-2">›</span>
                <span>{team.name}</span>
            </nav>

            <header className="mb-6">
                <h1 className="text-2xl font-bold text-white mb-2">
                    {team.name}
                </h1>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <Stat
                        label={t("fantasy.team.total_points")}
                        value={team.total_points.toString()}
                    />
                    <Stat
                        label={t("fantasy.team.bank")}
                        value={`€${(team.bank_balance / 10).toFixed(1)}M`}
                    />
                    <Stat
                        label={t("fantasy.team.squad_value")}
                        value={`€${(team.squad_value / 10).toFixed(1)}M`}
                    />
                    <Stat
                        label={t("fantasy.team.free_transfers")}
                        value={team.free_transfers_available.toString()}
                    />
                </div>
            </header>

            <TeamPitchView team={team} />

            {aiBundle && (
                <div className="mt-6">
                    <AICoachCard teamId={team.id} initialBundle={aiBundle} />
                </div>
            )}

            <div className="mt-6 flex gap-3 flex-wrap">
                <Link
                    href={`/fantasy/seasons/${seasonId}/players`}
                    className="px-4 py-2 bg-white/[0.04] text-white rounded text-sm hover:bg-white/[0.08]"
                >
                    {t("fantasy.team.market_link")}
                </Link>
            </div>
        </div>
    );
}

function Stat({ label, value }: { label: string; value: string }) {
    return (
        <div className="card">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                {label}
            </div>
            <div className="text-lg font-mono text-white tabular-nums">
                {value}
            </div>
        </div>
    );
}

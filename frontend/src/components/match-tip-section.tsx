"use client";

import { TipForm } from "@/components/tip-form";
import { getAccessToken } from "@/lib/auth-token";
import type { Fixture } from "@/lib/types";
import { useState } from "react";

interface MatchTipSectionProps {
    fixture: Fixture;
}

export function MatchTipSection({ fixture }: MatchTipSectionProps) {
    const [error, setError] = useState<string | null>(null);

    const canTip = fixture.status === "scheduled" && new Date(fixture.kickoff) > new Date();

    if (!canTip) return null;

    async function handleSubmit(tip: {
        fixture_id: number;
        predicted_outcome: string;
        predicted_home_goals: number | null;
        predicted_away_goals: number | null;
    }) {
        setError(null);
        const token = getAccessToken();

        if (!token) {
            setError("Du måste vara inloggad för att tippa. Logga in först!");
            return;
        }

        try {
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/tips`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify(tip),
                }
            );

            if (!res.ok) {
                const data = await res.json().catch(() => null);
                throw new Error(data?.detail || "Kunde inte spara tips");
            }
        } catch (e) {
            setError(e instanceof Error ? e.message : "Något gick fel");
        }
    }

    return (
        <div className="card-glow">
            <h3 className="text-lg font-semibold mb-2">🎯 Tippa matchen</h3>
            <p className="text-xs text-gray-500 mb-3">
                Tippa rätt och klättra på topplistan!
            </p>
            <TipForm fixture={fixture} onSubmit={handleSubmit} />
            {error && (
                <p className="text-red-400 text-sm mt-3 bg-red-500/5 border border-red-500/10 rounded-lg px-3 py-2">{error}</p>
            )}
        </div>
    );
}

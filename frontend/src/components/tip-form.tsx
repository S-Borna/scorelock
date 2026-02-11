"use client";

import { useState } from "react";
import type { Fixture } from "@/lib/types";

interface TipFormProps {
    fixture: Fixture;
    existingTip?: { predicted_outcome: string; predicted_home_goals: number | null; predicted_away_goals: number | null };
    onSubmit: (tip: { fixture_id: number; predicted_outcome: string; predicted_home_goals: number | null; predicted_away_goals: number | null }) => void;
}

const outcomes = [
    { value: "H", label: "Hemma", emoji: "🏠" },
    { value: "D", label: "Oavgjort", emoji: "🤝" },
    { value: "A", label: "Borta", emoji: "✈️" },
] as const;

export function TipForm({ fixture, existingTip, onSubmit }: TipFormProps) {
    const [selected, setSelected] = useState<string | null>(existingTip?.predicted_outcome ?? null);
    const [homeGoals, setHomeGoals] = useState<string>(existingTip?.predicted_home_goals?.toString() ?? "");
    const [awayGoals, setAwayGoals] = useState<string>(existingTip?.predicted_away_goals?.toString() ?? "");
    const [showExact, setShowExact] = useState(existingTip?.predicted_home_goals != null);
    const [submitting, setSubmitting] = useState(false);
    const [submitted, setSubmitted] = useState(false);

    const isScheduled = fixture.status === "scheduled";
    const kickoff = new Date(fixture.kickoff);
    const canTip = isScheduled && kickoff > new Date();

    async function handleSubmit() {
        if (!selected || !canTip) return;
        setSubmitting(true);
        try {
            onSubmit({
                fixture_id: fixture.id,
                predicted_outcome: selected,
                predicted_home_goals: showExact && homeGoals ? parseInt(homeGoals) : null,
                predicted_away_goals: showExact && awayGoals ? parseInt(awayGoals) : null,
            });
            setSubmitted(true);
            setTimeout(() => setSubmitted(false), 2000);
        } finally {
            setSubmitting(false);
        }
    }

    if (!canTip) {
        return (
            <div className="text-xs text-gray-600 italic mt-2">
                {isScheduled ? "Matchen börjar snart — tips stängt" : "Matchen har redan börjat"}
            </div>
        );
    }

    return (
        <div className="mt-3 space-y-3">
            {/* Outcome buttons */}
            <div className="flex gap-2">
                {outcomes.map((o) => (
                    <button
                        key={o.value}
                        onClick={() => setSelected(o.value)}
                        className={`flex-1 py-2.5 px-3 rounded-xl text-sm font-medium transition-all duration-200 ${selected === o.value
                                ? "bg-scorelock-600 text-white shadow-glow-sm ring-1 ring-scorelock-400/30"
                                : "bg-white/[0.04] text-gray-400 hover:bg-white/[0.07] border border-white/[0.06]"
                            }`}
                    >
                        {o.emoji} {o.label}
                    </button>
                ))}
            </div>

            {/* Exact score toggle */}
            <button
                onClick={() => setShowExact(!showExact)}
                className="text-xs text-scorelock-400 hover:text-scorelock-300 transition-colors"
            >
                {showExact ? "▼ Dölj exakt resultat" : "▶ Tippa exakt resultat (+3p)"}
            </button>

            {showExact && (
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 flex-1">
                        <span className="text-xs text-gray-500 truncate">{fixture.home_team.name}</span>
                        <input
                            type="number"
                            min="0"
                            max="15"
                            value={homeGoals}
                            onChange={(e) => setHomeGoals(e.target.value)}
                            className="w-12 bg-white/[0.03] border border-white/[0.08] rounded-lg text-center text-sm py-1.5 focus:border-scorelock-500/40 focus:ring-1 focus:ring-scorelock-500/20 focus:outline-none transition-all"
                            placeholder="0"
                        />
                    </div>
                    <span className="text-gray-600 font-bold">–</span>
                    <div className="flex items-center gap-2 flex-1">
                        <input
                            type="number"
                            min="0"
                            max="15"
                            value={awayGoals}
                            onChange={(e) => setAwayGoals(e.target.value)}
                            className="w-12 bg-white/[0.03] border border-white/[0.08] rounded-lg text-center text-sm py-1.5 focus:border-scorelock-500/40 focus:ring-1 focus:ring-scorelock-500/20 focus:outline-none transition-all"
                            placeholder="0"
                        />
                        <span className="text-xs text-gray-500 truncate">{fixture.away_team.name}</span>
                    </div>
                </div>
            )}

            {/* Submit */}
            <button
                onClick={handleSubmit}
                disabled={!selected || submitting}
                className={`w-full py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${submitted
                        ? "bg-scorelock-600 text-white shadow-glow-sm"
                        : selected
                            ? "btn-primary"
                            : "bg-white/[0.04] text-gray-600 cursor-not-allowed border border-white/[0.04]"
                    }`}
            >
                {submitted ? "✓ Tips sparat!" : submitting ? "Sparar..." : existingTip ? "Uppdatera tips" : "Skicka tips"}
            </button>

            {/* Points info */}
            <p className="text-xs text-gray-600 text-center">
                1p rätt utgång · 3p exakt resultat
            </p>
        </div>
    );
}

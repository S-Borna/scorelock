import { MatchesClient } from "@/components/matches-client";
import { fetchApi } from "@/lib/api";
import type { Fixture, Prediction, ValueBet } from "@/lib/types";
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Matcher — Livescore & AI Predictions",
    description: "Live resultat, kommande matcher med AI-prediktioner och value bets markerade inline.",
};

export const revalidate = 60;

export default async function MatchesPage() {
    let fixtures: Fixture[] = [];
    let predictions: Prediction[] = [];
    let valueBets: ValueBet[] = [];

    const [fixturesRes, predictionsRes, valueBetsRes] = await Promise.allSettled([
        fetchApi<Fixture[]>("/api/v1/fixtures"),
        fetchApi<Prediction[]>("/api/v1/predictions/today"),
        fetchApi<ValueBet[]>("/api/v1/value-bets?min_edge=3"),
    ]);

    // Fixtures är kärndatan: kasta vid fel så Next behåller senaste lyckade ISR-
    // version i stället för att cacha en tom matchlista 60s för alla besökare.
    // Predictions/value-bets är overlays — degradera tyst om de fallerar.
    if (fixturesRes.status === "rejected") throw fixturesRes.reason;
    fixtures = fixturesRes.value;
    if (predictionsRes.status === "fulfilled") predictions = predictionsRes.value;
    if (valueBetsRes.status === "fulfilled") valueBets = valueBetsRes.value;

    return (
        <MatchesClient
            initialFixtures={fixtures}
            predictions={predictions}
            valueBets={valueBets}
        />
    );
}

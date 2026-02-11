import { MatchCard } from "@/components/match-card";
import { fetchApi } from "@/lib/api";
import type { Fixture } from "@/lib/types";

export const revalidate = 60;

export default async function HomePage() {
    let fixtures: Fixture[] = [];
    let error: string | null = null;

    try {
        fixtures = await fetchApi<Fixture[]>("/api/v1/fixtures?status=scheduled");
    } catch (err) {
        error = "Could not load fixtures.";
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Hero */}
            <section className="text-center py-12">
                <h1 className="text-4xl sm:text-5xl font-bold mb-4">
                    AI-Powered{" "}
                    <span className="text-scorelock-400">Football Analytics</span>
                </h1>
                <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                    Match predictions, sentiment analysis, and value bet identification
                    powered by machine learning.
                </p>
            </section>

            {/* Upcoming Matches */}
            <section className="mt-8">
                <h2 className="text-2xl font-semibold mb-6">Upcoming Matches</h2>

                {error && (
                    <div className="card text-center text-gray-400 py-12">{error}</div>
                )}

                {!error && fixtures.length === 0 && (
                    <div className="card text-center text-gray-400 py-12">
                        No upcoming matches found. Check back later.
                    </div>
                )}

                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {fixtures.slice(0, 9).map((fixture) => (
                        <MatchCard key={fixture.id} fixture={fixture} />
                    ))}
                </div>
            </section>

            {/* Features */}
            <section className="mt-20 grid gap-6 md:grid-cols-3">
                <FeatureCard
                    icon="🤖"
                    title="ML Predictions"
                    description="XGBoost model trained on 7,600+ matches with calibrated probabilities."
                />
                <FeatureCard
                    icon="💰"
                    title="Value Bet Finder"
                    description="Identifies discrepancies between our model and bookmaker odds using Kelly Criterion."
                />
                <FeatureCard
                    icon="📊"
                    title="Sentiment Analysis"
                    description="LLM-powered analysis of news and social media for each team."
                />
            </section>
        </div>
    );
}

function FeatureCard({
    icon,
    title,
    description,
}: {
    icon: string;
    title: string;
    description: string;
}) {
    return (
        <div className="card hover:border-scorelock-800 transition-colors">
            <div className="text-3xl mb-3">{icon}</div>
            <h3 className="text-lg font-semibold mb-2">{title}</h3>
            <p className="text-gray-400 text-sm">{description}</p>
        </div>
    );
}

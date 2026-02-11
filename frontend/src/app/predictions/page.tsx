import { fetchApi } from "@/lib/api";
import type { Prediction } from "@/lib/types";
import { PredictionBar } from "@/components/prediction-bar";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Prediktioner",
    description: "AI-genererade matchprediktioner med kalibrerade sannolikheter för dagens matcher.",
};

export const revalidate = 120;

export default async function PredictionsPage() {
    let predictions: Prediction[] = [];

    try {
        predictions = await fetchApi<Prediction[]>("/api/v1/predictions/today");
    } catch {
        // Handled in UI
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <h1 className="text-3xl font-bold mb-2">🤖 Dagens prediktioner</h1>
            <p className="text-gray-500 mb-8">
                ML-genererade matchprediktioner med kalibrerade sannolikheter.
            </p>

            {predictions.length === 0 ? (
                <div className="card text-center text-gray-400 py-12">
                    Inga prediktioner för idag. Prediktioner genereras dagligen kl. 22:00 UTC
                    för morgondagens matcher.
                </div>
            ) : (
                <div className="grid gap-6 lg:grid-cols-2">
                    {predictions.map((pred) => (
                        <div key={pred.fixture_id} className="card">
                            <Link
                                href={`/matches/${pred.fixture_id}`}
                                className="text-sm text-scorelock-400 hover:underline mb-3 block"
                            >
                                Visa match →
                            </Link>
                            <PredictionBar prediction={pred} />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

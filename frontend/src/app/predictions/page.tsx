import { fetchApi } from "@/lib/api";
import type { Prediction } from "@/lib/types";
import { PredictionBar } from "@/components/prediction-bar";

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
            <h1 className="text-3xl font-bold mb-2">Today&apos;s Predictions</h1>
            <p className="text-gray-500 mb-8">
                ML-generated match predictions with calibrated probabilities.
            </p>

            {predictions.length === 0 ? (
                <div className="card text-center text-gray-400 py-12">
                    No predictions for today. Predictions are generated daily at 22:00 UTC
                    for the next day&apos;s matches.
                </div>
            ) : (
                <div className="grid gap-6 lg:grid-cols-2">
                    {predictions.map((pred) => (
                        <div key={pred.fixture_id} className="card">
                            <a
                                href={`/matches/${pred.fixture_id}`}
                                className="text-sm text-scorelock-400 hover:underline mb-3 block"
                            >
                                Match #{pred.fixture_id} →
                            </a>
                            <PredictionBar prediction={pred} />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

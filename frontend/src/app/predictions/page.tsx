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
        // 14-dagars fönster så VM-matcherna fångas även om idag är tom dag.
        predictions = await fetchApi<Prediction[]>("/api/v1/predictions/today?days_ahead=14");
    } catch {
        // Handled in UI
    }

    // Ärlighets-grind: modellens platta landslagsbaseline (conf < 0.2) visas
    // inte som "prognoser" — det vore pseudo-precision. Matchsidorna visar
    // marknadens bild + AI-analys för de matcherna i stället.
    predictions = predictions.filter((p) => p.confidence >= 0.2);

    return (
        <div className="container-main py-10">
            <h1 className="text-display-md mb-2">Prediktioner</h1>
            <p className="text-gray-400 mb-8">
                ML-genererade matchprediktioner för kommande 14 dagar — sannolikheter,
                konfidens, value-edge när odds finns.
            </p>

            {/* Transparens: varför VM-matcher saknas här */}
            <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] px-4 py-3 mb-8">
                <p className="text-sm text-gray-400 leading-snug">
                    <span className="font-semibold text-gray-200">Transparens:</span>{" "}
                    ScoreLocks ML-modell är tränad på klubbfotboll. VM-matcher visas
                    därför inte här som prognoser — på varje VM-matchsida hittar du i
                    stället marknadens implicita sannolikheter (riktiga odds från 40+
                    spelbolag) och AI-analysen. Hellre färre siffror som är sanna.
                </p>
            </div>

            {predictions.length === 0 ? (
                <div className="card text-center py-16">
                    <div className="w-16 h-16 rounded-2xl bg-white/[0.03] flex items-center justify-center text-3xl mx-auto mb-4">🤖</div>
                    <p className="text-gray-400 max-w-sm mx-auto">
                        Modellen har inga klubbmatcher med täckning i fönstret just nu.
                        Under VM: se matchsidornas AI-analys + marknadsbild.
                    </p>
                </div>
            ) : (
                <div className="grid gap-6 lg:grid-cols-2">
                    {predictions.map((pred) => (
                        <div key={pred.fixture_id} className="card">
                            <Link
                                href={`/matches/${pred.fixture_id}`}
                                className="text-sm text-scorelock-400 hover:text-scorelock-300 transition-colors mb-3 block"
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

import type { Metadata } from "next";
import { fetchApi } from "@/lib/api";
import type { FantasySeason } from "@/lib/types";
import { SeasonCard } from "@/components/season-card";

export const metadata: Metadata = {
    title: "Tipsligan — ScoreLock",
    description:
        "Sätt ihop ditt drömlag med spelare från Allsvenskan, Big-5 och CL. Få AI-coach-rekommendationer. Tävla mot vänner och AI:n.",
};

export default async function FantasyLanding() {
    let seasons: FantasySeason[] = [];
    try {
        seasons = await fetchApi<FantasySeason[]>(
            "/api/v1/fantasy/seasons?only_active=true",
        );
    } catch {
        seasons = [];
    }

    return (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <header className="mb-10">
                <h1 className="text-3xl font-bold text-white mb-2">Tipsligan</h1>
                <p className="text-gray-400 max-w-2xl">
                    Sätt ihop ditt drömlag, jämför mot AI:n, vinn mot vänner.
                </p>
            </header>

            {seasons.length === 0 ? (
                <div className="card text-center text-gray-400 py-12">
                    Inga aktiva säsonger ännu
                </div>
            ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {seasons.map((s) => (
                        <SeasonCard key={s.id} season={s} />
                    ))}
                </div>
            )}
        </div>
    );
}

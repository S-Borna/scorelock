import { fetchApi } from "@/lib/api";
import type { League, Standing } from "@/lib/types";
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Tabeller",
    description: "Ligatabeller för de 8 största europeiska ligorna med poäng, form och målskillnad.",
};

export const revalidate = 300;

export default async function StandingsPage() {
    let leagues: League[] = [];

    try {
        leagues = await fetchApi<League[]>("/api/v1/leagues");
    } catch {
        // Handled in UI
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <h1 className="text-3xl font-bold mb-8">🏆 Tabeller</h1>

            {leagues.length === 0 ? (
                <div className="card text-center text-gray-400 py-12">
                    Inga ligor tillgängliga.
                </div>
            ) : (
                <div className="space-y-8">
                    {leagues
                        .filter((l) => l.type === "league")
                        .map((league) => (
                            <LeagueTable key={league.id} league={league} />
                        ))}
                </div>
            )}
        </div>
    );
}

async function LeagueTable({ league }: { league: League }) {
    let standings: Standing[] = [];

    try {
        standings = await fetchApi<Standing[]>(`/api/v1/standings/${league.id}`);
    } catch {
        // No standings available
    }

    if (standings.length === 0) {
        return null;
    }

    return (
        <div className="card overflow-hidden p-0">
            <div className="px-6 py-4 border-b border-gray-800 flex items-center gap-3">
                {league.logo_url && (
                    <img src={league.logo_url} alt={league.name} className="w-6 h-6" />
                )}
                <h2 className="text-lg font-semibold">{league.name}</h2>
                <span className="text-sm text-gray-500">{league.country}</span>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="text-gray-500 border-b border-gray-800 text-xs uppercase">
                            <th className="px-4 py-3 text-left w-8">#</th>
                            <th className="px-4 py-3 text-left">Lag</th>
                            <th className="px-4 py-3 text-center">P</th>
                            <th className="px-4 py-3 text-center">W</th>
                            <th className="px-4 py-3 text-center">D</th>
                            <th className="px-4 py-3 text-center">L</th>
                            <th className="px-4 py-3 text-center">GF</th>
                            <th className="px-4 py-3 text-center">GA</th>
                            <th className="px-4 py-3 text-center">GD</th>
                            <th className="px-4 py-3 text-center font-semibold">P</th>
                            <th className="px-4 py-3 text-center">Form</th>
                        </tr>
                    </thead>
                    <tbody>
                        {standings.map((s, i) => (
                            <tr
                                key={s.team.id}
                                className={`border-b border-gray-800/50 hover:bg-gray-800/30 ${i < 4 ? "border-l-2 border-l-scorelock-600" : ""
                                    }`}
                            >
                                <td className="px-4 py-3 text-gray-500">{s.position}</td>
                                <td className="px-4 py-3">
                                    <div className="flex items-center gap-2">
                                        {s.team.logo_url && (
                                            <img
                                                src={s.team.logo_url}
                                                alt={s.team.name}
                                                className="w-5 h-5 object-contain"
                                            />
                                        )}
                                        <span className="font-medium">{s.team.name}</span>
                                    </div>
                                </td>
                                <td className="px-4 py-3 text-center text-gray-400">{s.played}</td>
                                <td className="px-4 py-3 text-center text-gray-400">{s.won}</td>
                                <td className="px-4 py-3 text-center text-gray-400">{s.drawn}</td>
                                <td className="px-4 py-3 text-center text-gray-400">{s.lost}</td>
                                <td className="px-4 py-3 text-center text-gray-400">{s.goals_for}</td>
                                <td className="px-4 py-3 text-center text-gray-400">{s.goals_against}</td>
                                <td className="px-4 py-3 text-center">
                                    <span className={s.goal_diff > 0 ? "text-green-400" : s.goal_diff < 0 ? "text-red-400" : "text-gray-400"}>
                                        {s.goal_diff > 0 ? "+" : ""}
                                        {s.goal_diff}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-center font-bold">{s.points}</td>
                                <td className="px-4 py-3 text-center">
                                    {s.form && <FormIndicator form={s.form} />}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function FormIndicator({ form }: { form: string }) {
    const colors: Record<string, string> = {
        W: "bg-green-500",
        D: "bg-gray-500",
        L: "bg-red-500",
    };

    return (
        <div className="flex gap-1 justify-center">
            {form.split("").slice(-5).map((r, i) => (
                <span
                    key={i}
                    className={`w-5 h-5 rounded-sm text-[10px] flex items-center justify-center font-bold ${colors[r] || "bg-gray-700"
                        }`}
                >
                    {r}
                </span>
            ))}
        </div>
    );
}

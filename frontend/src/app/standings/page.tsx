import { fetchApi } from "@/lib/api";
import type { League, Standing } from "@/lib/types";
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Tabeller",
    description: "Ligatabeller med poäng, form och målskillnad.",
};

export const revalidate = 300;

// League display order
const LEAGUE_ORDER: Record<string, number> = {
    "Premier League": 1,
    "premier_league": 1,
    "La Liga": 2,
    "la_liga": 2,
    "Serie A": 3,
    "serie_a": 3,
    "Bundesliga": 4,
    "bundesliga": 4,
    "Ligue 1": 5,
    "ligue_1": 5,
    "Allsvenskan": 6,
    "allsvenskan": 6,
    "Champions League": 10,
    "champions_league": 10,
    "Europa League": 11,
    "europa_league": 11,
    "Conference League": 12,
    "conference_league": 12,
};

export default async function StandingsPage() {
    let leagues: League[] = [];

    try {
        leagues = await fetchApi<League[]>("/api/v1/leagues");
    } catch {
        // Handled in UI
    }

    // Sort leagues by display order, filter out cups (no standings for CL etc.)
    const sortedLeagues = leagues
        .filter((l) => l.type !== "cup")
        .sort((a, b) => (LEAGUE_ORDER[a.name] ?? 99) - (LEAGUE_ORDER[b.name] ?? 99));

    return (
        <div className="max-w-4xl mx-auto px-4 py-6">
            <h1 className="text-2xl font-bold mb-6">Tabeller</h1>

            {sortedLeagues.length === 0 ? (
                <div className="text-center py-16 rounded-xl border border-white/[0.06] bg-white/[0.02]">
                    <div className="w-14 h-14 rounded-2xl bg-white/[0.03] flex items-center justify-center text-2xl mx-auto mb-3">🏆</div>
                    <p className="text-gray-500 text-sm">Inga ligor tillgängliga.</p>
                </div>
            ) : (
                <div className="space-y-6">
                    {sortedLeagues.map((league) => (
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

    if (standings.length === 0) return null;

    return (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
            {/* League header */}
            <div className="px-4 py-3 border-b border-white/[0.06] flex items-center gap-3 bg-white/[0.01]">
                {league.logo_url ? (
                    <img src={league.logo_url} alt="" className="w-6 h-6 object-contain" />
                ) : (
                    <div className="w-6 h-6 rounded bg-white/[0.06] flex items-center justify-center">
                        <span className="text-xs">🏆</span>
                    </div>
                )}
                <h2 className="font-semibold text-white">{league.name}</h2>
                <span className="text-xs text-gray-500">{league.country}</span>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="text-[11px] uppercase tracking-wider text-gray-500 border-b border-white/[0.06]">
                            <th className="pl-4 pr-2 py-2.5 text-left w-8">#</th>
                            <th className="px-2 py-2.5 text-left">Lag</th>
                            <th className="px-2 py-2.5 text-center w-8">S</th>
                            <th className="px-2 py-2.5 text-center w-8 hidden sm:table-cell">V</th>
                            <th className="px-2 py-2.5 text-center w-8 hidden sm:table-cell">O</th>
                            <th className="px-2 py-2.5 text-center w-8 hidden sm:table-cell">F</th>
                            <th className="px-2 py-2.5 text-center w-12 hidden md:table-cell">GM</th>
                            <th className="px-2 py-2.5 text-center w-12 hidden md:table-cell">IM</th>
                            <th className="px-2 py-2.5 text-center w-10">MS</th>
                            <th className="px-2 py-2.5 text-center w-10 font-semibold">P</th>
                            <th className="pr-4 pl-2 py-2.5 text-center hidden sm:table-cell">Form</th>
                        </tr>
                    </thead>
                    <tbody>
                        {standings.map((s, i) => {
                            // Zone coloring
                            let zoneClass = "";
                            if (i < 4) zoneClass = "border-l-2 border-l-green-500/60";
                            else if (i >= standings.length - 3) zoneClass = "border-l-2 border-l-red-500/60";

                            return (
                                <tr
                                    key={s.team.id}
                                    className={`border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors ${zoneClass}`}
                                >
                                    <td className="pl-4 pr-2 py-2 text-gray-500 text-xs">{s.position}</td>
                                    <td className="px-2 py-2">
                                        <div className="flex items-center gap-2">
                                            {s.team.logo_url ? (
                                                <img src={s.team.logo_url} alt="" className="w-4 h-4 object-contain flex-shrink-0" />
                                            ) : (
                                                <div className="w-4 h-4 rounded-full bg-white/[0.06] flex-shrink-0" />
                                            )}
                                            <span className="text-sm font-medium truncate max-w-[140px] sm:max-w-none">{s.team.name}</span>
                                        </div>
                                    </td>
                                    <td className="px-2 py-2 text-center text-gray-400 text-xs">{s.played}</td>
                                    <td className="px-2 py-2 text-center text-gray-400 text-xs hidden sm:table-cell">{s.won}</td>
                                    <td className="px-2 py-2 text-center text-gray-400 text-xs hidden sm:table-cell">{s.drawn}</td>
                                    <td className="px-2 py-2 text-center text-gray-400 text-xs hidden sm:table-cell">{s.lost}</td>
                                    <td className="px-2 py-2 text-center text-gray-400 text-xs hidden md:table-cell">{s.goals_for}</td>
                                    <td className="px-2 py-2 text-center text-gray-400 text-xs hidden md:table-cell">{s.goals_against}</td>
                                    <td className="px-2 py-2 text-center text-xs">
                                        <span className={s.goal_diff > 0 ? "text-green-400" : s.goal_diff < 0 ? "text-red-400" : "text-gray-500"}>
                                            {s.goal_diff > 0 ? "+" : ""}{s.goal_diff}
                                        </span>
                                    </td>
                                    <td className="px-2 py-2 text-center font-bold text-sm">{s.points}</td>
                                    <td className="pr-4 pl-2 py-2 hidden sm:table-cell">
                                        {s.form && <FormIndicator form={s.form} />}
                                    </td>
                                </tr>
                            );
                        })}
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
        <div className="flex gap-0.5 justify-center">
            {form.split("").slice(-5).map((r, i) => (
                <span
                    key={i}
                    className={`w-4 h-4 rounded-sm text-[9px] flex items-center justify-center font-bold ${colors[r] || "bg-gray-700"}`}
                >
                    {r}
                </span>
            ))}
        </div>
    );
}

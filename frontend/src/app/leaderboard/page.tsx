import { fetchApi } from "@/lib/api";
import type { LeaderboardEntry, WeeklyTopTipper } from "@/lib/types";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Tippningsligan — ScoreLock",
    description: "Tävla mot andra och mot AI:n. Se topplistan och veckans bästa tippare.",
};

export const revalidate = 60; // 1 min

export default async function LeaderboardPage() {
    let leaderboard: LeaderboardEntry[] = [];
    let weeklyTop: WeeklyTopTipper | null = null;

    try {
        leaderboard = await fetchApi<LeaderboardEntry[]>("/api/v1/leaderboard?limit=50");
    } catch { /* mock data will handle */ }

    try {
        weeklyTop = await fetchApi<WeeklyTopTipper | null>("/api/v1/tips/weekly-top");
    } catch { /* not critical */ }

    return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="flex items-center justify-between mb-2">
                <h1 className="text-3xl font-bold">🏆 Tippningsligan</h1>
                <Link
                    href="/leaderboard/ai-vs-me"
                    className="text-sm text-scorelock-400 hover:underline"
                >
                    🤖 AI vs Du →
                </Link>
            </div>
            <p className="text-gray-400 mb-8">
                Tippa rätt utgång (1p) eller exakt resultat (3p). Tävla mot andra — och mot AI:n.
            </p>

            {/* Weekly top tipper */}
            {weeklyTop && (
                <div className="card border-yellow-900/50 bg-yellow-950/20 mb-8">
                    <div className="flex items-center gap-3">
                        <span className="text-3xl">👑</span>
                        <div>
                            <p className="text-yellow-400 font-semibold">Veckans tippare</p>
                            <p className="text-lg font-bold">{weeklyTop.user_name || "Anonym"}</p>
                            <p className="text-sm text-gray-400">
                                {weeklyTop.points_this_week}p på {weeklyTop.tips_this_week} tips · {weeklyTop.accuracy_this_week}% rätt
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Leaderboard table */}
            {leaderboard.length > 0 ? (
                <div className="card overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="text-gray-500 border-b border-gray-800">
                                    <th className="text-left py-3 px-4 w-12">#</th>
                                    <th className="text-left py-3 px-4">Spelare</th>
                                    <th className="text-center py-3 px-4">Poäng</th>
                                    <th className="text-center py-3 px-4">Tips</th>
                                    <th className="text-center py-3 px-4 hidden sm:table-cell">Rätt</th>
                                    <th className="text-center py-3 px-4 hidden sm:table-cell">Exakta</th>
                                    <th className="text-center py-3 px-4">Träff%</th>
                                </tr>
                            </thead>
                            <tbody>
                                {leaderboard.map((entry, i) => (
                                    <tr
                                        key={entry.user_id}
                                        className={`border-b border-gray-800/50 ${i < 3 ? "bg-gray-800/30" : ""}`}
                                    >
                                        <td className="py-3 px-4 font-bold text-gray-500">
                                            {i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : i + 1}
                                        </td>
                                        <td className="py-3 px-4 font-medium">
                                            {entry.user_name || "Anonym"}
                                        </td>
                                        <td className="py-3 px-4 text-center font-bold text-scorelock-400">
                                            {entry.total_points}
                                        </td>
                                        <td className="py-3 px-4 text-center text-gray-400">
                                            {entry.total_tips}
                                        </td>
                                        <td className="py-3 px-4 text-center text-gray-400 hidden sm:table-cell">
                                            {entry.correct_outcomes}
                                        </td>
                                        <td className="py-3 px-4 text-center text-green-400 hidden sm:table-cell">
                                            {entry.exact_scores}
                                        </td>
                                        <td className="py-3 px-4 text-center">
                                            <span className={entry.accuracy >= 50 ? "text-green-400" : "text-gray-400"}>
                                                {entry.accuracy}%
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            ) : (
                <div className="card text-center py-12">
                    <p className="text-4xl mb-4">⚽</p>
                    <p className="text-gray-400 text-lg mb-2">Inga tips ännu!</p>
                    <p className="text-gray-600 text-sm">
                        Gå till en matchsida och tippa utgången för att komma med på topplistan.
                    </p>
                </div>
            )}

            {/* How it works */}
            <div className="mt-8 card">
                <h2 className="text-lg font-semibold mb-4">📖 Så fungerar det</h2>
                <div className="grid sm:grid-cols-3 gap-4 text-sm text-gray-400">
                    <div>
                        <p className="text-scorelock-400 font-semibold mb-1">1. Tippa</p>
                        <p>Välj hemma, oavgjort eller borta på vilken match som helst innan avspark.</p>
                    </div>
                    <div>
                        <p className="text-scorelock-400 font-semibold mb-1">2. Poäng</p>
                        <p>1 poäng för rätt utgång. 3 poäng om du tippar exakt resultat — direkt i toppen!</p>
                    </div>
                    <div>
                        <p className="text-scorelock-400 font-semibold mb-1">3. Tävla</p>
                        <p>Se hur du ligger till mot andra tippare och mot vår AI-modell. Kan du slå maskinen?</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

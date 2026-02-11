import { fetchApi } from "@/lib/api";
import type { League, Sentiment, Team } from "@/lib/types";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Sentiment",
    description: "AI-driven sentimentanalys av nyheter och sociala medier för fotbollslag i Europas toppligor.",
};

export const revalidate = 300;

interface TeamWithSentiment {
    team: Team;
    sentiment: Sentiment | null;
}

export default async function SentimentPage() {
    let leagues: League[] = [];
    try {
        leagues = await fetchApi<League[]>("/api/v1/leagues");
    } catch {
        // handled in UI
    }

    // Fetch a pool of teams from standings, then get sentiment for each
    const leagueData: { league: League; teams: TeamWithSentiment[] }[] = [];

    for (const league of leagues.filter((l) => l.type === "league").slice(0, 4)) {
        try {
            const standings = await fetchApi<{ team: Team }[]>(`/api/v1/standings/${league.id}`);
            const teamsWithSentiment: TeamWithSentiment[] = [];

            // Fetch sentiment for top 6 teams from each league
            for (const s of standings.slice(0, 6)) {
                try {
                    const sentiments = await fetchApi<Sentiment[]>(`/api/v1/sentiment/${s.team.id}`);
                    teamsWithSentiment.push({
                        team: s.team,
                        sentiment: sentiments.length > 0 ? sentiments[0] : null,
                    });
                } catch {
                    teamsWithSentiment.push({ team: s.team, sentiment: null });
                }
            }

            leagueData.push({ league, teams: teamsWithSentiment });
        } catch {
            // skip league
        }
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <h1 className="text-3xl font-bold mb-2">💬 Sentimentanalys</h1>
            <p className="text-gray-500 mb-8">
                AI-driven analys av nyheter och sociala medier. Visar lagets buzz och stämning inför matcher.
            </p>

            {leagueData.length === 0 ? (
                <div className="card text-center text-gray-400 py-12">
                    Ingen sentimentdata tillgänglig just nu.
                </div>
            ) : (
                <div className="space-y-10">
                    {leagueData.map(({ league, teams }) => (
                        <section key={league.id}>
                            <div className="flex items-center gap-3 mb-4">
                                {league.logo_url && (
                                    <img src={league.logo_url} alt={league.name} className="w-6 h-6" />
                                )}
                                <h2 className="text-xl font-semibold">{league.name}</h2>
                            </div>

                            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                                {teams.map(({ team, sentiment }) => (
                                    <SentimentCard key={team.id} team={team} sentiment={sentiment} />
                                ))}
                            </div>
                        </section>
                    ))}
                </div>
            )}

            <div className="mt-10 card bg-gray-900/50">
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Så fungerar det</h3>
                <p className="text-sm text-gray-500">
                    Sentimentanalys drivs av AI som dagligen analyserar nyhetsartiklar och sociala medier
                    relaterade till varje lag. Poängen spänner från −1.0 (mycket negativt) till +1.0 (mycket positivt).
                    Buzz-poängen mäter volymen av omnämnanden.
                </p>
            </div>
        </div>
    );
}

function SentimentCard({ team, sentiment }: { team: Team; sentiment: Sentiment | null }) {
    const score = sentiment?.score ?? 0;
    const buzz = sentiment?.buzz_score ?? 0;
    const sentClass = score > 0.2 ? "text-green-400" : score < -0.2 ? "text-red-400" : "text-gray-400";
    const bgClass = score > 0.2 ? "bg-green-500" : score < -0.2 ? "bg-red-500" : "bg-gray-500";
    const label = score > 0.2 ? "Positivt" : score < -0.2 ? "Negativt" : "Neutralt";

    return (
        <div className="card hover:border-gray-700 transition-colors">
            <div className="flex items-center gap-3 mb-3">
                {team.logo_url ? (
                    <img src={team.logo_url} alt={team.name} className="w-8 h-8 object-contain" />
                ) : (
                    <div className="w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center text-sm">⚽</div>
                )}
                <div>
                    <span className="font-medium text-sm">{team.name}</span>
                    {sentiment && (
                        <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${bgClass}/20 ${sentClass}`}>
                            {label}
                        </span>
                    )}
                </div>
            </div>

            {sentiment ? (
                <div className="space-y-3">
                    <div>
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                            <span>Sentiment</span>
                            <span className={`font-mono font-semibold ${sentClass}`}>
                                {score > 0 ? "+" : ""}{score.toFixed(2)}
                            </span>
                        </div>
                        <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div
                                className={`h-full rounded-full transition-all ${bgClass}`}
                                style={{ width: `${((score + 1) / 2) * 100}%` }}
                            />
                        </div>
                    </div>

                    <div>
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                            <span>Buzz</span>
                            <span className="font-mono">{buzz.toFixed(1)}</span>
                        </div>
                        <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div
                                className="h-full rounded-full bg-scorelock-500 transition-all"
                                style={{ width: `${Math.min(buzz * 10, 100)}%` }}
                            />
                        </div>
                    </div>

                    {sentiment.summary && (
                        <p className="text-xs text-gray-500 line-clamp-2 mt-2">
                            {sentiment.summary}
                        </p>
                    )}

                    <div className="text-[10px] text-gray-600">
                        Uppdaterad: {new Date(sentiment.analyzed_at).toLocaleDateString("sv-SE")}
                    </div>
                </div>
            ) : (
                <p className="text-xs text-gray-600">Ingen sentimentdata tillgänglig.</p>
            )}
        </div>
    );
}

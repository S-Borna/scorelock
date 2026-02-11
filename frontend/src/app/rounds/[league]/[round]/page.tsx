import { fetchApi } from "@/lib/api";
import type { Fixture, Article, ArticleList } from "@/lib/types";
import { MatchCard } from "@/components/match-card";
import type { Metadata } from "next";
import Link from "next/link";

interface PageProps {
    params: Promise<{ league: string; round: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
    const { league, round } = await params;
    const decodedRound = decodeURIComponent(round);
    return {
        title: `Omgång ${decodedRound}`,
        description: `Alla matcher och AI-analys för omgång ${decodedRound} i liga ${league}.`,
    };
}

export const revalidate = 120;

export default async function RoundPage({ params }: PageProps) {
    const { league, round } = await params;
    const decodedRound = decodeURIComponent(round);

    // Fetch fixtures for this round
    let fixtures: Fixture[] = [];
    try {
        const allFixtures = await fetchApi<Fixture[]>(`/api/v1/fixtures?league_id=${league}`);
        fixtures = allFixtures.filter((f) => f.round === decodedRound);
    } catch {
        // handled in UI
    }

    // Fetch round summary article
    let roundArticle: Article | null = null;
    try {
        const res = await fetchApi<ArticleList>(
            `/api/v1/articles?article_type=ROUND_SUMMARY&limit=10`
        );
        roundArticle = res.articles.find(
            (a) => a.round === decodedRound && a.league_id === Number(league)
        ) ?? null;
    } catch {
        // not critical
    }

    const leagueName = fixtures.length > 0 ? fixtures[0].league.name : `Liga ${league}`;
    const finished = fixtures.filter((f) => f.status === "finished");
    const upcoming = fixtures.filter((f) => f.status !== "finished");

    return (
        <div className="container-main py-10">
            {/* Breadcrumbs */}
            <nav className="text-sm text-gray-500 mb-6">
                <Link href="/matches" className="hover:text-gray-300">Matcher</Link>
                <span className="mx-2">›</span>
                <Link href="/standings" className="hover:text-gray-300">{leagueName}</Link>
                <span className="mx-2">›</span>
                <span>Omgång {decodedRound}</span>
            </nav>

            <h1 className="text-display-md mb-2">
                📅 {leagueName} — Omgång {decodedRound}
            </h1>
            <p className="text-gray-400 mb-8">
                {fixtures.length} {fixtures.length === 1 ? "match" : "matcher"} i denna omgång.
            </p>

            {/* Round summary article */}
            {roundArticle && (
                <Link
                    href={`/articles/${roundArticle.slug}`}
                    className="card-interactive block mb-8 border-scorelock-500/15"
                >
                    <div className="flex items-center gap-2 mb-2">
                        <span className="badge bg-scorelock-500/10 text-scorelock-400 border-scorelock-500/20">
                            📰 AI-sammanfattning
                        </span>
                    </div>
                    <h2 className="text-lg font-semibold mb-1">{roundArticle.title}</h2>
                    {roundArticle.summary && (
                        <p className="text-sm text-gray-400 line-clamp-2">{roundArticle.summary}</p>
                    )}
                </Link>
            )}

            {fixtures.length === 0 ? (
                <div className="card text-center py-16">
                    <p className="text-gray-400">Inga matcher hittades för denna omgång.</p>
                </div>
            ) : (
                <div className="space-y-8">
                    {/* Upcoming */}
                    {upcoming.length > 0 && (
                        <section>
                            <h2 className="text-base font-semibold mb-5 text-gray-400">
                                ⏳ Kommande ({upcoming.length})
                            </h2>
                            <div className="grid gap-4 md:grid-cols-2">
                                {upcoming.map((f) => (
                                    <MatchCard key={f.id} fixture={f} />
                                ))}
                            </div>
                        </section>
                    )}

                    {/* Finished */}
                    {finished.length > 0 && (
                        <section>
                            <h2 className="text-base font-semibold mb-5 text-gray-400">
                                ✅ Avslutade ({finished.length})
                            </h2>
                            <div className="grid gap-4 md:grid-cols-2">
                                {finished.map((f) => (
                                    <MatchCard key={f.id} fixture={f} />
                                ))}
                            </div>
                        </section>
                    )}
                </div>
            )}
        </div>
    );
}

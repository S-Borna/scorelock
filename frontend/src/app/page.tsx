import { ArticleCard } from "@/components/article-card";
import { MatchCard } from "@/components/match-card";
import { fetchApi } from "@/lib/api";
import type { Article, ArticleList, Fixture, WeeklyTopTipper } from "@/lib/types";
import Link from "next/link";

export const revalidate = 60;

export default async function HomePage() {
    let articles: Article[] = [];
    let fixtures: Fixture[] = [];
    let weeklyTop: WeeklyTopTipper | null = null;

    const [articlesRes, fixturesRes, weeklyTopRes] = await Promise.allSettled([
        fetchApi<ArticleList>("/api/v1/articles?limit=9"),
        fetchApi<Fixture[]>("/api/v1/fixtures?status=scheduled"),
        fetchApi<WeeklyTopTipper | null>("/api/v1/tips/weekly-top"),
    ]);

    if (articlesRes.status === "fulfilled") articles = articlesRes.value.articles;
    if (fixturesRes.status === "fulfilled") fixtures = fixturesRes.value;
    if (weeklyTopRes.status === "fulfilled") weeklyTop = weeklyTopRes.value;

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Hero */}
            <section className="text-center py-8 sm:py-12">
                <h1 className="text-3xl sm:text-5xl font-bold mb-4">
                    AI-driven{" "}
                    <span className="text-scorelock-400">fotbollsanalys</span>
                </h1>
                <p className="text-gray-400 text-base sm:text-lg max-w-2xl mx-auto">
                    Förhandsanalyser, matchreferat och value bets — genererade av
                    maskininlärning och AI, på svenska.
                </p>
            </section>

            {/* Weekly top tipper */}
            {weeklyTop && (
                <section className="mt-6">
                    <Link href="/leaderboard" className="block card border-yellow-900/50 bg-yellow-950/20 hover:border-yellow-800/60 transition-colors">
                        <div className="flex items-center gap-3">
                            <span className="text-3xl">👑</span>
                            <div className="flex-1 min-w-0">
                                <p className="text-yellow-400 font-semibold text-sm">Veckans tippare</p>
                                <p className="text-lg font-bold truncate">{weeklyTop.user_name || "Anonym"}</p>
                            </div>
                            <div className="text-right text-sm text-gray-400">
                                <p className="text-scorelock-400 font-bold text-lg">{weeklyTop.points_this_week}p</p>
                                <p>{weeklyTop.tips_this_week} tips · {weeklyTop.accuracy_this_week}%</p>
                            </div>
                            <span className="text-gray-600 text-sm">→</span>
                        </div>
                    </Link>
                </section>
            )}

            {/* Article Feed */}
            <section className="mt-4">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-semibold">Senaste artiklarna</h2>
                    <div className="flex gap-2 text-sm">
                        <FilterLink label="Alla" type="" />
                        <FilterLink label="🔮 Analyser" type="MATCH_PREVIEW" />
                        <FilterLink label="📝 Referat" type="MATCH_REPORT" />
                        <FilterLink label="💰 Value Bets" type="VALUE_BET_ALERT" />
                    </div>
                </div>

                {articles.length === 0 ? (
                    <div className="card text-center py-12">
                        <p className="text-4xl mb-3">📝</p>
                        <p className="text-gray-400">
                            Inga artiklar publicerade ännu. Artiklar genereras automatiskt
                            inför och efter matcher.
                        </p>
                    </div>
                ) : (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {articles.map((article, i) => (
                            <ArticleCard
                                key={article.id}
                                article={article}
                                featured={i === 0}
                            />
                        ))}
                    </div>
                )}
            </section>

            {/* Upcoming Matches */}
            {fixtures.length > 0 && (
                <section className="mt-16">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-2xl font-semibold">Kommande matcher</h2>
                        <Link
                            href="/matches"
                            className="text-sm text-scorelock-400 hover:underline"
                        >
                            Visa alla →
                        </Link>
                    </div>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {fixtures.slice(0, 6).map((fixture) => (
                            <MatchCard key={fixture.id} fixture={fixture} />
                        ))}
                    </div>
                </section>
            )}

            {/* Features */}
            <section className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                <FeatureCard
                    icon="🤖"
                    title="ML-prediktioner"
                    description="XGBoost-modell tränad på 7 600+ matcher med kalibrerade sannolikheter."
                />
                <FeatureCard
                    icon="📝"
                    title="AI-artiklar"
                    description="Förhandsanalyser och matchreferat skrivna av AI på svenska — ScoreLocks USP."
                />
                <FeatureCard
                    icon="💰"
                    title="Value Bet Finder"
                    description="Identifierar avvikelser mellan modellens sannolikheter och bookmakerödds via Kelly Criterion."
                />
            </section>
        </div>
    );
}

function FilterLink({ label, type }: { label: string; type: string }) {
    return (
        <Link
            href={type ? `/?type=${type}` : "/"}
            className="hidden sm:inline-block text-gray-400 hover:text-white px-2 py-1 rounded transition-colors text-xs"
        >
            {label}
        </Link>
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

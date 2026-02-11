import { ArticleCard } from "@/components/article-card";
import { MatchCard } from "@/components/match-card";
import { fetchApi } from "@/lib/api";
import type { Article, ArticleList, Fixture, Prediction, ValueBet, WeeklyTopTipper } from "@/lib/types";
import Link from "next/link";

export const revalidate = 60;

export default async function HomePage() {
    let articles: Article[] = [];
    let fixtures: Fixture[] = [];
    let allFixtures: Fixture[] = [];
    let predictions: Prediction[] = [];
    let valueBets: ValueBet[] = [];
    let weeklyTop: WeeklyTopTipper | null = null;

    const [articlesRes, scheduledRes, allFixturesRes, predictionsRes, valueBetsRes, weeklyTopRes] = await Promise.allSettled([
        fetchApi<ArticleList>("/api/v1/articles?limit=9"),
        fetchApi<Fixture[]>("/api/v1/fixtures?status=scheduled"),
        fetchApi<Fixture[]>("/api/v1/fixtures"),
        fetchApi<Prediction[]>("/api/v1/predictions/today"),
        fetchApi<ValueBet[]>("/api/v1/value-bets?min_edge=3"),
        fetchApi<WeeklyTopTipper | null>("/api/v1/tips/weekly-top"),
    ]);

    if (articlesRes.status === "fulfilled") articles = articlesRes.value.articles;
    if (scheduledRes.status === "fulfilled") fixtures = scheduledRes.value;
    if (allFixturesRes.status === "fulfilled") allFixtures = allFixturesRes.value;
    if (predictionsRes.status === "fulfilled") predictions = predictionsRes.value;
    if (valueBetsRes.status === "fulfilled") valueBets = valueBetsRes.value;
    if (weeklyTopRes.status === "fulfilled") weeklyTop = weeklyTopRes.value;

    // Build lookup maps
    const predMap = new Map(predictions.map((p) => [p.fixture_id, p]));
    const vbMap = new Map(valueBets.map((vb) => [vb.fixture.id, vb]));

    // Live matches from all fixtures
    const liveFixtures = allFixtures.filter((f) => f.status === "live" || f.status === "halftime");

    return (
        <div>
            {/* Hero */}
            <section className="relative overflow-hidden border-b border-white/[0.04]">
                <div className="absolute inset-0 bg-gradient-mesh" />
                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-surface" />
                <div className="relative container-main py-16 sm:py-24 text-center">
                    <div className="inline-flex items-center gap-2 badge bg-scorelock-500/10 text-scorelock-400 border-scorelock-500/20 mb-6">
                        <span className="w-1.5 h-1.5 rounded-full bg-scorelock-500 animate-pulse" />
                        Driven av maskininlärning
                    </div>
                    <h1 className="text-display-lg sm:text-display-xl max-w-3xl mx-auto mb-5">
                        AI-driven{" "}
                        <span className="text-gradient">fotbollsanalys</span>
                    </h1>
                    <p className="text-gray-400 text-base sm:text-lg max-w-xl mx-auto leading-relaxed">
                        Livescore, prediktioner, value bets och matchanalyser —
                        driven av maskininlärning, på svenska.
                    </p>
                    <div className="flex items-center justify-center gap-3 mt-8">
                        <Link href="/matches" className="btn-primary">
                            Livescore & matcher
                        </Link>
                        <Link href="/value-bets" className="btn-secondary">
                            Value bets
                        </Link>
                    </div>
                </div>
            </section>

            <div className="container-main py-10">

                {/* LIVE MATCHES — always first when available */}
                {liveFixtures.length > 0 && (
                    <section className="mb-10 animate-fade-in">
                        <div className="section-header">
                            <div className="flex items-center gap-2.5">
                                <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                                <h2 className="section-title">Live nu</h2>
                                <span className="badge-live ml-1">{liveFixtures.length}</span>
                            </div>
                            <Link href="/matches" className="btn-ghost text-scorelock-400 text-sm">
                                Alla matcher →
                            </Link>
                        </div>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {liveFixtures.slice(0, 6).map((f) => (
                                <MatchCard
                                    key={f.id}
                                    fixture={f}
                                    prediction={predMap.get(f.id)}
                                    valueBet={vbMap.get(f.id)}
                                />
                            ))}
                        </div>
                    </section>
                )}

                {/* VALUE BETS CALLOUT — prominent if available */}
                {valueBets.length > 0 && (
                    <section className="mb-10 animate-fade-in">
                        <div className="p-5 rounded-2xl border border-scorelock-500/10 bg-scorelock-500/[0.03]">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-scorelock-500/10 flex items-center justify-center">
                                        <svg className="w-5 h-5 text-scorelock-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
                                        </svg>
                                    </div>
                                    <div>
                                        <h2 className="text-base font-semibold text-white">{valueBets.length} value bets idag</h2>
                                        <p className="text-xs text-gray-400">AI-identifierad edge mot oddsen</p>
                                    </div>
                                </div>
                                <Link href="/value-bets" className="btn-primary text-sm px-4 py-2">
                                    Se alla →
                                </Link>
                            </div>
                            {/* Quick preview of top 3 */}
                            <div className="grid gap-2 sm:grid-cols-3">
                                {valueBets.slice(0, 3).map((vb) => (
                                    <Link
                                        key={vb.fixture.id}
                                        href={`/matches/${vb.fixture.id}`}
                                        className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/[0.04] hover:border-scorelock-500/20 transition-all group"
                                    >
                                        <div className="min-w-0 flex-1">
                                            <p className="text-sm font-medium text-white truncate group-hover:text-scorelock-400 transition-colors">
                                                {vb.fixture.home_team.name} - {vb.fixture.away_team.name}
                                            </p>
                                            <p className="text-[10px] text-gray-500">{vb.suggested_bet === "Home" ? vb.fixture.home_team.name : vb.suggested_bet === "Away" ? vb.fixture.away_team.name : "Oavgjort"}</p>
                                        </div>
                                        <span className="badge-value text-[10px] px-1.5 py-0.5 ml-2">
                                            +{vb.edge_percent.toFixed(0)}%
                                        </span>
                                    </Link>
                                ))}
                            </div>
                        </div>
                    </section>
                )}

                {/* UPCOMING MATCHES — with predictions and value bets inline */}
                {fixtures.length > 0 && (
                    <section className="mb-12">
                        <div className="section-header">
                            <div>
                                <h2 className="section-title">Kommande matcher</h2>
                                <p className="section-subtitle">Med AI-prediktioner & value bets</p>
                            </div>
                            <Link href="/matches" className="btn-ghost text-scorelock-400 text-sm">
                                Alla matcher
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                                </svg>
                            </Link>
                        </div>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {fixtures.slice(0, 6).map((fixture) => (
                                <MatchCard
                                    key={fixture.id}
                                    fixture={fixture}
                                    prediction={predMap.get(fixture.id)}
                                    valueBet={vbMap.get(fixture.id)}
                                />
                            ))}
                        </div>
                    </section>
                )}

                {/* Weekly top tipper */}
                {weeklyTop && (
                    <section className="mb-10 animate-fade-in">
                        <Link href="/leaderboard" className="block card-interactive border-accent-amber/10 bg-gradient-to-r from-amber-950/20 via-surface-900/80 to-surface-900/80">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-xl bg-accent-amber/10 flex items-center justify-center text-2xl">
                                    👑
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-accent-amber font-semibold text-xs uppercase tracking-wider">Veckans tippare</p>
                                    <p className="text-lg font-bold truncate mt-0.5">{weeklyTop.user_name || "Anonym"}</p>
                                </div>
                                <div className="text-right">
                                    <p className="stat-value text-scorelock-400">{weeklyTop.points_this_week}p</p>
                                    <p className="text-xs text-gray-500 mt-0.5">{weeklyTop.tips_this_week} tips · {weeklyTop.accuracy_this_week}%</p>
                                </div>
                                <svg className="w-5 h-5 text-gray-600 hidden sm:block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                                </svg>
                            </div>
                        </Link>
                    </section>
                )}

                {/* ARTICLES — secondary, below matches */}
                <section>
                    <div className="section-header">
                        <div>
                            <h2 className="section-title">Senaste artiklarna</h2>
                            <p className="section-subtitle">AI-genererade analyser och matchreferat</p>
                        </div>
                        <div className="hidden sm:flex gap-1">
                            <FilterLink label="Alla" type="" />
                            <FilterLink label="Analyser" type="MATCH_PREVIEW" />
                            <FilterLink label="Referat" type="MATCH_REPORT" />
                            <FilterLink label="Value Bets" type="VALUE_BET_ALERT" />
                        </div>
                    </div>

                    {articles.length === 0 ? (
                        <div className="card text-center py-16">
                            <div className="w-16 h-16 rounded-2xl bg-white/[0.03] flex items-center justify-center text-3xl mx-auto mb-4">
                                📝
                            </div>
                            <p className="text-gray-400 max-w-sm mx-auto">
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

                {/* Features */}
                <section className="mt-20 mb-8">
                    <div className="text-center mb-10">
                        <h2 className="text-display-sm">Varför ScoreLock?</h2>
                        <p className="text-gray-400 mt-2 max-w-lg mx-auto">
                            Avancerad AI-analys möter användarvänlig design
                        </p>
                    </div>
                    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                        <FeatureCard
                            icon={<LiveIcon />}
                            title="Livescore & matcher"
                            description="Liveresultat, kommande matcher och historik — med AI-prediktioner och value bets markerade inline."
                        />
                        <FeatureCard
                            icon={<ModelIcon />}
                            title="ML-prediktioner"
                            description="XGBoost-modell tränad på 7 600+ matcher med kalibrerade sannolikheter för varje match."
                        />
                        <FeatureCard
                            icon={<ValueIcon />}
                            title="Value Bet Finder"
                            description="Identifierar edge mellan modellens sannolikheter och bookmakerödds med Kelly Criterion."
                        />
                    </div>
                </section>
            </div>
        </div>
    );
}

function FilterLink({ label, type }: { label: string; type: string }) {
    return (
        <Link
            href={type ? `/?type=${type}` : "/"}
            className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-400 hover:text-white hover:bg-white/[0.05] transition-all duration-150"
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
    icon: React.ReactNode;
    title: string;
    description: string;
}) {
    return (
        <div className="card-hover group">
            <div className="w-10 h-10 rounded-xl bg-scorelock-500/10 flex items-center justify-center mb-4 group-hover:bg-scorelock-500/15 transition-colors">
                {icon}
            </div>
            <h3 className="text-base font-semibold mb-2 text-white">{title}</h3>
            <p className="text-gray-400 text-sm leading-relaxed">{description}</p>
        </div>
    );
}

function LiveIcon() {
    return (
        <svg className="w-5 h-5 text-scorelock-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
        </svg>
    );
}

function ModelIcon() {
    return (
        <svg className="w-5 h-5 text-scorelock-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
        </svg>
    );
}

function ValueIcon() {
    return (
        <svg className="w-5 h-5 text-scorelock-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
        </svg>
    );
}

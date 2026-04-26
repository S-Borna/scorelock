import { PredictionBar } from "@/components/prediction-bar";
import { ArticleCard } from "@/components/article-card";
import { AffiliateCTA } from "@/components/affiliate-cta";
import type { AffiliateLink } from "@/components/affiliate-cta";
import { GamblingDisclaimer } from "@/components/gambling-disclaimer";
import { MatchTipSection } from "@/components/match-tip-section";
import { LiveMatchHeader, LiveMatchStats } from "@/components/live-match-header";
import { BroadcastCard } from "@/components/broadcast-card";
import { EventTimeline } from "@/components/event-timeline";
import { StatsPanel } from "@/components/stats-panel";
import { LineupsPitch } from "@/components/lineups-pitch";
import { fetchApi } from "@/lib/api";
import type { Article, ArticleList, Broadcast, FixtureDetail, FixtureEvent, FixtureLineupsBundle, FixtureStatisticsBundle, Sentiment } from "@/lib/types";
import { formatKickoff, getStatusClass } from "@/lib/utils";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Link from "next/link";

interface PageProps {
    params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
    const { id } = await params;
    try {
        const f = await fetchApi<FixtureDetail>(`/api/v1/fixtures/${id}`);
        return {
            title: `${f.home_team.name} vs ${f.away_team.name}`,
            description: `${f.league.name} — ML-prediktion, odds och analys för ${f.home_team.name} vs ${f.away_team.name}.`,
        };
    } catch {
        return { title: "Match" };
    }
}

export default async function MatchDetailPage({ params }: PageProps) {
    const { id } = await params;
    let fixture: FixtureDetail;

    try {
        fixture = await fetchApi<FixtureDetail>(`/api/v1/fixtures/${id}`);
    } catch {
        notFound();
    }

    // Fetch related articles for this fixture
    let articles: Article[] = [];
    try {
        const res = await fetchApi<ArticleList>(`/api/v1/articles?limit=5`);
        articles = res.articles.filter(
            (a) => a.fixture_id === fixture.id ||
                (a.tags && (a.tags.includes(fixture.home_team.name) || a.tags.includes(fixture.away_team.name)))
        ).slice(0, 3);
    } catch { /* not critical */ }

    // Fetch sentiment
    let homeSentiment: Sentiment[] = [];
    let awaySentiment: Sentiment[] = [];
    try {
        homeSentiment = await fetchApi<Sentiment[]>(`/api/v1/sentiment/${fixture.home_team.id}`);
    } catch { /* not critical */ }
    try {
        awaySentiment = await fetchApi<Sentiment[]>(`/api/v1/sentiment/${fixture.away_team.id}`);
    } catch { /* not critical */ }

    // Fetch affiliate links
    let affiliateLinks: AffiliateLink[] = [];
    try {
        affiliateLinks = await fetchApi<AffiliateLink[]>("/api/v1/affiliate/links?country=SE");
    } catch { /* not critical */ }

    // Fetch broadcasts (SE)
    let broadcasts: Broadcast[] = [];
    try {
        broadcasts = await fetchApi<Broadcast[]>(`/api/v1/fixtures/${fixture.id}/broadcasts?country=SE`);
    } catch { /* not critical */ }

    // Fetch events
    let events: FixtureEvent[] = [];
    try {
        events = await fetchApi<FixtureEvent[]>(`/api/v1/fixtures/${fixture.id}/events`);
    } catch { /* not critical */ }

    // Fetch statistics
    let statistics: FixtureStatisticsBundle = { home: null, away: null };
    try {
        statistics = await fetchApi<FixtureStatisticsBundle>(`/api/v1/fixtures/${fixture.id}/statistics`);
    } catch { /* not critical */ }

    // Fetch lineups
    let lineups: FixtureLineupsBundle = { home: null, away: null };
    try {
        lineups = await fetchApi<FixtureLineupsBundle>(`/api/v1/fixtures/${fixture.id}/lineups`);
    } catch { /* not critical */ }

    return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            {/* Breadcrumbs */}
            <nav className="text-sm text-gray-500 mb-8">
                <Link href="/matches" className="hover:text-gray-300">Matcher</Link>
                <span className="mx-2">›</span>
                <span>{fixture.home_team.name} vs {fixture.away_team.name}</span>
            </nav>

            {/* Match header card — live updating */}
            <LiveMatchHeader fixture={fixture} />

            <div className="grid gap-6 lg:grid-cols-3">
                <div className="lg:col-span-2 space-y-6">
                    {/* Live match stats (auto-refreshing) */}
                    <LiveMatchStats fixtureId={fixture.id} />
                    {/* Event timeline */}
                    <EventTimeline events={events} homeTeamId={fixture.home_team.id} />
                    {/* Lineups + pitch view */}
                    <LineupsPitch
                        lineups={lineups}
                        homeTeamName={fixture.home_team.name}
                        awayTeamName={fixture.away_team.name}
                    />
                    {/* Stats panel */}
                    <StatsPanel stats={statistics} />
                    {/* Prediction */}
                    {fixture.prediction && (
                        <div className="card">
                            <h2 className="text-base font-semibold mb-4 text-white">🤖 ML-prediktion</h2>
                            <PredictionBar prediction={fixture.prediction} />
                            <p className="text-xs text-gray-600 mt-3">
                                Modell: {fixture.prediction.model_version}
                            </p>
                        </div>
                    )}

                    {/* Odds */}
                    {fixture.odds.length > 0 && (
                        <div className="card">
                            <h2 className="text-base font-semibold mb-4 text-white">📊 Odds</h2>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="table-header">
                                            <th className="text-left py-2">Bookmaker</th>
                                            <th className="text-center py-2">Hemma</th>
                                            <th className="text-center py-2">Oavgjort</th>
                                            <th className="text-center py-2">Borta</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {fixture.odds
                                            .filter((o) => o.market === "1X2")
                                            .map((o, i) => (
                                                <tr key={i} className="table-row">
                                                    <td className="py-2">{o.bookmaker}</td>
                                                    <td className="text-center font-mono">{o.home_odds?.toFixed(2)}</td>
                                                    <td className="text-center font-mono">{o.draw_odds?.toFixed(2)}</td>
                                                    <td className="text-center font-mono">{o.away_odds?.toFixed(2)}</td>
                                                </tr>
                                            ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* Where to watch (SE) */}
                    <BroadcastCard broadcasts={broadcasts} />

                    {/* Related articles */}
                    {articles.length > 0 && (
                        <div>
                            <h2 className="text-base font-semibold mb-4 text-white">📝 Artiklar</h2>
                            <div className="space-y-4">
                                {articles.map((a) => (
                                    <ArticleCard key={a.id} article={a} />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Affiliate CTA after odds + articles */}
                    {affiliateLinks.length > 0 && (
                        <AffiliateCTA
                            links={affiliateLinks}
                            variant="banner"
                            fixtureId={fixture.id}
                            pageSource={`match-${fixture.id}`}
                        />
                    )}
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    {/* Tipping */}
                    <MatchTipSection fixture={fixture} />

                    {/* Sentiment */}
                    {(homeSentiment.length > 0 || awaySentiment.length > 0) && (
                        <div className="card">
                            <h3 className="text-lg font-semibold mb-4">💬 Sentiment</h3>
                            <SentimentRow team={fixture.home_team.name} scores={homeSentiment} />
                            <SentimentRow team={fixture.away_team.name} scores={awaySentiment} />
                        </div>
                    )}

                    {/* Quick links */}
                    <div className="card">
                        <h3 className="text-sm font-semibold text-gray-500 mb-3">Snabblänkar</h3>
                        <div className="space-y-2 text-sm">
                            <Link href="/value-bets" className="block text-scorelock-400 hover:underline">
                                💰 Value Bets
                            </Link>
                            <Link href="/standings" className="block text-scorelock-400 hover:underline">
                                🏆 Tabeller
                            </Link>
                            <Link href="/predictions" className="block text-scorelock-400 hover:underline">
                                🤖 Prediktioner
                            </Link>
                        </div>
                    </div>

                    {/* Gambling disclaimer */}
                    <GamblingDisclaimer compact />
                </div>
            </div>
        </div>
    );
}

function SentimentRow({ team, scores }: { team: string; scores: Sentiment[] }) {
    if (scores.length === 0) return null;
    const latest = scores[0];
    const sentimentClass = latest.score > 0.2 ? "sentiment-positive" : latest.score < -0.2 ? "sentiment-negative" : "sentiment-neutral";
    return (
        <div className="flex items-center justify-between py-2.5 border-b border-white/[0.06] last:border-0">
            <span className="text-sm">{team}</span>
            <div className="flex items-center gap-2">
                <span className={`text-sm font-mono font-semibold ${sentimentClass}`}>
                    {latest.score > 0 ? "+" : ""}{latest.score.toFixed(2)}
                </span>
                <div className="w-16 h-2 bg-white/[0.04] rounded-full overflow-hidden">
                    <div
                        className={`h-full rounded-full ${latest.score > 0.2 ? "bg-green-500" : latest.score < -0.2 ? "bg-red-500" : "bg-gray-500"}`}
                        style={{ width: `${((latest.score + 1) / 2) * 100}%` }}
                    />
                </div>
            </div>
        </div>
    );
}

import type { AffiliateLink } from "@/components/affiliate-cta";
import { GamblingDisclaimer } from "@/components/gambling-disclaimer";
import { MatchTipSection } from "@/components/match-tip-section";
import { LiveMatchHeader } from "@/components/live-match-header";
import { MatchInfoStrip } from "@/components/match-info-strip";
import { MatchRoom } from "@/components/match-room";
import { MatchTabs } from "@/components/match-tabs";
import { fetchApi, ApiError } from "@/lib/api";
import type { Article, Broadcast, CommentaryFeed, FixtureDetail, FixtureEvent, FixtureLineupsBundle, FixtureStatisticsBundle, MOTMTally, MatchInfo, MatchIntelligenceBundle, MomentumSeries, OddsSnapshotsBundle, Sentiment } from "@/lib/types";
import { formatKickoff, getStatusClass } from "@/lib/utils";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import Link from "next/link";

interface PageProps {
    params: Promise<{ id: string }>;
}

// Bundlat svar från /fixtures/{id}/detail — allt sidan behöver i ETT anrop.
interface FixtureDetailBundle {
    fixture: FixtureDetail;
    match_info: MatchInfo;
    broadcasts: Broadcast[];
    events: FixtureEvent[];
    statistics: FixtureStatisticsBundle;
    lineups: FixtureLineupsBundle;
    odds_snapshots: OddsSnapshotsBundle;
    commentary: CommentaryFeed;
    momentum: MomentumSeries;
    motm: MOTMTally;
    intelligence: MatchIntelligenceBundle;
    articles: Article[];
    home_sentiment: Sentiment[];
    away_sentiment: Sentiment[];
    affiliate_links: AffiliateLink[];
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
    // ETT bundlat anrop i stället för ~15 sekventiella fetch:ar (fan-out som drev
    // rate-limit-tryck + skörhet). Servern aggregerar allt in-process.
    let bundle: FixtureDetailBundle;
    try {
        bundle = await fetchApi<FixtureDetailBundle>(`/api/v1/fixtures/${id}/detail`);
    } catch (err) {
        // Bara genuin 404 (matchen finns inte) → not-found-sida. Transienta fel
        // (timeout/nätverk) ska INTE bli en cachad hård 404 — låt dem bubbla
        // till en retrybar error-boundary istället.
        if (err instanceof ApiError && err.status === 404) notFound();
        throw err;
    }

    const fixture = bundle.fixture;

    // Härda mot tunn/saknad data — garantera väldefinierade bundles så komponenterna
    // aldrig kraschar på .map/.length av undefined (sub-delar kan vara null/tomma).
    const events: FixtureEvent[] = Array.isArray(bundle.events) ? bundle.events : [];
    const broadcasts: Broadcast[] = Array.isArray(bundle.broadcasts) ? bundle.broadcasts : [];
    const affiliateLinks: AffiliateLink[] = Array.isArray(bundle.affiliate_links) ? bundle.affiliate_links : [];
    const homeSentiment: Sentiment[] = Array.isArray(bundle.home_sentiment) ? bundle.home_sentiment : [];
    const awaySentiment: Sentiment[] = Array.isArray(bundle.away_sentiment) ? bundle.away_sentiment : [];
    const articles: Article[] = Array.isArray(bundle.articles) ? bundle.articles : [];
    const statistics: FixtureStatisticsBundle = { home: bundle.statistics?.home ?? null, away: bundle.statistics?.away ?? null };
    const lineups: FixtureLineupsBundle = { home: bundle.lineups?.home ?? null, away: bundle.lineups?.away ?? null };
    const matchInfo: MatchInfo = { venue: bundle.match_info?.venue ?? null, referee: bundle.match_info?.referee ?? null };
    const oddsBundle: OddsSnapshotsBundle = {
        fixture_id: fixture.id,
        market_code: bundle.odds_snapshots?.market_code ?? "h2h",
        snapshots: Array.isArray(bundle.odds_snapshots?.snapshots) ? bundle.odds_snapshots.snapshots : [],
    };
    const commentary: CommentaryFeed = {
        fixture_id: fixture.id,
        entries: Array.isArray(bundle.commentary?.entries) ? bundle.commentary.entries : [],
    };
    const momentum: MomentumSeries = {
        fixture_id: fixture.id,
        points: Array.isArray(bundle.momentum?.points) ? bundle.momentum.points : [],
    };
    const motm: MOTMTally = {
        fixture_id: fixture.id,
        total_votes: bundle.motm?.total_votes ?? 0,
        user_voted_player_id: bundle.motm?.user_voted_player_id ?? null,
        tally: Array.isArray(bundle.motm?.tally) ? bundle.motm.tally : [],
    };
    const intelligence: MatchIntelligenceBundle =
        bundle.intelligence && typeof bundle.intelligence === "object"
            ? {
                  pre_match: bundle.intelligence.pre_match ?? null,
                  in_match: bundle.intelligence.in_match ?? null,
                  post_match: bundle.intelligence.post_match ?? null,
              }
            : { pre_match: null, in_match: null, post_match: null };

    const motmCandidates = [
        ...(lineups.home?.starters ?? []).map((p) => ({
            player_id: p.player_id,
            display_name: p.display_name,
            team_label: fixture.home_team.short_name ?? fixture.home_team.name.slice(0, 3).toUpperCase(),
        })),
        ...(lineups.away?.starters ?? []).map((p) => ({
            player_id: p.player_id,
            display_name: p.display_name,
            team_label: fixture.away_team.short_name ?? fixture.away_team.name.slice(0, 3).toUpperCase(),
        })),
    ];

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

            {/* Match info-rad: venue + referee */}
            <MatchInfoStrip info={matchInfo} />

            <div className="grid gap-6 lg:grid-cols-3">
                <div className="lg:col-span-2">
                    <MatchTabs
                        fixture={fixture}
                        intelligence={intelligence}
                        events={events}
                        lineups={lineups}
                        statistics={statistics}
                        oddsBundle={oddsBundle}
                        momentum={momentum}
                        commentary={commentary}
                        motm={motm}
                        motmCandidates={motmCandidates}
                        articles={articles}
                        affiliateLinks={affiliateLinks}
                        broadcasts={broadcasts}
                    />
                </div>

                {/* Sidebar */}
                <div className="space-y-6 stagger">
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

                    {/* Matchrum (hangout / Steg 4) — oskinnad funktionell prototyp */}
                    <MatchRoom fixtureId={fixture.id} />

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

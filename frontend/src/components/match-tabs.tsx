"use client";

import { useState } from "react";
import { PredictionBar } from "@/components/prediction-bar";
import { ArticleCard } from "@/components/article-card";
import { AffiliateCTA, type AffiliateLink } from "@/components/affiliate-cta";
import { LiveMatchStats } from "@/components/live-match-header";
import { BroadcastCard } from "@/components/broadcast-card";
import { EventTimeline } from "@/components/event-timeline";
import { StatsPanel } from "@/components/stats-panel";
import { LineupsPitch } from "@/components/lineups-pitch";
import { IntelligenceCard } from "@/components/intelligence-card";
import { MarketView } from "@/components/market-view";
import { OddsSparkline } from "@/components/odds-sparkline";
import { CommentaryFeedCard } from "@/components/commentary-feed";
import { MomentumGraph } from "@/components/momentum-graph";
import { MOTMPoll } from "@/components/motm-poll";
import { useLiveEvents } from "@/lib/use-live-events";
import type {
    Article, Broadcast, CommentaryFeed, FixtureDetail, FixtureEvent,
    FixtureLineupsBundle, FixtureStatisticsBundle, MOTMTally,
    MatchIntelligenceBundle, MomentumSeries, OddsSnapshotsBundle,
} from "@/lib/types";

interface MotmCandidate { player_id: number; display_name: string; team_label: string }

interface MatchTabsProps {
    fixture: FixtureDetail;
    intelligence: MatchIntelligenceBundle;
    events: FixtureEvent[];
    lineups: FixtureLineupsBundle;
    statistics: FixtureStatisticsBundle;
    oddsBundle: OddsSnapshotsBundle;
    momentum: MomentumSeries;
    commentary: CommentaryFeed;
    motm: MOTMTally;
    motmCandidates: MotmCandidate[];
    articles: Article[];
    affiliateLinks: AffiliateLink[];
    broadcasts: Broadcast[];
}

type TabKey = "oversikt" | "lineups" | "stats" | "odds";

const TABS: { key: TabKey; label: string; icon: string }[] = [
    { key: "oversikt", label: "Översikt", icon: "📊" },
    { key: "lineups", label: "Uppställningar", icon: "👥" },
    { key: "stats", label: "Statistik", icon: "📈" },
    { key: "odds", label: "Odds & TV", icon: "💰" },
];

/**
 * Tabbad match-detalj — klick + överskådligt i stället för en lång scroll.
 * key={tab} på innehållet → stagger-reveal re-firar vid varje flik-byte (finess).
 */
export function MatchTabs(props: MatchTabsProps) {
    const { fixture } = props;
    const [tab, setTab] = useState<TabKey>("oversikt");
    // Live-uppdaterad timeline: mål/kort dyker upp utan sidladdning under matchen.
    const liveEvents = useLiveEvents(fixture.id, props.events, fixture.status);

    return (
        <div>
            {/* Flik-bar — sticky så den följer med, klick i stället för scroll */}
            <div className="sticky top-2 z-10 mb-5 flex gap-1 bg-surface-900/80 backdrop-blur-md p-1 rounded-xl border border-white/[0.06]">
                {TABS.map((t) => (
                    <button
                        key={t.key}
                        onClick={() => setTab(t.key)}
                        className={`relative flex-1 flex items-center justify-center gap-1.5 px-2 py-2 rounded-lg text-sm font-medium transition-all ${tab === t.key ? "bg-white/[0.08] text-white shadow-sm" : "text-gray-400 hover:text-gray-200 hover:bg-white/[0.03]"}`}
                    >
                        <span>{t.icon}</span>
                        <span className="hidden sm:inline">{t.label}</span>
                        {/* Underline-indikator — glider in via scale/opacity på aktiv flik */}
                        <span
                            className={`pointer-events-none absolute inset-x-4 bottom-1 h-0.5 rounded-full bg-scorelock-400 transition-all duration-300 ease-out ${tab === t.key ? "opacity-100 scale-x-100" : "opacity-0 scale-x-50"}`}
                        />
                    </button>
                ))}
            </div>

            {/* key={tab} → remount → stagger-animationen spelar om vid varje byte */}
            <div key={tab} className="space-y-6 stagger">
                {tab === "oversikt" && (
                    <>
                        <LiveMatchStats fixtureId={fixture.id} />
                        {/* IntelligenceCard renderas nu som hero ovanför flikarna — */}
                        {/* visa inte här igen för att undvika dubblering. */}
                        {fixture.prediction && fixture.prediction.confidence >= 0.2 ? (
                            <div className="card-glow">
                                <h2 className="text-base font-semibold mb-4 text-white">🤖 ScoreLock AI — prediktion</h2>
                                <PredictionBar prediction={fixture.prediction} />
                                <p className="text-xs text-gray-600 mt-3">ScoreLock-modellen · uppdateras inför avspark</p>
                            </div>
                        ) : fixture.odds.length > 0 ? (
                            /* Ärlighets-grind: modellens platta landslagsbaseline döljs —
                               marknadens implicita sannolikheter (riktiga odds) visas i stället. */
                            <div className="card">
                                <h2 className="text-base font-semibold mb-4 text-white">📊 Marknadens bild</h2>
                                <MarketView odds={fixture.odds} />
                            </div>
                        ) : null}
                        <EventTimeline events={liveEvents} homeTeamId={fixture.home_team.id} />
                        <MomentumGraph series={props.momentum} />
                        <CommentaryFeedCard feed={props.commentary} locale="sv" />
                    </>
                )}

                {tab === "lineups" && (
                    <>
                        <LineupsPitch lineups={props.lineups} homeTeamName={fixture.home_team.name} awayTeamName={fixture.away_team.name} />
                        {props.motmCandidates.length > 0 && (
                            <MOTMPoll fixtureId={fixture.id} candidates={props.motmCandidates} initialTally={props.motm} />
                        )}
                    </>
                )}

                {tab === "stats" && (
                    <>
                        <StatsPanel stats={props.statistics} />
                        <OddsSparkline bundle={props.oddsBundle} />
                    </>
                )}

                {tab === "odds" && (
                    <>
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
                                            {fixture.odds.filter((o) => o.market === "1X2").map((o, i) => (
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
                        <BroadcastCard broadcasts={props.broadcasts} />
                        {props.articles.length > 0 && (
                            <div>
                                <h2 className="text-base font-semibold mb-4 text-white">📝 Artiklar</h2>
                                <div className="space-y-4">{props.articles.map((a) => <ArticleCard key={a.id} article={a} />)}</div>
                            </div>
                        )}
                        {props.affiliateLinks.length > 0 && (
                            <AffiliateCTA links={props.affiliateLinks} variant="banner" fixtureId={fixture.id} pageSource={`match-${fixture.id}`} />
                        )}
                    </>
                )}
            </div>
        </div>
    );
}

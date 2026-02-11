import { fetchApi } from "@/lib/api";
import type { ValueBet } from "@/lib/types";
import { formatKickoff, formatProb } from "@/lib/utils";
import type { Metadata } from "next";
import Link from "next/link";
import { AffiliateCTA } from "@/components/affiliate-cta";
import type { AffiliateLink } from "@/components/affiliate-cta";
import { GamblingDisclaimer } from "@/components/gambling-disclaimer";

export const metadata: Metadata = {
    title: "Value Bets",
    description: "AI-identifierade value bets med Kelly Criterion — spel där modellens sannolikhet överstiger oddsen.",
};

export const revalidate = 120;

export default async function ValueBetsPage() {
    let valueBets: ValueBet[] = [];
    let affiliateLinks: AffiliateLink[] = [];

    try {
        valueBets = await fetchApi<ValueBet[]>("/api/v1/value-bets?min_edge=3");
    } catch {
        // Handled in UI
    }
    try {
        affiliateLinks = await fetchApi<AffiliateLink[]>("/api/v1/affiliate/links?country=SE");
    } catch {
        // Not critical
    }

    return (
        <div className="container-main py-10">
            <h1 className="text-display-md mb-2">Value Bets</h1>
            <p className="text-gray-400 mb-8">
                Matcher där vår ML-modell identifierar värde gentemot bookmaker-oddsen.
            </p>

            {valueBets.length === 0 ? (
                <div className="card text-center py-16">
                    <div className="w-16 h-16 rounded-2xl bg-white/[0.03] flex items-center justify-center text-3xl mx-auto mb-4">💰</div>
                    <p className="text-gray-400 max-w-sm mx-auto">
                        Inga value bets identifierade just nu. Kolla tillbaka när nya odds finns tillgängliga.
                    </p>
                </div>
            ) : (
                <div className="grid gap-4 lg:grid-cols-2">
                    {valueBets.map((vb) => (
                        <div
                            key={vb.fixture.id}
                            className="card-hover border-scorelock-500/10"
                        >
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <Link
                                        href={`/matches/${vb.fixture.id}`}
                                        className="font-semibold hover:text-scorelock-400 transition-colors"
                                    >
                                        {vb.fixture.home_team.name} vs {vb.fixture.away_team.name}
                                    </Link>
                                    <p className="text-xs text-gray-500">
                                        {vb.fixture.league.name} · {formatKickoff(vb.fixture.kickoff)}
                                    </p>
                                </div>
                                <span className="badge-value">
                                    {vb.edge_percent.toFixed(1)}% edge
                                </span>
                            </div>

                            <div className="grid grid-cols-3 gap-4 text-sm">
                                <div>
                                    <span className="stat-label">Rekommenderat</span>
                                    <p className="font-semibold text-scorelock-400">{vb.suggested_bet}</p>
                                </div>
                                <div>
                                    <span className="stat-label">Kelly</span>
                                    <p className="font-mono">{(vb.kelly_fraction * 100).toFixed(1)}%</p>
                                </div>
                                <div>
                                    <span className="stat-label">Modell-sannolikhet</span>
                                    <p className="font-mono">
                                        {vb.suggested_bet === "Home"
                                            ? formatProb(vb.prediction.home_win_prob)
                                            : vb.suggested_bet === "Draw"
                                                ? formatProb(vb.prediction.draw_prob)
                                                : formatProb(vb.prediction.away_win_prob)}
                                    </p>
                                </div>
                            </div>

                            {/* Affiliate inline links */}
                            {affiliateLinks.length > 0 && (
                                <div className="mt-3 pt-3 border-t border-white/[0.04]">
                                    <AffiliateCTA
                                        links={affiliateLinks}
                                        fixtureId={vb.fixture.id}
                                        pageSource="value-bets"
                                        variant="inline"
                                    />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Affiliate banner */}
            {affiliateLinks.length > 0 && (
                <div className="mt-8">
                    <AffiliateCTA
                        links={affiliateLinks}
                        pageSource="value-bets"
                        variant="banner"
                    />
                </div>
            )}

            <div className="mt-6">
                <GamblingDisclaimer />
            </div>
        </div>
    );
}

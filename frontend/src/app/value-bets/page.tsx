import { fetchApi } from "@/lib/api";
import type { ValueBet } from "@/lib/types";
import { formatKickoff, formatProb } from "@/lib/utils";
import type { Metadata } from "next";
import Link from "next/link";
import { AffiliateCTA } from "@/components/affiliate-cta";
import type { AffiliateLink } from "@/components/affiliate-cta";
import { GamblingDisclaimer } from "@/components/gambling-disclaimer";

export const metadata: Metadata = {
    title: "Value Bets — AI Edge Finder",
    description: "AI-identifierade value bets med Kelly Criterion — matcher där modellens sannolikhet överstiger oddsen.",
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

    // Sort by edge descending
    const sorted = [...valueBets].sort((a, b) => b.edge_percent - a.edge_percent);
    const avgEdge = sorted.length > 0 ? sorted.reduce((sum, vb) => sum + vb.edge_percent, 0) / sorted.length : 0;
    const maxEdge = sorted.length > 0 ? sorted[0].edge_percent : 0;
    const leagues = [...new Set(sorted.map((vb) => vb.fixture.league.name))];

    return (
        <div className="container-main py-10">
            {/* Header */}
            <div className="mb-8">
                <div className="flex items-center gap-3 mb-2">
                    <div className="w-10 h-10 rounded-xl bg-scorelock-500/10 flex items-center justify-center">
                        <svg className="w-5 h-5 text-scorelock-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
                        </svg>
                    </div>
                    <h1 className="text-display-md">Value Bets</h1>
                </div>
                <p className="text-gray-400 max-w-2xl">
                    Matcher där vår ML-modell identifierar statistisk edge gentemot bookmaker-oddsen.
                    Sorterade efter högst edge — Kelly Criterion beräknar optimal insatsstorlek.
                </p>
            </div>

            {/* Transparens: VM-matcher filtreras bort server-side (konfidens-grind)
                  — klubbmodellens platta baseline producerar pseudo-edges som inte
                  är riktiga value-lägen. Hellre färre rader som betyder något. */}
            <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] px-4 py-3 mb-8">
                <p className="text-sm text-gray-400 leading-snug">
                    <span className="font-semibold text-gray-200">Transparens:</span>{" "}
                    VM-matcher visas inte här — vår ML-modell är tränad på klubbfotboll
                    och dess landslagssiffror håller inte vår ribba för ett value-läge.
                    Raderna nedan är klubbmatcher där modellen har riktig täckning.
                </p>
            </div>

            {/* Summary stats bar */}
            {sorted.length > 0 && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
                    <StatCard label="Aktiva bets" value={sorted.length.toString()} icon="📊" />
                    <StatCard label="Högst edge" value={`${maxEdge.toFixed(1)}%`} icon="🎯" accent />
                    <StatCard label="Snitt edge" value={`${avgEdge.toFixed(1)}%`} icon="📈" />
                    <StatCard label="Ligor" value={leagues.length.toString()} icon="🏆" />
                </div>
            )}

            {sorted.length === 0 ? (
                <div className="card text-center py-16">
                    <div className="w-16 h-16 rounded-2xl bg-white/[0.03] flex items-center justify-center text-3xl mx-auto mb-4">💰</div>
                    <h3 className="text-lg font-semibold mb-2">Inga value bets just nu</h3>
                    <p className="text-gray-400 max-w-sm mx-auto text-sm">
                        Modellen analyserar kontinuerligt — kolla tillbaka när nya odds och matcher finns tillgängliga.
                    </p>
                    <Link href="/matches" className="btn-secondary mt-6 inline-flex">
                        Se matcher istället
                    </Link>
                </div>
            ) : (
                <div className="space-y-4">
                    {sorted.map((vb) => (
                        <ValueBetCard
                            key={vb.fixture.id}
                            vb={vb}
                            affiliateLinks={affiliateLinks}
                        />
                    ))}
                </div>
            )}

            {/* Affiliate banner */}
            {affiliateLinks.length > 0 && (
                <div className="mt-10">
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

function StatCard({ label, value, icon, accent }: { label: string; value: string; icon: string; accent?: boolean }) {
    return (
        <div className={`card ${accent ? "border-scorelock-500/15 bg-scorelock-500/[0.03]" : ""}`}>
            <div className="flex items-center gap-3">
                <span className="text-lg">{icon}</span>
                <div>
                    <p className={`text-xl font-bold font-mono tabular-nums ${accent ? "text-scorelock-400" : "text-white"}`}>
                        {value}
                    </p>
                    <p className="stat-label">{label}</p>
                </div>
            </div>
        </div>
    );
}

function ValueBetCard({ vb, affiliateLinks }: { vb: ValueBet; affiliateLinks: AffiliateLink[] }) {
    const suggestedTeam = vb.suggested_bet === "Home"
        ? vb.fixture.home_team.name
        : vb.suggested_bet === "Away"
            ? vb.fixture.away_team.name
            : "Oavgjort";

    const modelProb = vb.suggested_bet === "Home"
        ? vb.prediction.home_win_prob
        : vb.suggested_bet === "Draw"
            ? vb.prediction.draw_prob
            : vb.prediction.away_win_prob;

    const impliedProb = modelProb - (vb.edge_percent / 100);

    return (
        <div className="card-hover border-scorelock-500/10 group">
            {/* Top row — match info + edge badge */}
            <div className="flex items-start justify-between mb-4">
                <div className="min-w-0">
                    <Link
                        href={`/matches/${vb.fixture.id}`}
                        className="text-base font-semibold text-white hover:text-scorelock-400 transition-colors inline-flex items-center gap-2"
                    >
                        <span className="truncate">
                            {vb.fixture.home_team.name} vs {vb.fixture.away_team.name}
                        </span>
                        <svg className="w-4 h-4 text-gray-600 group-hover:text-scorelock-400 transition-colors flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                        </svg>
                    </Link>
                    <p className="text-xs text-gray-500 mt-0.5 flex items-center gap-2">
                        {vb.fixture.league.logo_url && (
                            <img src={vb.fixture.league.logo_url} alt="" className="w-3.5 h-3.5 object-contain" />
                        )}
                        {vb.fixture.league.name} · {formatKickoff(vb.fixture.kickoff)}
                    </p>
                </div>
                <span className="badge-value text-sm px-3 py-1.5 font-semibold flex-shrink-0">
                    +{vb.edge_percent.toFixed(1)}% edge
                </span>
            </div>

            {/* Value bet details — 2 row layout */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
                <div>
                    <p className="stat-label">Rekommendation</p>
                    <p className="text-sm font-semibold text-scorelock-400 mt-0.5">{suggestedTeam}</p>
                </div>
                <div>
                    <p className="stat-label">Modell</p>
                    <p className="text-sm font-mono font-semibold text-white mt-0.5">{formatProb(modelProb)}</p>
                </div>
                <div>
                    <p className="stat-label">Implied odds</p>
                    <p className="text-sm font-mono text-gray-400 mt-0.5">{formatProb(Math.max(0, impliedProb))}</p>
                </div>
                <div>
                    <p className="stat-label">Kelly stake</p>
                    <p className="text-sm font-mono text-white mt-0.5">{(vb.kelly_fraction * 100).toFixed(1)}%</p>
                </div>
            </div>

            {/* Edge visualization bar */}
            <div className="mb-4">
                <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] uppercase tracking-wider text-gray-500">Edge visualisering</span>
                    <span className="text-[10px] text-gray-500">0% → 20%</span>
                </div>
                <div className="h-2 rounded-full bg-white/[0.04] overflow-hidden">
                    <div
                        className="h-full rounded-full bg-gradient-to-r from-scorelock-600 to-scorelock-400 transition-all duration-700"
                        style={{ width: `${Math.min(vb.edge_percent / 20 * 100, 100)}%` }}
                    />
                </div>
            </div>

            {/* Prediction bar */}
            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                <div className="flex items-center gap-1.5 mb-2">
                    <svg className="w-3 h-3 text-scorelock-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5" />
                    </svg>
                    <span className="text-[10px] font-medium uppercase tracking-wider text-gray-500">AI Prediktion</span>
                </div>
                <div className="prob-bar-track mb-1.5">
                    <div className="prob-bar bg-gradient-to-r from-scorelock-600 to-scorelock-500" style={{ width: `${(vb.prediction.home_win_prob * 100).toFixed(1)}%` }} />
                    <div className="prob-bar bg-gradient-to-r from-gray-500 to-gray-400" style={{ width: `${(vb.prediction.draw_prob * 100).toFixed(1)}%` }} />
                    <div className="prob-bar bg-gradient-to-r from-accent-blue to-blue-400" style={{ width: `${(vb.prediction.away_win_prob * 100).toFixed(1)}%` }} />
                </div>
                <div className="flex justify-between text-[10px] text-gray-500">
                    <span>Hemma {formatProb(vb.prediction.home_win_prob)}</span>
                    <span>Oavgjort {formatProb(vb.prediction.draw_prob)}</span>
                    <span>Borta {formatProb(vb.prediction.away_win_prob)}</span>
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
    );
}

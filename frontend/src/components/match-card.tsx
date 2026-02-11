import type { Fixture, Prediction, ValueBet } from "@/lib/types";
import { formatKickoff, formatProb, getStatusClass } from "@/lib/utils";

interface MatchCardProps {
    fixture: Fixture;
    prediction?: Prediction | null;
    valueBet?: ValueBet | null;
    compact?: boolean;
}

export function MatchCard({ fixture, prediction, valueBet, compact = false }: MatchCardProps) {
    const isLive = fixture.status === "live" || fixture.status === "halftime";
    const isFinished = fixture.status === "finished";
    const hasValue = valueBet && valueBet.edge_percent > 0;

    return (
        <a
            href={`/matches/${fixture.id}`}
            className={`card-interactive block group ${isLive ? "border-red-500/15 shadow-[0_0_20px_-5px_rgba(239,68,68,0.1)]" : ""} ${hasValue ? "border-scorelock-500/10" : ""}`}
        >
            {/* League & Status + Value badge */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2 min-w-0">
                    {fixture.league.logo_url && (
                        <img src={fixture.league.logo_url} alt="" className="w-4 h-4 object-contain flex-shrink-0" />
                    )}
                    <span className="text-xs text-gray-500 truncate">
                        {fixture.league.name}
                        {fixture.round && <span className="text-gray-600"> · {fixture.round}</span>}
                    </span>
                </div>
                <div className="flex items-center gap-1.5">
                    {hasValue && (
                        <span className="badge-value text-[10px] px-1.5 py-0.5">
                            {valueBet.edge_percent.toFixed(0)}% edge
                        </span>
                    )}
                    <span className={getStatusClass(fixture.status)}>
                        {isLive
                            ? fixture.status === "halftime" ? "HT" : "LIVE"
                            : fixture.status.toUpperCase()}
                    </span>
                </div>
            </div>

            {/* Teams & Score */}
            <div className="space-y-3">
                <TeamRow
                    name={fixture.home_team.name}
                    logoUrl={fixture.home_team.logo_url}
                    goals={fixture.home_goals}
                    isWinner={isFinished && (fixture.home_goals ?? 0) > (fixture.away_goals ?? 0)}
                    isLive={isLive}
                />
                <TeamRow
                    name={fixture.away_team.name}
                    logoUrl={fixture.away_team.logo_url}
                    goals={fixture.away_goals}
                    isWinner={isFinished && (fixture.away_goals ?? 0) > (fixture.home_goals ?? 0)}
                    isLive={isLive}
                />
            </div>

            {/* AI Prediction Bar — inline on match card */}
            {prediction && !compact && (
                <div className="mt-4 pt-3 border-t border-white/[0.04]">
                    <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[10px] font-medium uppercase tracking-wider text-gray-500 flex items-center gap-1">
                            <svg className="w-3 h-3 text-scorelock-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5" />
                            </svg>
                            AI Prediktion
                        </span>
                        <span className="text-[10px] text-gray-600">
                            {Math.round(prediction.confidence * 100)}% konfidens
                        </span>
                    </div>
                    <div className="prob-bar-track">
                        <div
                            className="prob-bar bg-gradient-to-r from-scorelock-600 to-scorelock-500"
                            style={{ width: `${(prediction.home_win_prob * 100).toFixed(1)}%` }}
                        />
                        <div
                            className="prob-bar bg-gradient-to-r from-gray-500 to-gray-400"
                            style={{ width: `${(prediction.draw_prob * 100).toFixed(1)}%` }}
                        />
                        <div
                            className="prob-bar bg-gradient-to-r from-accent-blue to-blue-400"
                            style={{ width: `${(prediction.away_win_prob * 100).toFixed(1)}%` }}
                        />
                    </div>
                    <div className="flex justify-between mt-1">
                        <span className="text-[10px] font-mono text-gray-500">{formatProb(prediction.home_win_prob)}</span>
                        <span className="text-[10px] font-mono text-gray-500">{formatProb(prediction.draw_prob)}</span>
                        <span className="text-[10px] font-mono text-gray-500">{formatProb(prediction.away_win_prob)}</span>
                    </div>
                </div>
            )}

            {/* Value bet suggestion */}
            {hasValue && !compact && (
                <div className="mt-2 px-3 py-2 rounded-lg bg-scorelock-500/[0.06] border border-scorelock-500/10">
                    <div className="flex items-center justify-between">
                        <span className="text-xs text-scorelock-400 font-medium">
                            Value: {valueBet.suggested_bet === "Home" ? fixture.home_team.name : valueBet.suggested_bet === "Away" ? fixture.away_team.name : "Oavgjort"}
                        </span>
                        <span className="text-xs font-mono text-scorelock-300">
                            Kelly {(valueBet.kelly_fraction * 100).toFixed(1)}%
                        </span>
                    </div>
                </div>
            )}

            {/* Kickoff + arrow */}
            <div className={`${prediction && !compact ? "mt-3 pt-3 border-t border-white/[0.04]" : "mt-4 pt-3 border-t border-white/[0.04]"} flex items-center justify-between`}>
                <span className="text-xs text-gray-500">{formatKickoff(fixture.kickoff)}</span>
                <svg className="w-4 h-4 text-gray-600 group-hover:text-scorelock-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
            </div>
        </a>
    );
}

function TeamRow({
    name,
    logoUrl,
    goals,
    isWinner,
    isLive,
}: {
    name: string;
    logoUrl: string | null;
    goals: number | null;
    isWinner: boolean;
    isLive: boolean;
}) {
    return (
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 min-w-0">
                {logoUrl ? (
                    <img src={logoUrl} alt={name} className="w-7 h-7 object-contain flex-shrink-0" />
                ) : (
                    <div className="w-7 h-7 rounded-full bg-white/[0.04] flex items-center justify-center flex-shrink-0">
                        <span className="text-xs text-gray-500">⚽</span>
                    </div>
                )}
                <span className={`truncate ${isWinner ? "font-semibold text-white" : "text-gray-300"}`}>
                    {name}
                </span>
            </div>
            {goals !== null && (
                <span className={`text-lg font-mono tabular-nums ml-3 ${isWinner ? "font-bold text-white" : isLive ? "text-red-400 font-semibold" : "text-gray-400"
                    }`}>
                    {goals}
                </span>
            )}
        </div>
    );
}

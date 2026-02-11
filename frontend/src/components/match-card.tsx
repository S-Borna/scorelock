import type { Fixture } from "@/lib/types";
import { formatKickoff, getStatusClass } from "@/lib/utils";

interface MatchCardProps {
    fixture: Fixture;
}

export function MatchCard({ fixture }: MatchCardProps) {
    const isLive = fixture.status === "live" || fixture.status === "halftime";
    const isFinished = fixture.status === "finished";

    return (
        <a
            href={`/matches/${fixture.id}`}
            className={`card-interactive block ${isLive ? "border-red-500/15 shadow-[0_0_20px_-5px_rgba(239,68,68,0.1)]" : ""}`}
        >
            {/* League & Status */}
            <div className="flex items-center justify-between mb-4">
                <span className="text-xs text-gray-500 truncate mr-2">
                    {fixture.league.name}
                    {fixture.round && <span className="text-gray-600"> · {fixture.round}</span>}
                </span>
                <span className={getStatusClass(fixture.status)}>
                    {fixture.status === "live" || fixture.status === "halftime"
                        ? fixture.status === "halftime" ? "HT" : "LIVE"
                        : fixture.status.toUpperCase()}
                </span>
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

            {/* Kickoff time */}
            <div className="mt-4 pt-3 border-t border-white/[0.04] flex items-center justify-between">
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
                <span className={`text-lg font-mono tabular-nums ml-3 ${
                    isWinner ? "font-bold text-white" : isLive ? "text-red-400 font-semibold" : "text-gray-400"
                }`}>
                    {goals}
                </span>
            )}
        </div>
    );
}

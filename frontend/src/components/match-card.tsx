import type { Fixture } from "@/lib/types";
import { formatKickoff, getStatusClass } from "@/lib/utils";

interface MatchCardProps {
    fixture: Fixture;
}

export function MatchCard({ fixture }: MatchCardProps) {
    const isLive = fixture.status === "live" || fixture.status === "halftime";
    const isFinished = fixture.status === "finished";

    return (
        <a href={`/matches/${fixture.id}`} className="card hover:border-gray-700 transition-colors block">
            {/* League & Status */}
            <div className="flex items-center justify-between mb-4">
                <span className="text-xs text-gray-500">
                    {fixture.league.name}
                    {fixture.round && ` · ${fixture.round}`}
                </span>
                <span className={getStatusClass(fixture.status)}>
                    {isLive && "● "}
                    {fixture.status.toUpperCase()}
                </span>
            </div>

            {/* Teams & Score */}
            <div className="space-y-3">
                <TeamRow
                    name={fixture.home_team.name}
                    logoUrl={fixture.home_team.logo_url}
                    goals={fixture.home_goals}
                    isWinner={isFinished && (fixture.home_goals ?? 0) > (fixture.away_goals ?? 0)}
                />
                <TeamRow
                    name={fixture.away_team.name}
                    logoUrl={fixture.away_team.logo_url}
                    goals={fixture.away_goals}
                    isWinner={isFinished && (fixture.away_goals ?? 0) > (fixture.home_goals ?? 0)}
                />
            </div>

            {/* Kickoff time */}
            <div className="mt-4 text-xs text-gray-500">
                {formatKickoff(fixture.kickoff)}
            </div>
        </a>
    );
}

function TeamRow({
    name,
    logoUrl,
    goals,
    isWinner,
}: {
    name: string;
    logoUrl: string | null;
    goals: number | null;
    isWinner: boolean;
}) {
    return (
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
                {logoUrl ? (
                    <img src={logoUrl} alt={name} className="w-6 h-6 object-contain" />
                ) : (
                    <div className="w-6 h-6 bg-gray-800 rounded-full" />
                )}
                <span className={isWinner ? "font-semibold" : "text-gray-300"}>
                    {name}
                </span>
            </div>
            {goals !== null && (
                <span className={`text-lg font-mono ${isWinner ? "font-bold" : "text-gray-400"}`}>
                    {goals}
                </span>
            )}
        </div>
    );
}

"use client";

import { useLocale } from "@/components/locale-provider";
import type { FixtureLineupsBundle, LineupPlayer } from "@/lib/types";

const PITCH_W = 100;
const PITCH_H = 150;
const HALF_H = 75;

const HOME_FILL = "#09ce5f";
const AWAY_FILL = "#3b82f6";
const PITCH_BG = "#1a3d1f";
const PITCH_LINE = "rgba(255,255,255,0.4)";
const CAPTAIN_FILL = "#facc15";

interface SideCoord {
    x: number;
    y: number;
}

function homeCoord(gx: number, gy: number): SideCoord {
    return { x: gx, y: (gy * HALF_H) / 100 };
}

function awayCoord(gx: number, gy: number): SideCoord {
    return { x: gx, y: PITCH_H - (gy * HALF_H) / 100 };
}

function PlayerNode({
    player,
    side,
}: {
    player: LineupPlayer;
    side: "home" | "away";
}) {
    if (player.grid_x === null || player.grid_y === null) return null;
    const { x, y } =
        side === "home"
            ? homeCoord(player.grid_x, player.grid_y)
            : awayCoord(player.grid_x, player.grid_y);
    const fill = side === "home" ? HOME_FILL : AWAY_FILL;

    return (
        <g>
            <circle
                cx={x}
                cy={y}
                r={4.2}
                fill={fill}
                stroke="white"
                strokeWidth={0.5}
            />
            <text
                x={x}
                y={y + 1.4}
                textAnchor="middle"
                fontSize={3.6}
                fontWeight={700}
                fill="white"
            >
                {player.shirt_number ?? ""}
            </text>
            {player.is_captain && (
                <>
                    <circle
                        cx={x + 3.2}
                        cy={y - 3.2}
                        r={1.7}
                        fill={CAPTAIN_FILL}
                        stroke="white"
                        strokeWidth={0.3}
                    />
                    <text
                        x={x + 3.2}
                        y={y - 2.6}
                        textAnchor="middle"
                        fontSize={2}
                        fontWeight={700}
                        fill="black"
                    >
                        C
                    </text>
                </>
            )}
            <text
                x={x}
                y={y + 8}
                textAnchor="middle"
                fontSize={2.6}
                fill="white"
            >
                {player.display_name}
            </text>
        </g>
    );
}

function PitchBackground() {
    return (
        <g>
            <rect x={0} y={0} width={PITCH_W} height={PITCH_H} fill={PITCH_BG} />
            <rect
                x={2}
                y={2}
                width={PITCH_W - 4}
                height={PITCH_H - 4}
                fill="none"
                stroke={PITCH_LINE}
                strokeWidth={0.4}
            />
            <line
                x1={2}
                y1={PITCH_H / 2}
                x2={PITCH_W - 2}
                y2={PITCH_H / 2}
                stroke={PITCH_LINE}
                strokeWidth={0.4}
            />
            <circle
                cx={PITCH_W / 2}
                cy={PITCH_H / 2}
                r={9}
                fill="none"
                stroke={PITCH_LINE}
                strokeWidth={0.4}
            />
            <circle
                cx={PITCH_W / 2}
                cy={PITCH_H / 2}
                r={0.7}
                fill={PITCH_LINE}
            />
            {/* Top penalty area (home side) */}
            <rect
                x={25}
                y={2}
                width={50}
                height={14}
                fill="none"
                stroke={PITCH_LINE}
                strokeWidth={0.4}
            />
            <rect
                x={38}
                y={2}
                width={24}
                height={6}
                fill="none"
                stroke={PITCH_LINE}
                strokeWidth={0.4}
            />
            {/* Bottom penalty area (away side) */}
            <rect
                x={25}
                y={PITCH_H - 16}
                width={50}
                height={14}
                fill="none"
                stroke={PITCH_LINE}
                strokeWidth={0.4}
            />
            <rect
                x={38}
                y={PITCH_H - 8}
                width={24}
                height={6}
                fill="none"
                stroke={PITCH_LINE}
                strokeWidth={0.4}
            />
        </g>
    );
}

function SubsList({
    label,
    subs,
    align,
}: {
    label: string;
    subs: LineupPlayer[];
    align: "left" | "right";
}) {
    if (subs.length === 0) return <div />;
    return (
        <div className={align === "right" ? "text-right" : ""}>
            <h3 className="text-xs uppercase tracking-wider text-gray-500 mb-2">
                {label}
            </h3>
            <ul className="space-y-1 text-sm">
                {subs.map((p, i) => (
                    <li key={i} className="text-gray-300">
                        <span className="font-mono text-gray-500 w-6 inline-block">
                            {p.shirt_number ?? "—"}
                        </span>
                        {p.display_name}
                    </li>
                ))}
            </ul>
        </div>
    );
}

export function LineupsPitch({
    lineups,
    homeTeamName,
    awayTeamName,
}: {
    lineups: FixtureLineupsBundle;
    homeTeamName: string;
    awayTeamName: string;
}) {
    const { t } = useLocale();
    const home = lineups.home;
    const away = lineups.away;
    if (!home && !away) return null;

    const homeStarters = home?.starters ?? [];
    const awayStarters = away?.starters ?? [];
    const homeSubs = home?.substitutes ?? [];
    const awaySubs = away?.substitutes ?? [];

    return (
        <div className="card">
            <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                <h2 className="text-base font-semibold text-white">
                    👥 {t("lineup.title")}
                </h2>
                <div className="text-xs text-gray-400 flex gap-3 font-mono">
                    {home?.formation && (
                        <span>
                            <span style={{ color: HOME_FILL }}>●</span>{" "}
                            {home.formation}
                        </span>
                    )}
                    {away?.formation && (
                        <span>
                            <span style={{ color: AWAY_FILL }}>●</span>{" "}
                            {away.formation}
                        </span>
                    )}
                </div>
            </div>

            <svg
                viewBox={`0 0 ${PITCH_W} ${PITCH_H}`}
                className="w-full max-w-md mx-auto rounded-lg block"
                role="img"
                aria-label={`${homeTeamName} vs ${awayTeamName}`}
            >
                <PitchBackground />
                {homeStarters.map((p, i) => (
                    <PlayerNode key={`h-${i}`} player={p} side="home" />
                ))}
                {awayStarters.map((p, i) => (
                    <PlayerNode key={`a-${i}`} player={p} side="away" />
                ))}
            </svg>

            {(home?.coach_name || away?.coach_name) && (
                <div className="grid grid-cols-2 gap-4 mt-4 text-xs">
                    <div>
                        {home?.coach_name && (
                            <span className="text-gray-400">
                                {t("lineup.coach")}:{" "}
                                <span className="text-white">{home.coach_name}</span>
                            </span>
                        )}
                    </div>
                    <div className="text-right">
                        {away?.coach_name && (
                            <span className="text-gray-400">
                                {t("lineup.coach")}:{" "}
                                <span className="text-white">{away.coach_name}</span>
                            </span>
                        )}
                    </div>
                </div>
            )}

            {(homeSubs.length > 0 || awaySubs.length > 0) && (
                <div className="grid grid-cols-2 gap-4 mt-6">
                    <SubsList
                        label={`${homeTeamName} – ${t("lineup.substitutes")}`}
                        subs={homeSubs}
                        align="left"
                    />
                    <SubsList
                        label={`${awayTeamName} – ${t("lineup.substitutes")}`}
                        subs={awaySubs}
                        align="right"
                    />
                </div>
            )}
        </div>
    );
}

"use client";

import { useLocale } from "@/components/locale-provider";
import type {
    FantasyTeam,
    FantasyTeamPlayerEntry,
} from "@/lib/types";

const PITCH_W = 100;
const PITCH_H = 150;
const PITCH_BG = "#1a3d1f";
const PITCH_LINE = "rgba(255,255,255,0.4)";
const POSITION_COLOR: Record<string, string> = {
    GK: "#facc15",
    DEF: "#3b82f6",
    MID: "#09ce5f",
    FWD: "#ef4444",
};

interface FormationLayout {
    DEF: number;
    MID: number;
    FWD: number;
}

const FORMATION_LAYOUTS: Record<string, FormationLayout> = {
    "4-3-3": { DEF: 4, MID: 3, FWD: 3 },
    "4-4-2": { DEF: 4, MID: 4, FWD: 2 },
    "3-5-2": { DEF: 3, MID: 5, FWD: 2 },
    "4-2-3-1": { DEF: 4, MID: 5, FWD: 1 },
    "3-4-3": { DEF: 3, MID: 4, FWD: 3 },
    "5-3-2": { DEF: 5, MID: 3, FWD: 2 },
};

const ROW_Y: Record<string, number> = {
    GK: 12,
    DEF: 40,
    MID: 75,
    FWD: 110,
};

function placeRow(count: number, y: number): { x: number; y: number }[] {
    const margin = 14;
    const usable = PITCH_W - margin * 2;
    if (count === 1) return [{ x: PITCH_W / 2, y }];
    const step = usable / (count - 1);
    return Array.from({ length: count }, (_, i) => ({
        x: margin + i * step,
        y,
    }));
}

function PitchBackground() {
    return (
        <g>
            <rect
                x={0}
                y={0}
                width={PITCH_W}
                height={PITCH_H}
                fill={PITCH_BG}
            />
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
                x={25}
                y={PITCH_H - 16}
                width={50}
                height={14}
                fill="none"
                stroke={PITCH_LINE}
                strokeWidth={0.4}
            />
        </g>
    );
}

function PlayerNode({
    entry,
    x,
    y,
}: {
    entry: FantasyTeamPlayerEntry;
    x: number;
    y: number;
}) {
    const fill = POSITION_COLOR[entry.slot_position] ?? "#ffffff";
    return (
        <g>
            <circle
                cx={x}
                cy={y}
                r={4.6}
                fill={fill}
                stroke="white"
                strokeWidth={0.5}
            />
            {entry.is_captain && (
                <>
                    <circle
                        cx={x + 3.6}
                        cy={y - 3.6}
                        r={1.8}
                        fill="#facc15"
                        stroke="white"
                        strokeWidth={0.3}
                    />
                    <text
                        x={x + 3.6}
                        y={y - 3.0}
                        textAnchor="middle"
                        fontSize={2.1}
                        fontWeight={700}
                        fill="black"
                    >
                        C
                    </text>
                </>
            )}
            {entry.is_vice_captain && !entry.is_captain && (
                <>
                    <circle
                        cx={x + 3.6}
                        cy={y - 3.6}
                        r={1.8}
                        fill="#94a3b8"
                        stroke="white"
                        strokeWidth={0.3}
                    />
                    <text
                        x={x + 3.6}
                        y={y - 3.0}
                        textAnchor="middle"
                        fontSize={2.1}
                        fontWeight={700}
                        fill="black"
                    >
                        V
                    </text>
                </>
            )}
            <text
                x={x}
                y={y + 8}
                textAnchor="middle"
                fontSize={2.6}
                fill="white"
                fontWeight={600}
            >
                {entry.display_name}
            </text>
            <text
                x={x}
                y={y + 11}
                textAnchor="middle"
                fontSize={2.2}
                fill="rgba(255,255,255,0.6)"
            >
                €{(entry.current_price / 10).toFixed(1)}M
            </text>
        </g>
    );
}

export function TeamPitchView({ team }: { team: FantasyTeam }) {
    const { t } = useLocale();
    const layout = FORMATION_LAYOUTS[team.formation] ?? FORMATION_LAYOUTS["4-3-3"];

    const starting = team.players.filter((p) => p.is_starting);
    const bench = team.players.filter((p) => !p.is_starting);

    const gks = starting.filter((p) => p.slot_position === "GK").slice(0, 1);
    const defs = starting.filter((p) => p.slot_position === "DEF").slice(0, layout.DEF);
    const mids = starting.filter((p) => p.slot_position === "MID").slice(0, layout.MID);
    const fwds = starting.filter((p) => p.slot_position === "FWD").slice(0, layout.FWD);

    const gkPos = placeRow(gks.length, ROW_Y.GK);
    const defPos = placeRow(defs.length, ROW_Y.DEF);
    const midPos = placeRow(mids.length, ROW_Y.MID);
    const fwdPos = placeRow(fwds.length, ROW_Y.FWD);

    return (
        <div className="card">
            <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
                <h2 className="text-base font-semibold text-white">
                    {t("fantasy.team.starting_xi")}
                </h2>
                <span className="text-xs text-gray-400 font-mono">
                    {team.formation}
                </span>
            </div>
            <svg
                viewBox={`0 0 ${PITCH_W} ${PITCH_H}`}
                className="w-full max-w-md mx-auto rounded-lg block"
                role="img"
                aria-label={`${team.name} – ${team.formation}`}
            >
                <PitchBackground />
                {gks.map((p, i) => (
                    <PlayerNode key={p.player_id} entry={p} x={gkPos[i].x} y={gkPos[i].y} />
                ))}
                {defs.map((p, i) => (
                    <PlayerNode key={p.player_id} entry={p} x={defPos[i].x} y={defPos[i].y} />
                ))}
                {mids.map((p, i) => (
                    <PlayerNode key={p.player_id} entry={p} x={midPos[i].x} y={midPos[i].y} />
                ))}
                {fwds.map((p, i) => (
                    <PlayerNode key={p.player_id} entry={p} x={fwdPos[i].x} y={fwdPos[i].y} />
                ))}
            </svg>

            {bench.length > 0 && (
                <div className="mt-6">
                    <h3 className="text-xs uppercase tracking-wider text-gray-500 mb-3">
                        {t("fantasy.team.bench")}
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        {bench.map((p) => (
                            <div
                                key={p.player_id}
                                className="bg-white/[0.03] rounded px-2 py-2 text-center"
                            >
                                <div
                                    className="inline-block w-2 h-2 rounded-full mb-1"
                                    style={{
                                        background:
                                            POSITION_COLOR[p.slot_position] ?? "#fff",
                                    }}
                                />
                                <div className="text-xs text-white truncate">
                                    {p.display_name}
                                </div>
                                <div className="text-[10px] text-gray-500 font-mono">
                                    €{(p.current_price / 10).toFixed(1)}M
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

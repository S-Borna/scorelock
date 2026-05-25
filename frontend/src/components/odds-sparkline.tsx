"use client";

import { useLocale } from "@/components/locale-provider";
import type { OddsSnapshot, OddsSnapshotsBundle } from "@/lib/types";

const W = 320;
const H = 100;
const PAD_X = 28;
const PAD_Y = 14;

const OUTCOME_COLOR: Record<string, string> = {
    home: "#09ce5f",
    draw: "#94a3b8",
    away: "#3b82f6",
};

const OUTCOME_LABEL: Record<string, string> = {
    home: "1",
    draw: "X",
    away: "2",
};

interface BestSeriesPoint {
    t: number;
    home: number | null;
    draw: number | null;
    away: number | null;
}

function buildBestSeries(snapshots: OddsSnapshot[]): BestSeriesPoint[] {
    // Guard: fixtures utan odds-snapshots ger undefined/null → kraschar annars
    // hela match-detaljsidan (TypeError: snapshots is not iterable).
    if (!Array.isArray(snapshots) || snapshots.length === 0) return [];
    const byTimestamp = new Map<string, OddsSnapshot[]>();
    for (const s of snapshots) {
        const arr = byTimestamp.get(s.taken_at) ?? [];
        arr.push(s);
        byTimestamp.set(s.taken_at, arr);
    }
    const points: BestSeriesPoint[] = [];
    for (const [iso, group] of byTimestamp) {
        const t = new Date(iso).getTime();
        const best = (k: "home" | "draw" | "away") =>
            group.reduce(
                (acc, s) => Math.max(acc, Number(s.outcomes[k] ?? 0)),
                0,
            );
        points.push({
            t,
            home: best("home") || null,
            draw: best("draw") || null,
            away: best("away") || null,
        });
    }
    points.sort((a, b) => a.t - b.t);
    return points;
}

function makePath(
    points: BestSeriesPoint[],
    key: "home" | "draw" | "away",
    minOdds: number,
    maxOdds: number,
): string {
    if (points.length < 2) return "";
    const tMin = points[0].t;
    const tMax = points[points.length - 1].t;
    const xRange = W - PAD_X * 2;
    const yRange = H - PAD_Y * 2;
    const span = maxOdds - minOdds || 1;

    let d = "";
    for (let i = 0; i < points.length; i++) {
        const p = points[i];
        const v = p[key];
        if (v === null) continue;
        const x =
            PAD_X +
            ((p.t - tMin) / Math.max(tMax - tMin, 1)) * xRange;
        const y = PAD_Y + (1 - (v - minOdds) / span) * yRange;
        d += d.length === 0 ? `M ${x.toFixed(1)} ${y.toFixed(1)}` : ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
    }
    return d;
}

export function OddsSparkline({
    bundle,
}: {
    bundle: OddsSnapshotsBundle;
}) {
    const { t } = useLocale();
    const series = buildBestSeries(bundle.snapshots);
    if (series.length < 2) return null;

    const allOdds = series.flatMap((p) => [p.home, p.draw, p.away].filter((v): v is number => v !== null));
    const minOdds = Math.min(...allOdds);
    const maxOdds = Math.max(...allOdds);

    const latest = series[series.length - 1];

    return (
        <div className="card">
            <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
                <div>
                    <h2 className="text-base font-semibold text-white">
                        📈 {t("odds.movement_title")}
                    </h2>
                    <p className="text-xs text-gray-500 mt-1">
                        {t("odds.movement_subtitle")}
                    </p>
                </div>
                <div className="flex items-center gap-3 text-xs font-mono">
                    {(["home", "draw", "away"] as const).map((k) => (
                        <span key={k} className="flex items-center gap-1">
                            <span
                                className="inline-block w-2.5 h-2.5 rounded-full"
                                style={{ background: OUTCOME_COLOR[k] }}
                            />
                            <span className="text-gray-400">{OUTCOME_LABEL[k]}</span>
                            <span className="text-white tabular-nums">
                                {latest[k]?.toFixed(2) ?? "—"}
                            </span>
                        </span>
                    ))}
                </div>
            </div>
            <svg
                viewBox={`0 0 ${W} ${H}`}
                className="w-full block"
                role="img"
                aria-label="Odds movement sparkline"
            >
                <line
                    x1={PAD_X}
                    y1={H - PAD_Y}
                    x2={W - PAD_X}
                    y2={H - PAD_Y}
                    stroke="rgba(255,255,255,0.08)"
                    strokeWidth={0.5}
                />
                {(["home", "draw", "away"] as const).map((k) => (
                    <path
                        key={k}
                        d={makePath(series, k, minOdds, maxOdds)}
                        fill="none"
                        stroke={OUTCOME_COLOR[k]}
                        strokeWidth={1.5}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                ))}
                <text
                    x={PAD_X}
                    y={PAD_Y - 4}
                    fill="rgba(255,255,255,0.4)"
                    fontSize={9}
                    fontFamily="monospace"
                >
                    {maxOdds.toFixed(2)}
                </text>
                <text
                    x={PAD_X}
                    y={H - PAD_Y + 9}
                    fill="rgba(255,255,255,0.4)"
                    fontSize={9}
                    fontFamily="monospace"
                >
                    {minOdds.toFixed(2)}
                </text>
            </svg>
        </div>
    );
}

"use client";

import { useLocale } from "@/components/locale-provider";
import type { MomentumSeries } from "@/lib/types";

const W = 320;
const H = 110;
const PAD_X = 24;
const PAD_Y = 12;

const HOME_FILL = "#09ce5f";
const AWAY_FILL = "#3b82f6";

function buildArea(
    points: { minute: number; pct: number }[],
    side: "home" | "away",
): string {
    if (points.length < 2) return "";
    const minM = points[0].minute;
    const maxM = points[points.length - 1].minute;
    const xRange = W - PAD_X * 2;
    const yRange = H - PAD_Y * 2;

    let d = "";
    for (let i = 0; i < points.length; i++) {
        const p = points[i];
        const x = PAD_X + ((p.minute - minM) / Math.max(maxM - minM, 1)) * xRange;
        const yPct = side === "home" ? p.pct : 100 - p.pct;
        const y = PAD_Y + (1 - yPct / 100) * yRange;
        d += d.length === 0 ? `M ${x.toFixed(1)} ${y.toFixed(1)}` : ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
    }
    if (side === "home") {
        d += ` L ${(W - PAD_X).toFixed(1)} ${(H - PAD_Y).toFixed(1)} L ${PAD_X.toFixed(1)} ${(H - PAD_Y).toFixed(1)} Z`;
    } else {
        d += ` L ${(W - PAD_X).toFixed(1)} ${PAD_Y.toFixed(1)} L ${PAD_X.toFixed(1)} ${PAD_Y.toFixed(1)} Z`;
    }
    return d;
}

export function MomentumGraph({ series }: { series: MomentumSeries }) {
    const { t } = useLocale();
    if (series.points.length < 2) return null;

    const points = series.points.map((p) => ({
        minute: p.match_minute,
        pct: p.home_momentum_pct,
    }));

    return (
        <div className="card">
            <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
                <div>
                    <h2 className="text-base font-semibold text-white">
                        🌊 {t("momentum.title")}
                    </h2>
                    <p className="text-xs text-gray-500 mt-1">
                        {t("momentum.subtitle")}
                    </p>
                </div>
                <div className="flex items-center gap-3 text-xs font-mono">
                    <span className="flex items-center gap-1">
                        <span
                            className="inline-block w-2.5 h-2.5 rounded-full"
                            style={{ background: HOME_FILL }}
                        />
                        <span className="text-gray-400">Hemma</span>
                    </span>
                    <span className="flex items-center gap-1">
                        <span
                            className="inline-block w-2.5 h-2.5 rounded-full"
                            style={{ background: AWAY_FILL }}
                        />
                        <span className="text-gray-400">Borta</span>
                    </span>
                </div>
            </div>
            <svg
                viewBox={`0 0 ${W} ${H}`}
                className="w-full block"
                role="img"
                aria-label="Momentum series"
            >
                <line
                    x1={PAD_X}
                    y1={H / 2}
                    x2={W - PAD_X}
                    y2={H / 2}
                    stroke="rgba(255,255,255,0.08)"
                    strokeWidth={0.4}
                    strokeDasharray="2 2"
                />
                <path d={buildArea(points, "home")} fill={HOME_FILL} fillOpacity={0.65} />
                <path d={buildArea(points, "away")} fill={AWAY_FILL} fillOpacity={0.55} />
                {[15, 30, 45, 60, 75, 90].map((m) => {
                    const minM = points[0].minute;
                    const maxM = points[points.length - 1].minute;
                    if (m < minM || m > maxM) return null;
                    const x = PAD_X + ((m - minM) / Math.max(maxM - minM, 1)) * (W - PAD_X * 2);
                    return (
                        <text
                            key={m}
                            x={x}
                            y={H - 2}
                            fill="rgba(255,255,255,0.4)"
                            fontSize={8}
                            fontFamily="monospace"
                            textAnchor="middle"
                        >
                            {m}'
                        </text>
                    );
                })}
            </svg>
        </div>
    );
}

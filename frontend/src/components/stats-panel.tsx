"use client";

import { useLocale } from "@/components/locale-provider";
import type { FixtureStatisticsBundle } from "@/lib/types";

type Row = {
    labelKey: string;
    home: number | null;
    away: number | null;
    asPercent?: boolean;
    decimals?: number;
};

function format(v: number | null, decimals = 0): string {
    if (v === null || v === undefined) return "—";
    return v.toFixed(decimals);
}

function StatRow({ row, t }: { row: Row; t: (k: string) => string }) {
    const home = row.home ?? 0;
    const away = row.away ?? 0;
    let homePct: number;
    if (row.asPercent) {
        homePct = home;
    } else {
        const total = home + away;
        homePct = total > 0 ? (home / total) * 100 : 50;
    }
    const awayPct = 100 - homePct;
    return (
        <div className="space-y-1">
            <div className="flex items-baseline justify-between text-sm">
                <span className="font-mono text-white tabular-nums">
                    {format(row.home, row.decimals ?? 0)}
                    {row.asPercent && row.home !== null ? "%" : ""}
                </span>
                <span className="text-xs text-gray-400">{t(row.labelKey)}</span>
                <span className="font-mono text-white tabular-nums">
                    {format(row.away, row.decimals ?? 0)}
                    {row.asPercent && row.away !== null ? "%" : ""}
                </span>
            </div>
            <div className="flex h-1.5 rounded-full overflow-hidden bg-white/[0.04]">
                <div
                    className="bg-scorelock-500"
                    style={{ width: `${homePct}%` }}
                />
                <div
                    className="bg-blue-500"
                    style={{ width: `${awayPct}%` }}
                />
            </div>
        </div>
    );
}

export function StatsPanel({ stats }: { stats: FixtureStatisticsBundle }) {
    const { t } = useLocale();
    const home = stats.home;
    const away = stats.away;
    if (!home && !away) return null;

    const rows: Row[] = [
        { labelKey: "stats.possession", home: home?.possession_pct ?? null, away: away?.possession_pct ?? null, asPercent: true, decimals: 0 },
        { labelKey: "stats.xg", home: home?.xg ?? null, away: away?.xg ?? null, decimals: 2 },
        { labelKey: "stats.shots_total", home: home?.shots_total ?? null, away: away?.shots_total ?? null },
        { labelKey: "stats.shots_on_target", home: home?.shots_on_target ?? null, away: away?.shots_on_target ?? null },
        { labelKey: "stats.corners", home: home?.corners ?? null, away: away?.corners ?? null },
        { labelKey: "stats.fouls", home: home?.fouls ?? null, away: away?.fouls ?? null },
        { labelKey: "stats.offsides", home: home?.offsides ?? null, away: away?.offsides ?? null },
        { labelKey: "stats.pass_accuracy", home: home?.pass_accuracy_pct ?? null, away: away?.pass_accuracy_pct ?? null, asPercent: true, decimals: 0 },
        { labelKey: "stats.tackles", home: home?.tackles ?? null, away: away?.tackles ?? null },
    ];

    return (
        <div className="card">
            <h2 className="text-base font-semibold mb-4 text-white">
                📊 {t("stats.title")}
            </h2>
            <div className="space-y-3">
                {rows.map((r) => (
                    <StatRow key={r.labelKey} row={r} t={t} />
                ))}
            </div>
        </div>
    );
}

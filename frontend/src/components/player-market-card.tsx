"use client";

import Image from "next/image";
import { useLocale } from "@/components/locale-provider";
import type { FantasyPlayerMarketEntry, FantasyValueTrend } from "@/lib/types";

const POSITION_LABEL_KEY: Record<string, string> = {
    GK: "fantasy.market.position.GK",
    DEF: "fantasy.market.position.DEF",
    MID: "fantasy.market.position.MID",
    FWD: "fantasy.market.position.FWD",
};

const POSITION_COLOR: Record<string, string> = {
    GK: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
    DEF: "bg-blue-500/20 text-blue-300 border-blue-500/30",
    MID: "bg-green-500/20 text-green-300 border-green-500/30",
    FWD: "bg-red-500/20 text-red-300 border-red-500/30",
};

const TREND_GLYPH: Record<FantasyValueTrend, string> = {
    up: "▲",
    down: "▼",
    stable: "—",
};

const TREND_COLOR: Record<FantasyValueTrend, string> = {
    up: "text-green-400",
    down: "text-red-400",
    stable: "text-gray-500",
};

function normalizePosition(code: string | null): string {
    if (!code) return "MID";
    const c = code.toUpperCase();
    if (c.startsWith("G")) return "GK";
    if (
        c.startsWith("D") ||
        c.startsWith("L") ||
        c.startsWith("R") ||
        c.startsWith("CB") ||
        c.startsWith("WB")
    ) {
        return "DEF";
    }
    if (
        c.startsWith("M") ||
        c.startsWith("CM") ||
        c.startsWith("DM") ||
        c.startsWith("AM")
    ) {
        return "MID";
    }
    return "FWD";
}

function formatPrice(units: number): string {
    return `${(units / 10).toFixed(1)}`;
}

export function PlayerMarketCard({
    entry,
}: {
    entry: FantasyPlayerMarketEntry;
}) {
    const { t } = useLocale();
    const pos = normalizePosition(entry.position_code);
    return (
        <div className="card flex items-center gap-4 hover:border-scorelock-500/20 transition-colors">
            <div className="flex-shrink-0">
                {entry.team_logo_url ? (
                    <Image
                        src={entry.team_logo_url}
                        alt={entry.team_name ?? ""}
                        width={36}
                        height={36}
                        className="rounded"
                    />
                ) : (
                    <div className="w-9 h-9 rounded bg-white/[0.06]" />
                )}
            </div>
            <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                    <span className="text-white font-semibold truncate">
                        {entry.display_name}
                    </span>
                    <span
                        className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border font-mono ${POSITION_COLOR[pos]}`}
                    >
                        {pos}
                    </span>
                </div>
                <div className="text-xs text-gray-500 truncate">
                    {entry.team_name ?? "—"}
                </div>
            </div>
            <div className="grid grid-cols-3 gap-3 text-right text-xs">
                <div>
                    <div className="text-gray-500">{t("fantasy.market.price")}</div>
                    <div className="font-mono text-white font-semibold tabular-nums">
                        €{formatPrice(entry.current_price)}
                        <span
                            className={`ml-1 ${TREND_COLOR[entry.value_trend]}`}
                            aria-label={entry.value_trend}
                        >
                            {TREND_GLYPH[entry.value_trend]}
                        </span>
                    </div>
                </div>
                <div>
                    <div className="text-gray-500">{t("fantasy.market.points")}</div>
                    <div className="font-mono text-white tabular-nums">
                        {entry.fantasy_points_total}
                    </div>
                </div>
                <div>
                    <div className="text-gray-500">{t("fantasy.market.ownership")}</div>
                    <div className="font-mono text-white tabular-nums">
                        {entry.selected_by_pct.toFixed(1)}%
                    </div>
                </div>
            </div>
            {/* position-label translation key exists for future tooltip use */}
            <span className="sr-only">{t(POSITION_LABEL_KEY[pos])}</span>
        </div>
    );
}

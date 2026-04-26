"use client";

import { useLocale } from "@/components/locale-provider";
import type { MatchInfo } from "@/lib/types";

const SURFACE_KEY: Record<string, string> = {
    grass: "match_info.surface_grass",
    artificial: "match_info.surface_artificial",
    hybrid: "match_info.surface_hybrid",
};

export function MatchInfoStrip({ info }: { info: MatchInfo }) {
    const { t } = useLocale();
    const venue = info.venue;
    const ref = info.referee;
    if (!venue && !ref) return null;

    return (
        <div className="card mb-6">
            <div className="grid gap-3 sm:grid-cols-2 text-sm">
                {venue && (
                    <div>
                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                            🏟 {t("match_info.stadium")}
                        </div>
                        <div className="text-white font-semibold">
                            {venue.display_name}
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5 font-mono">
                            {venue.city ? `${venue.city} · ` : ""}
                            {venue.capacity
                                ? `${t("match_info.capacity")} ${venue.capacity.toLocaleString("sv-SE")}`
                                : ""}
                            {venue.surface && SURFACE_KEY[venue.surface]
                                ? ` · ${t(SURFACE_KEY[venue.surface])}`
                                : ""}
                        </div>
                    </div>
                )}
                {ref && (
                    <div className="sm:text-right">
                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                            ⚖ {t("match_info.referee")}
                        </div>
                        <div className="text-white font-semibold">
                            {ref.display_name}
                            {ref.nationality_iso_2 ? (
                                <span className="text-gray-500 font-mono ml-2 text-xs">
                                    {ref.nationality_iso_2}
                                </span>
                            ) : null}
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5 font-mono">
                            {ref.career_games_count !== null
                                ? `${ref.career_games_count} matcher`
                                : ""}
                            {ref.career_yellows_per_game !== null
                                ? ` · ${ref.career_yellows_per_game.toFixed(1)} ${t("match_info.yellows_per_game")}`
                                : ""}
                            {ref.career_reds_per_game !== null
                                ? ` · ${ref.career_reds_per_game.toFixed(2)} ${t("match_info.reds_per_game")}`
                                : ""}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

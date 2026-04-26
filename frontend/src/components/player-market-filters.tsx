"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";
import { useLocale } from "@/components/locale-provider";

const POSITIONS = ["all", "GK", "DEF", "MID", "FWD"] as const;
const SORTS = [
    "ownership_desc",
    "price_desc",
    "price_asc",
    "points_desc",
] as const;

export function PlayerMarketFilters({
    seasonId,
}: {
    seasonId: number;
}) {
    const router = useRouter();
    const search = useSearchParams();
    const { t } = useLocale();

    const currentPosition = search.get("position") ?? "all";
    const currentSort = search.get("sort") ?? "ownership_desc";

    const update = useCallback(
        (key: string, value: string) => {
            const params = new URLSearchParams(search.toString());
            if (value === "all" || value === "" || value === undefined) {
                params.delete(key);
            } else {
                params.set(key, value);
            }
            router.push(`/fantasy/seasons/${seasonId}/players?${params.toString()}`);
        },
        [router, search, seasonId],
    );

    return (
        <div className="card flex flex-wrap gap-4 mb-6">
            <div>
                <label className="block text-xs text-gray-500 mb-2 uppercase tracking-wider">
                    {t("fantasy.market.filter_position")}
                </label>
                <div className="flex gap-1 flex-wrap">
                    {POSITIONS.map((p) => (
                        <button
                            key={p}
                            type="button"
                            onClick={() => update("position", p)}
                            className={
                                "px-3 py-1.5 text-xs rounded font-mono uppercase tracking-wider transition-colors " +
                                (currentPosition === p
                                    ? "bg-scorelock-500 text-black"
                                    : "bg-white/[0.04] text-gray-400 hover:bg-white/[0.08]")
                            }
                        >
                            {p === "all"
                                ? t("fantasy.market.position.all")
                                : p}
                        </button>
                    ))}
                </div>
            </div>
            <div className="flex-1 min-w-[200px]">
                <label className="block text-xs text-gray-500 mb-2 uppercase tracking-wider">
                    {t("fantasy.market.sort.price_desc").split(" (")[0]}
                </label>
                <select
                    value={currentSort}
                    onChange={(e) => update("sort", e.target.value)}
                    className="w-full bg-white/[0.04] text-white text-sm rounded px-3 py-2 border border-white/[0.06]"
                >
                    {SORTS.map((s) => (
                        <option key={s} value={s}>
                            {t(`fantasy.market.sort.${s}`)}
                        </option>
                    ))}
                </select>
            </div>
        </div>
    );
}

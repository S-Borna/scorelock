"use client";

import Link from "next/link";
import { useLocale } from "@/components/locale-provider";
import type { FantasySeason } from "@/lib/types";

const SCOPE_KEY: Record<FantasySeason["scope"], string> = {
    demo: "fantasy.season.scope.demo",
    single_league: "fantasy.season.scope.single_league",
    cross_european: "fantasy.season.scope.cross_european",
    world_cup: "fantasy.season.scope.world_cup",
};

function formatDateRange(start: string, end: string): string {
    const s = new Date(start);
    const e = new Date(end);
    const sameYear = s.getFullYear() === e.getFullYear();
    const sFmt = `${s.getDate()}/${s.getMonth() + 1}${sameYear ? "" : ` ${s.getFullYear()}`}`;
    const eFmt = `${e.getDate()}/${e.getMonth() + 1} ${e.getFullYear()}`;
    return `${sFmt} – ${eFmt}`;
}

function formatBudget(units: number): string {
    return `${(units / 10).toFixed(1)}M`;
}

export function SeasonCard({ season }: { season: FantasySeason }) {
    const { t } = useLocale();
    return (
        <Link
            href={`/fantasy/seasons/${season.id}`}
            className="card hover:border-scorelock-500/30 transition-colors block"
        >
            <div className="flex items-start justify-between gap-3 mb-3">
                <h3 className="text-base font-semibold text-white leading-tight">
                    {season.name}
                </h3>
                <span className="text-xs uppercase tracking-wider px-2 py-1 rounded bg-white/[0.04] text-gray-400 font-mono">
                    {t(SCOPE_KEY[season.scope])}
                </span>
            </div>
            <dl className="grid grid-cols-2 gap-2 text-xs text-gray-400">
                <div>
                    <dt className="text-gray-500">{t("fantasy.season.start_to_end")}</dt>
                    <dd className="text-white font-mono">
                        {formatDateRange(season.start_date, season.end_date)}
                    </dd>
                </div>
                <div>
                    <dt className="text-gray-500">{t("fantasy.season.budget")}</dt>
                    <dd className="text-white font-mono">
                        €{formatBudget(season.total_budget_units)}
                    </dd>
                </div>
            </dl>
            <p className="text-xs text-scorelock-400 mt-3">
                {t("fantasy.season.view_market")}
            </p>
        </Link>
    );
}

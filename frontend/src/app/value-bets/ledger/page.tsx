import type { Metadata } from "next";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import type { ValueBetLedger, ValueBetLedgerEntry } from "@/lib/types";

export const metadata: Metadata = {
    title: "Value-bet ledger — ScoreLock",
    description:
        "Vi visar alla value-bet-tips, även förlorarna. Trust by transparency.",
};

interface PageProps {
    searchParams: Promise<{ status?: string }>;
}

const STATUS_LABEL: Record<string, string> = {
    win: "Vann",
    loss: "Förlust",
    pending: "Väntande",
};

const STATUS_COLOR: Record<string, string> = {
    win: "bg-green-500/15 text-green-300 border-green-500/30",
    loss: "bg-red-500/15 text-red-300 border-red-500/30",
    pending: "bg-yellow-500/15 text-yellow-300 border-yellow-500/30",
};

function formatDate(iso: string): string {
    const d = new Date(iso);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function StatBox({ label, value, hint }: { label: string; value: string; hint?: string }) {
    return (
        <div className="card">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                {label}
            </div>
            <div className="text-2xl font-mono text-white tabular-nums">
                {value}
            </div>
            {hint && (
                <div className="text-xs text-gray-500 mt-1 font-mono">{hint}</div>
            )}
        </div>
    );
}

function LedgerRow({ entry }: { entry: ValueBetLedgerEntry }) {
    return (
        <Link
            href={`/matches/${entry.fixture_id}`}
            className="block bg-white/[0.02] hover:bg-white/[0.04] border-b border-white/[0.04] last:border-0 transition-colors"
        >
            <div className="grid grid-cols-12 gap-3 items-center py-3 px-4 text-sm">
                <div className="col-span-12 sm:col-span-5">
                    <div className="text-white font-semibold truncate">
                        {entry.home_team_name} – {entry.away_team_name}
                    </div>
                    <div className="text-xs text-gray-500 truncate font-mono">
                        {entry.league_name ?? "—"} · {formatDate(entry.kickoff)}
                    </div>
                </div>
                <div className="col-span-4 sm:col-span-2 font-mono text-white">
                    {entry.suggested_bet}
                    <div className="text-xs text-gray-500">
                        {Math.round(entry.model_probability * 100)}%
                    </div>
                </div>
                <div className="col-span-4 sm:col-span-2 font-mono text-white tabular-nums text-right">
                    {entry.edge_percent !== null
                        ? `+${entry.edge_percent.toFixed(1)}%`
                        : "—"}
                </div>
                <div className="col-span-4 sm:col-span-3 text-right">
                    <span
                        className={
                            "inline-block text-[10px] uppercase tracking-wider px-2 py-1 rounded border font-mono " +
                            STATUS_COLOR[entry.status]
                        }
                    >
                        {STATUS_LABEL[entry.status]}
                        {entry.actual_result && entry.status !== "pending"
                            ? ` (${entry.actual_result})`
                            : ""}
                    </span>
                </div>
            </div>
        </Link>
    );
}

export default async function ValueBetLedgerPage({ searchParams }: PageProps) {
    const sp = await searchParams;
    const status = sp.status ?? "all";

    let ledger: ValueBetLedger;
    try {
        ledger = await fetchApi<ValueBetLedger>(
            `/api/v1/value-bets/ledger?status=${encodeURIComponent(status)}&limit=200`,
        );
    } catch {
        ledger = {
            total: 0,
            win_count: 0,
            loss_count: 0,
            pending_count: 0,
            win_rate_percent: 0,
            avg_edge_percent: null,
            entries: [],
        };
    }

    const filters = ["all", "win", "loss", "pending"] as const;

    return (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <header className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2">
                    Value-bet ledger
                </h1>
                <p className="text-sm text-gray-400 max-w-2xl">
                    Vi visar alla tips, även förlorarna. Trust by transparency.
                </p>
                <p className="text-xs text-gray-500 mt-3 max-w-2xl border-l-2 border-yellow-500/40 pl-3">
                    Modellens tips är inte spelråd. Vi loggar alla tips öppet —
                    vinster och förluster — så du själv kan bedöma kvalitén.
                </p>
            </header>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                <StatBox label="Totalt" value={ledger.total.toString()} />
                <StatBox
                    label="Träffsäkerhet"
                    value={`${ledger.win_rate_percent.toFixed(1)}%`}
                    hint={`${ledger.win_count}V / ${ledger.loss_count}F / ${ledger.pending_count}V`}
                />
                <StatBox
                    label="Snitt-edge"
                    value={
                        ledger.avg_edge_percent !== null
                            ? `+${ledger.avg_edge_percent.toFixed(1)}%`
                            : "—"
                    }
                />
                <StatBox
                    label="Modell"
                    value="v20260210"
                    hint="ML XGBoost"
                />
            </div>

            <div className="card mb-6 flex gap-2 flex-wrap">
                {filters.map((f) => (
                    <Link
                        key={f}
                        href={`/value-bets/ledger?status=${f}`}
                        className={
                            "px-3 py-1.5 text-xs rounded font-mono uppercase tracking-wider transition-colors " +
                            (status === f
                                ? "bg-scorelock-500 text-black"
                                : "bg-white/[0.04] text-gray-400 hover:bg-white/[0.08]")
                        }
                    >
                        {f === "all"
                            ? "Alla"
                            : f === "win"
                              ? "Vinster"
                              : f === "loss"
                                ? "Förluster"
                                : "Väntande"}
                    </Link>
                ))}
            </div>

            {ledger.entries.length === 0 ? (
                <div className="card text-center text-gray-400 py-12">
                    Inga value-bets registrerade ännu
                </div>
            ) : (
                <div className="card !p-0 overflow-hidden">
                    <div className="grid grid-cols-12 gap-3 py-3 px-4 text-xs uppercase tracking-wider text-gray-500 border-b border-white/[0.06] bg-white/[0.02]">
                        <div className="col-span-12 sm:col-span-5">Match</div>
                        <div className="col-span-4 sm:col-span-2">Tips</div>
                        <div className="col-span-4 sm:col-span-2 text-right">
                            Edge
                        </div>
                        <div className="col-span-4 sm:col-span-3 text-right">
                            Utfall
                        </div>
                    </div>
                    {ledger.entries.map((e) => (
                        <LedgerRow key={e.prediction_id} entry={e} />
                    ))}
                </div>
            )}
        </div>
    );
}

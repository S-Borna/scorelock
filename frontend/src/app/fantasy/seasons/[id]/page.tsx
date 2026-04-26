import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { fetchApi } from "@/lib/api";
import type { FantasyGameweek, FantasySeasonDetail } from "@/lib/types";

interface PageProps {
    params: Promise<{ id: string }>;
}

export async function generateMetadata({
    params,
}: PageProps): Promise<Metadata> {
    const { id } = await params;
    try {
        const s = await fetchApi<FantasySeasonDetail>(
            `/api/v1/fantasy/seasons/${id}`,
        );
        return { title: `${s.name} — Tipsligan` };
    } catch {
        return { title: "Tipsligan-säsong" };
    }
}

function formatDateTime(iso: string): string {
    const d = new Date(iso);
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    const hh = String(d.getHours()).padStart(2, "0");
    const mi = String(d.getMinutes()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd} ${hh}:${mi}`;
}

function formatBudget(units: number): string {
    return `€${(units / 10).toFixed(1)}M`;
}

export default async function SeasonOverview({ params }: PageProps) {
    const { id } = await params;
    let season: FantasySeasonDetail;
    try {
        season = await fetchApi<FantasySeasonDetail>(
            `/api/v1/fantasy/seasons/${id}`,
        );
    } catch {
        notFound();
    }

    let currentGw: FantasyGameweek | null = null;
    try {
        currentGw = await fetchApi<FantasyGameweek | null>(
            `/api/v1/fantasy/seasons/${id}/current-gw`,
        );
    } catch { /* not critical */ }

    return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <nav className="text-sm text-gray-500 mb-6">
                <Link href="/fantasy" className="hover:text-gray-300">
                    Tipsligan
                </Link>
                <span className="mx-2">›</span>
                <span>{season.name}</span>
            </nav>

            <header className="mb-8">
                <h1 className="text-2xl font-bold text-white mb-2">{season.name}</h1>
                <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-400">
                    <div>
                        <span className="text-gray-500">Budget:</span>{" "}
                        <span className="text-white font-mono">
                            {formatBudget(season.total_budget_units)}
                        </span>
                    </div>
                    <div>
                        <span className="text-gray-500">Omgångar:</span>{" "}
                        <span className="text-white font-mono">
                            {season.gameweeks.length}
                        </span>
                    </div>
                    <div>
                        <span className="text-gray-500">Säsong:</span>{" "}
                        <span className="text-white font-mono">
                            {season.start_date} → {season.end_date}
                        </span>
                    </div>
                </div>
            </header>

            <div className="mb-8 flex flex-wrap gap-3">
                <Link
                    href={`/fantasy/seasons/${id}/team`}
                    className="inline-flex items-center px-4 py-2 bg-scorelock-500 text-black rounded font-semibold hover:bg-scorelock-400 transition-colors"
                >
                    Mitt lag →
                </Link>
                <Link
                    href={`/fantasy/seasons/${id}/players`}
                    className="inline-flex items-center px-4 py-2 bg-white/[0.04] text-white rounded hover:bg-white/[0.08] transition-colors"
                >
                    Spelarmarknad
                </Link>
            </div>

            {currentGw && (
                <div className="card mb-6">
                    <h2 className="text-base font-semibold mb-3 text-white">
                        ⏱ Nästa omgång
                    </h2>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <div className="text-gray-500 text-xs uppercase tracking-wider">
                                Omgång
                            </div>
                            <div className="text-white font-mono text-lg">
                                {currentGw.gameweek_number}
                            </div>
                        </div>
                        <div>
                            <div className="text-gray-500 text-xs uppercase tracking-wider">
                                Deadline
                            </div>
                            <div className="text-white font-mono">
                                {formatDateTime(currentGw.deadline_at)}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="card">
                <h2 className="text-base font-semibold mb-3 text-white">
                    Alla omgångar
                </h2>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-left text-xs text-gray-500 uppercase tracking-wider border-b border-white/[0.06]">
                                <th className="py-2">#</th>
                                <th className="py-2">Deadline</th>
                                <th className="py-2">Avspark</th>
                                <th className="py-2 text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {season.gameweeks.map((gw) => (
                                <tr
                                    key={gw.id}
                                    className="border-b border-white/[0.04] last:border-0"
                                >
                                    <td className="py-2 font-mono text-white">
                                        {gw.gameweek_number}
                                    </td>
                                    <td className="py-2 text-gray-300 font-mono">
                                        {formatDateTime(gw.deadline_at)}
                                    </td>
                                    <td className="py-2 text-gray-300 font-mono">
                                        {formatDateTime(gw.first_kickoff_at)}
                                    </td>
                                    <td className="py-2 text-right">
                                        <span
                                            className={
                                                "text-xs font-mono " +
                                                (gw.is_finalized
                                                    ? "text-gray-500"
                                                    : "text-scorelock-400")
                                            }
                                        >
                                            {gw.is_finalized
                                                ? "Slutförd"
                                                : "Kommande"}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { fetchApi } from "@/lib/api";
import type {
    FantasyPlayerMarketBundle,
    FantasySeasonDetail,
} from "@/lib/types";
import { PlayerMarketCard } from "@/components/player-market-card";
import { PlayerMarketFilters } from "@/components/player-market-filters";

interface PageProps {
    params: Promise<{ id: string }>;
    searchParams: Promise<{
        position?: string;
        sort?: string;
        max_price?: string;
    }>;
}

export const metadata: Metadata = {
    title: "Spelarmarknad — Tipsligan",
    description: "Bläddra alla spelare med priser, ägarskap och poäng.",
};

export default async function PlayerMarket({
    params,
    searchParams,
}: PageProps) {
    const { id } = await params;
    const sp = await searchParams;

    let season: FantasySeasonDetail;
    try {
        season = await fetchApi<FantasySeasonDetail>(
            `/api/v1/fantasy/seasons/${id}`,
        );
    } catch {
        notFound();
    }

    const query = new URLSearchParams();
    query.set("limit", "100");
    if (sp.sort) query.set("sort", sp.sort);
    if (sp.position && sp.position !== "all") query.set("position", sp.position);
    if (sp.max_price) query.set("max_price", sp.max_price);

    let market: FantasyPlayerMarketBundle = {
        season_id: Number(id),
        total_count: 0,
        players: [],
    };
    try {
        market = await fetchApi<FantasyPlayerMarketBundle>(
            `/api/v1/fantasy/seasons/${id}/players?${query.toString()}`,
        );
    } catch { /* fall through to empty state */ }

    return (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <nav className="text-sm text-gray-500 mb-6">
                <Link href="/fantasy" className="hover:text-gray-300">
                    Tipsligan
                </Link>
                <span className="mx-2">›</span>
                <Link
                    href={`/fantasy/seasons/${id}`}
                    className="hover:text-gray-300"
                >
                    {season.name}
                </Link>
                <span className="mx-2">›</span>
                <span>Spelarmarknad</span>
            </nav>

            <header className="mb-6">
                <h1 className="text-2xl font-bold text-white mb-1">
                    Spelarmarknad
                </h1>
                <p className="text-sm text-gray-500">
                    {market.total_count} spelare
                </p>
            </header>

            <PlayerMarketFilters seasonId={Number(id)} />

            {market.players.length === 0 ? (
                <div className="card text-center text-gray-400 py-12">
                    Inga spelare matchar filtret
                </div>
            ) : (
                <div className="space-y-2">
                    {market.players.map((p) => (
                        <PlayerMarketCard key={p.player_id} entry={p} />
                    ))}
                </div>
            )}
        </div>
    );
}

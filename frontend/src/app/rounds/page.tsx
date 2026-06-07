import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Omgångar — Tabeller per liga",
    description: "Välj liga för att se aktuell omgång, tabell och kommande matcher.",
};

const LEAGUES = [
    { slug: "allsvenskan", name: "Allsvenskan", country: "Sverige", emoji: "🇸🇪" },
    { slug: "premier-league", name: "Premier League", country: "England", emoji: "🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
    { slug: "la-liga", name: "La Liga", country: "Spanien", emoji: "🇪🇸" },
    { slug: "serie-a", name: "Serie A", country: "Italien", emoji: "🇮🇹" },
];

export default function RoundsPage() {
    return (
        <div className="container-main py-10">
            <header className="mb-10">
                <h1 className="font-display text-display-lg sm:text-display-xl leading-tight mb-3">
                    Omgångar
                </h1>
                <p className="text-gray-400 text-base sm:text-lg max-w-2xl">
                    Välj liga för att se aktuell omgång, tabell och kommande matcher.
                </p>
            </header>

            <div className="grid gap-4 sm:grid-cols-2">
                {LEAGUES.map((league) => (
                    <Link
                        key={league.slug}
                        href={`/rounds/${league.slug}`}
                        className="card-interactive group flex items-center justify-between"
                    >
                        <div className="flex items-center gap-4">
                            <span className="text-3xl">{league.emoji}</span>
                            <div>
                                <h2 className="font-semibold text-lg text-white group-hover:text-scorelock-400 transition-colors">
                                    {league.name}
                                </h2>
                                <p className="text-sm text-gray-500">{league.country}</p>
                            </div>
                        </div>
                        <span className="text-gray-500 group-hover:text-scorelock-400 transition-colors">
                            →
                        </span>
                    </Link>
                ))}
            </div>
        </div>
    );
}

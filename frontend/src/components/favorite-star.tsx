"use client";

import { useFavorite } from "@/lib/favorites";

/**
 * Stjärn-knapp som markerar en match som favorit (localStorage, ingen backend).
 * Stoppar klick-propagering så den kan ligga inuti en länk-rad utan att navigera.
 */
export function FavoriteStar({
    fixtureId,
    className = "",
}: {
    fixtureId: number;
    className?: string;
}) {
    const [isFav, toggle] = useFavorite(fixtureId);
    return (
        <button
            type="button"
            onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                toggle();
            }}
            aria-label={isFav ? "Ta bort från Mina matcher" : "Lägg till i Mina matcher"}
            aria-pressed={isFav}
            className={`shrink-0 text-base leading-none transition-transform hover:scale-125 ${isFav ? "text-yellow-400" : "text-gray-600 hover:text-gray-400"} ${className}`}
        >
            {isFav ? "★" : "☆"}
        </button>
    );
}

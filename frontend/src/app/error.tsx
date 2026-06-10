"use client";

/**
 * Global error-boundary — fångar render/fetch-fel så Next ALDRIG cachar en
 * tom sida som ISR-state. Vid revalidering som kastar behåller Next den
 * senaste lyckade versionen; boundaryn syns bara vid kallstart utan data.
 */
export default function GlobalError({
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    return (
        <div className="min-h-[70vh] flex items-center justify-center px-4">
            <div className="text-center max-w-sm">
                <p className="text-5xl mb-5">⚽</p>
                <h1 className="font-serif text-2xl mb-2 text-white">
                    Datan värmer upp
                </h1>
                <p className="text-sm text-gray-400 mb-6">
                    Vi hämtar det senaste från VM just nu — försök igen om en
                    sekund.
                </p>
                <button onClick={() => reset()} className="btn-primary text-sm">
                    Ladda om
                </button>
            </div>
        </div>
    );
}

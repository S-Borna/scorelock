"use client";

export default function GlobalError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    return (
        <html lang="sv">
            <body className="bg-gray-950 text-white">
                <div className="min-h-screen flex items-center justify-center px-4">
                    <div className="text-center">
                        <h1 className="text-4xl font-bold text-red-500 mb-4">Något gick fel</h1>
                        <p className="text-gray-400 mb-6">
                            Ett oväntat fel inträffade. Försök igen.
                        </p>
                        <button
                            onClick={reset}
                            className="bg-scorelock-600 hover:bg-scorelock-700 text-white font-semibold px-6 py-3 rounded-lg transition"
                        >
                            Försök igen
                        </button>
                    </div>
                </div>
            </body>
        </html>
    );
}

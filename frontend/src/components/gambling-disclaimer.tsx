/**
 * Responsible gambling disclaimer — shown on all pages with odds or betting content.
 * Required by Swedish gambling regulation (Spelinspektionen).
 */
export function GamblingDisclaimer({ compact = false }: { compact?: boolean }) {
    if (compact) {
        return (
            <p className="text-[10px] text-gray-600">
                Reklamlänk · 18+ · Spela ansvarsfullt ·{" "}
                <a
                    href="https://www.stodlinjen.se"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline hover:text-gray-500"
                >
                    Stödlinjen: 020-819 100
                </a>
            </p>
        );
    }

    return (
        <div className="card bg-gray-900/50 border-gray-800">
            <div className="flex items-start gap-3">
                <span className="text-xl flex-shrink-0">⚠️</span>
                <div>
                    <p className="text-sm text-gray-300 font-medium mb-1">
                        Spela ansvarsfullt
                    </p>
                    <p className="text-xs text-gray-500 leading-relaxed">
                        Spel om pengar kan vara beroendeframkallande. Spela aldrig för mer
                        än du har råd att förlora. Du måste vara minst 18 år för att
                        spela. Vissa länkar på denna sida är reklamlänkar till
                        licensierade spelbolag.
                    </p>
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-xs">
                        <a
                            href="https://www.stodlinjen.se"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-scorelock-400 hover:underline"
                        >
                            📞 Stödlinjen: 020-819 100
                        </a>
                        <a
                            href="https://www.spelpaus.se"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-scorelock-400 hover:underline"
                        >
                            🛑 Spelpaus.se
                        </a>
                        <span className="text-gray-600">18+</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

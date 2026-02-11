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
                    className="underline underline-offset-2 hover:text-gray-500 transition-colors"
                >
                    Stödlinjen: 020-819 100
                </a>
            </p>
        );
    }

    return (
        <div className="card bg-white/[0.01] border-white/[0.04]">
            <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-accent-amber/10 flex items-center justify-center text-base flex-shrink-0">
                    ⚠️
                </div>
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
                    <div className="flex flex-wrap items-center gap-3 mt-3 text-xs">
                        <a
                            href="https://www.stodlinjen.se"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-scorelock-400 hover:text-scorelock-300 transition-colors"
                        >
                            📞 Stödlinjen: 020-819 100
                        </a>
                        <a
                            href="https://www.spelpaus.se"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-scorelock-400 hover:text-scorelock-300 transition-colors"
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

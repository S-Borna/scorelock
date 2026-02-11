"use client";

import { useCallback } from "react";

export interface AffiliateLink {
    id: number;
    bookmaker: string;
    bookmaker_display: string;
    logo_url: string | null;
    base_url: string;
    tracking_id: string | null;
    market: string;
    country: string;
    priority: number;
}

interface AffiliateCTAProps {
    links: AffiliateLink[];
    fixtureId?: number;
    pageSource: string;
    variant?: "inline" | "card" | "banner";
}

/**
 * Affiliate CTA component — shows bookmaker links with click tracking.
 * Before redirecting, fires a POST to /api/v1/affiliate/click.
 */
export function AffiliateCTA({ links, fixtureId, pageSource, variant = "card" }: AffiliateCTAProps) {
    const handleClick = useCallback(async (link: AffiliateLink) => {
        try {
            await fetch("/api/v1/affiliate/click", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    link_id: link.id,
                    fixture_id: fixtureId || null,
                    page_source: pageSource,
                }),
            });
        } catch {
            // Non-blocking — don't prevent redirect if tracking fails
        }
    }, [fixtureId, pageSource]);

    if (links.length === 0) return null;

    if (variant === "banner") {
        return (
            <div className="card border-scorelock-800/50 bg-gradient-to-r from-scorelock-950/50 to-gray-900">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div>
                        <p className="text-sm font-semibold text-scorelock-400">
                            📊 Jämför odds hos licensierade spelbolag
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                            Reklamlänk · 18+ · Spela ansvarsfullt
                        </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {links.slice(0, 3).map((link) => (
                            <a
                                key={link.id}
                                href={link.base_url}
                                target="_blank"
                                rel="noopener noreferrer nofollow sponsored"
                                onClick={() => handleClick(link)}
                                className="inline-flex items-center gap-1.5 bg-scorelock-700 hover:bg-scorelock-600 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
                            >
                                {link.bookmaker_display} →
                            </a>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    if (variant === "inline") {
        return (
            <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="text-gray-500">Odds hos:</span>
                {links.slice(0, 3).map((link) => (
                    <a
                        key={link.id}
                        href={link.base_url}
                        target="_blank"
                        rel="noopener noreferrer nofollow sponsored"
                        onClick={() => handleClick(link)}
                        className="text-scorelock-400 hover:text-scorelock-300 underline decoration-dotted"
                    >
                        {link.bookmaker_display}
                    </a>
                ))}
                <span className="text-gray-600 text-[10px]">Reklamlänk · 18+</span>
            </div>
        );
    }

    // Default: card variant
    return (
        <div className="card border-green-900/30">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">
                🏆 Bästa odds hos licensierade spelbolag
            </h3>
            <div className="grid gap-2 sm:grid-cols-2">
                {links.map((link) => (
                    <a
                        key={link.id}
                        href={link.base_url}
                        target="_blank"
                        rel="noopener noreferrer nofollow sponsored"
                        onClick={() => handleClick(link)}
                        className="flex items-center justify-between p-3 rounded-lg bg-gray-800/50 hover:bg-gray-800 border border-gray-700/50 hover:border-green-800/50 transition-all group"
                    >
                        <span className="font-medium text-sm group-hover:text-green-400 transition-colors">
                            {link.bookmaker_display}
                        </span>
                        <span className="text-xs text-gray-500 group-hover:text-green-400 transition-colors">
                            Besök →
                        </span>
                    </a>
                ))}
            </div>
            <p className="text-[10px] text-gray-600 mt-3 text-center">
                Reklamlänk · 18+ · Spela ansvarsfullt · Stödlinjen: 020-819 100
            </p>
        </div>
    );
}

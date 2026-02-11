"use client";

import { useLocale } from "@/components/locale-provider";

/**
 * Compact language toggle — 🇸🇪 / 🇬🇧 flag button.
 * Persists choice to localStorage.
 */
export function LanguageToggle() {
    const { locale, setLocale } = useLocale();

    return (
        <button
            onClick={() => setLocale(locale === "sv" ? "en" : "sv")}
            className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-xs font-medium text-gray-400 hover:text-white hover:bg-white/[0.05] transition-all duration-150"
            title={locale === "sv" ? "Switch to English" : "Byt till svenska"}
            aria-label={locale === "sv" ? "Switch to English" : "Byt till svenska"}
        >
            <span className="text-base leading-none">{locale === "sv" ? "🇸🇪" : "🇬🇧"}</span>
            <span className="hidden sm:inline uppercase">{locale === "sv" ? "SV" : "EN"}</span>
        </button>
    );
}

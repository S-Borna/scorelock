import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with conflict resolution.
 */
export function cn(...inputs: ClassValue[]): string {
    return twMerge(clsx(inputs));
}

/**
 * Format a probability as a percentage string.
 */
export function formatProb(prob: number): string {
    return `${(prob * 100).toFixed(1)}%`;
}

/**
 * Format a date string for display (Swedish locale).
 */
export function formatKickoff(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString("sv-SE", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        // Fast tidszon → server (UTC) och klient (lokal) ger identisk sträng,
        // annars hydration-mismatch för matcher nära dygnsgränsen.
        timeZone: "Europe/Stockholm",
    });
}

/**
 * Format a date as relative time (e.g. "2 timmar sedan").
 */
export function timeAgo(dateStr: string): string {
    const now = Date.now();
    const then = new Date(dateStr).getTime();
    const diff = now - then;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return "just nu";
    if (minutes < 60) return `${minutes} min sedan`;
    if (hours < 24) return `${hours} tim sedan`;
    if (days < 7) return `${days} dagar sedan`;
    return new Date(dateStr).toLocaleDateString("sv-SE", { day: "numeric", month: "short", timeZone: "Europe/Stockholm" });
}

/**
 * Get status badge styling class.
 */
export function getStatusClass(status: string): string {
    switch (status) {
        case "live":
        case "halftime":
            return "badge-live";
        case "scheduled":
            return "badge-scheduled";
        default:
            return "badge-finished";
    }
}

/**
 * Article type display names and icons (Swedish).
 */
export const ARTICLE_TYPE_META: Record<string, { label: string; icon: string; color: string }> = {
    MATCH_PREVIEW: { label: "Förhandsanalys", icon: "🔮", color: "text-blue-400" },
    MATCH_REPORT: { label: "Matchreferat", icon: "📝", color: "text-green-400" },
    ROUND_SUMMARY: { label: "Omgångssammanfattning", icon: "📊", color: "text-purple-400" },
    VALUE_BET_ALERT: { label: "Value Bet", icon: "💰", color: "text-yellow-400" },
    NEWS_REWRITE: { label: "Nyhet", icon: "📰", color: "text-orange-400" },
};

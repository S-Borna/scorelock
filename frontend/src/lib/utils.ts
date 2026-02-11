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
 * Format a date string for display.
 */
export function formatKickoff(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString("sv-SE", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
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

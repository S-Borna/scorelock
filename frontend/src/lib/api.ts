/**
 * API client for ScoreLock backend.
 * Vid fel bubblar felet — anroparen visar tom-/fel-state. INGEN mock-fallback:
 * fabricerad data (fejk-matcher/tabeller) är värre än ärlig tomhet.
 */

// SSR (inside frontend container) reaches backend via docker-network hostname.
// Browser (on user's host) reaches backend via mapped localhost port.
// Both can be overridden via env vars in prod.
const API_BASE =
    typeof window === "undefined"
        ? process.env.INTERNAL_API_URL || "http://backend:8000"
        : process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
    constructor(
        public status: number,
        message: string,
    ) {
        super(message);
        this.name = "ApiError";
    }
}

export async function fetchApi<T>(
    path: string,
    options?: RequestInit,
): Promise<T> {
    const url = `${API_BASE}${path}`;

    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 8000);

        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                "Content-Type": "application/json",
                ...options?.headers,
            },
        });

        clearTimeout(timeout);

        if (!response.ok) {
            const body = await response.text();
            throw new ApiError(response.status, body);
        }

        return response.json();
    } catch (error) {
        // Ingen mock-fallback: låt felet bubbla så anroparen visar tom-/fel-state
        // i stället för fabricerade matcher/tabeller.
        throw error;
    }
}

export async function fetchApiAuth<T>(
    path: string,
    token: string,
    options?: RequestInit,
): Promise<T> {
    return fetchApi<T>(path, {
        ...options,
        headers: {
            Authorization: `Bearer ${token}`,
            ...options?.headers,
        },
    });
}

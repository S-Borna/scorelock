/**
 * API client for ScoreLock backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options?.headers,
        },
    });

    if (!response.ok) {
        const body = await response.text();
        throw new ApiError(response.status, body);
    }

    return response.json();
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

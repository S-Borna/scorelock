/**
 * API client for ScoreLock backend.
 * Falls back to mock data when the backend is unreachable (offline dev mode).
 */

import { getMockData } from "./mock-data";

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

    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 3000);

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
        // If backend is unreachable, try mock data
        const mock = getMockData(path);
        if (mock !== null) {
            console.log(`[ScoreLock] API offline — using mock data for ${path}`);
            return mock as T;
        }
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

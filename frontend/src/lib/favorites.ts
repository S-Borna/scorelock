"use client";

import { useCallback, useEffect, useState } from "react";

const KEY = "scorelock:favorites";
const EVENT = "scorelock:favorites-changed";

function read(): Set<number> {
    if (typeof window === "undefined") return new Set();
    try {
        const raw = localStorage.getItem(KEY);
        const arr = raw ? (JSON.parse(raw) as unknown) : [];
        return new Set(Array.isArray(arr) ? (arr as number[]) : []);
    } catch {
        return new Set();
    }
}

function write(s: Set<number>): void {
    localStorage.setItem(KEY, JSON.stringify([...s]));
    // Synka alla useFavorites-instanser i samma flik (storage-eventet fyrar bara
    // i ANDRA flikar) + andra flikar via det inbyggda storage-eventet.
    window.dispatchEvent(new Event(EVENT));
}

export function toggleFavorite(id: number): void {
    const s = read();
    if (s.has(id)) s.delete(id);
    else s.add(id);
    write(s);
}

/** Reaktiv mängd favorit-fixture-ids, synkad över komponenter och flikar. */
export function useFavorites(): Set<number> {
    const [favs, setFavs] = useState<Set<number>>(() => new Set());
    useEffect(() => {
        const sync = () => setFavs(read());
        sync(); // hämta efter mount → undviker hydration-mismatch (SSR = tom)
        window.addEventListener(EVENT, sync);
        window.addEventListener("storage", sync);
        return () => {
            window.removeEventListener(EVENT, sync);
            window.removeEventListener("storage", sync);
        };
    }, []);
    return favs;
}

export function useFavorite(id: number): [boolean, () => void] {
    const favs = useFavorites();
    const toggle = useCallback(() => toggleFavorite(id), [id]);
    return [favs.has(id), toggle];
}

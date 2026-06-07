"use client";

import { setAccessToken } from "@/lib/auth-token";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/login`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password }),
                }
            );

            if (!res.ok) {
                const data = await res.json().catch(() => null);
                // Pydantic-validation kommer som array — extract msg så användaren ser något läsbart
                const detail = data?.detail;
                const msg = Array.isArray(detail)
                    ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ")
                    : typeof detail === "string"
                      ? detail
                      : "Invalid credentials";
                throw new Error(msg || "Invalid credentials");
            }

            const data = await res.json();
            setAccessToken(data.access_token);
            router.push("/");
            router.refresh();
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Login failed");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="min-h-[calc(100vh-200px)] flex items-center justify-center px-4">
            <div className="card max-w-md w-full p-8 shadow-elevated">
                <h1 className="text-display-sm text-center mb-8">Logga in</h1>

                {error && (
                    <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg px-4 py-3 mb-4">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-400 mb-1">
                            E-post
                        </label>
                        <input
                            id="email"
                            type="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="input"
                            placeholder="you@example.com"
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="block text-sm font-medium text-gray-400 mb-1">
                            Lösenord
                        </label>
                        <input
                            id="password"
                            type="password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="input"
                            placeholder="••••••••"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? "Loggar in…" : "Logga in"}
                    </button>
                </form>

                <p className="text-center text-sm text-gray-500 mt-6">
                    Har du inget konto?{" "}
                    <Link href="/signup" className="text-scorelock-400 hover:underline">
                        Skapa konto
                    </Link>
                </p>
            </div>
        </div>
    );
}

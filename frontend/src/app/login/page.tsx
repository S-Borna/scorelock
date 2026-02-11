"use client";

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
                    headers: { "Content-Type": "application/x-www-form-urlencoded" },
                    body: new URLSearchParams({ username: email, password }),
                }
            );

            if (!res.ok) {
                const data = await res.json().catch(() => null);
                throw new Error(data?.detail || "Invalid credentials");
            }

            const data = await res.json();
            localStorage.setItem("access_token", data.access_token);
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
            <div className="card max-w-md w-full p-8">
                <h1 className="text-2xl font-bold text-center mb-6">Logga in</h1>

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
                            className="w-full rounded-lg bg-gray-800 border border-gray-700 px-4 py-2.5 text-white placeholder-gray-500 focus:border-scorelock-500 focus:ring-1 focus:ring-scorelock-500 outline-none"
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
                            className="w-full rounded-lg bg-gray-800 border border-gray-700 px-4 py-2.5 text-white placeholder-gray-500 focus:border-scorelock-500 focus:ring-1 focus:ring-scorelock-500 outline-none"
                            placeholder="••••••••"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-scorelock-600 hover:bg-scorelock-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-lg transition"
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

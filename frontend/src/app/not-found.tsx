import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Sidan hittades inte",
};

export default function NotFound() {
    return (
        <div className="min-h-[calc(100vh-200px)] flex items-center justify-center px-4">
            <div className="text-center">
                <h1 className="text-6xl font-bold text-scorelock-500 mb-4">404</h1>
                <h2 className="text-2xl font-semibold mb-2">Sidan hittades inte</h2>
                <p className="text-gray-500 mb-8">
                    Sidan du söker finns inte eller har flyttats.
                </p>
                <Link
                    href="/"
                    className="inline-block bg-scorelock-600 hover:bg-scorelock-700 text-white font-semibold px-6 py-3 rounded-lg transition"
                >
                    Tillbaka till startsidan
                </Link>
            </div>
        </div>
    );
}

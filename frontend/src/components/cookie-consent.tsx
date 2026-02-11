"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const COOKIE_KEY = "scorelock_cookie_consent";

export function CookieConsent() {
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        const consent = localStorage.getItem(COOKIE_KEY);
        if (!consent) {
            // Small delay so it doesn't flash on page load
            const timer = setTimeout(() => setVisible(true), 1000);
            return () => clearTimeout(timer);
        }
    }, []);

    function accept() {
        localStorage.setItem(COOKIE_KEY, "accepted");
        setVisible(false);
    }

    function decline() {
        localStorage.setItem(COOKIE_KEY, "declined");
        setVisible(false);
    }

    if (!visible) return null;

    return (
        <div className="fixed bottom-0 inset-x-0 z-50 p-4">
            <div className="max-w-3xl mx-auto bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6 shadow-2xl">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                    <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-300 leading-relaxed">
                            🍪 Vi använder cookies för att förbättra din upplevelse. Vi lagrar{" "}
                            <strong className="text-white">ingen</strong> persondata i cookies
                            — bara nödvändiga session-cookies.{" "}
                            <Link
                                href="/privacy"
                                className="text-scorelock-400 hover:underline"
                            >
                                Läs mer →
                            </Link>
                        </p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                        <button
                            onClick={decline}
                            className="px-4 py-2 text-sm text-gray-400 hover:text-white border border-gray-700 rounded-lg transition-colors"
                        >
                            Avböj
                        </button>
                        <button
                            onClick={accept}
                            className="px-4 py-2 text-sm font-medium text-white bg-scorelock-600 hover:bg-scorelock-500 rounded-lg transition-colors"
                        >
                            Acceptera
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

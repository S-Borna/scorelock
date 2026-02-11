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
        <div className="fixed bottom-0 inset-x-0 z-50 p-4 animate-fade-up">
            <div className="max-w-3xl mx-auto glass-strong rounded-2xl p-5 sm:p-6 shadow-elevated">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                    <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-300 leading-relaxed">
                            Vi använder cookies för att förbättra din upplevelse. Vi lagrar{" "}
                            <strong className="text-white">ingen</strong> persondata i cookies
                            — bara nödvändiga session-cookies.{" "}
                            <Link
                                href="/privacy"
                                className="text-scorelock-400 hover:text-scorelock-300 underline underline-offset-2 decoration-scorelock-500/30 transition-colors"
                            >
                                Läs mer →
                            </Link>
                        </p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                        <button
                            onClick={decline}
                            className="btn-ghost text-sm"
                        >
                            Avböj
                        </button>
                        <button
                            onClick={accept}
                            className="btn-primary text-sm"
                        >
                            Acceptera
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

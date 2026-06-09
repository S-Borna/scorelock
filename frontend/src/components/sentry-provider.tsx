"use client";

import { useEffect } from "react";

/**
 * Lättviktig frontend-error-reporter — POST:ar window.onerror +
 * unhandledrejection till backend /api/v1/client-errors, som vidarebefordrar
 * till Sentry (backend-SDK:t är redan i drift). Inget eget Sentry-SDK i
 * frontend: @sentry/nextjs mot Next 16 är oprövat så nära launch, och
 * symbolication kan vänta — synlighet kan inte.
 *
 * Skydd: dedupe per meddelande + max 10 rapporter per sidladdning så en
 * error-loop aldrig spammar backend.
 */

const MAX_REPORTS_PER_PAGE = 10;

export function SentryProvider({ children }: { children: React.ReactNode }) {
    useEffect(() => {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || "";
        const seen = new Set<string>();
        let sent = 0;

        function report(message: string, stack?: string) {
            if (sent >= MAX_REPORTS_PER_PAGE) return;
            const key = message.slice(0, 200);
            if (seen.has(key)) return;
            seen.add(key);
            sent += 1;

            const payload = JSON.stringify({
                message: message.slice(0, 500),
                stack: (stack || "").slice(0, 2000),
                url: window.location.href.slice(0, 300),
            });
            // sendBeacon överlever sidnavigering; fetch som fallback
            try {
                const endpoint = `${apiBase}/api/v1/client-errors`;
                if (navigator.sendBeacon) {
                    navigator.sendBeacon(
                        endpoint,
                        new Blob([payload], { type: "application/json" }),
                    );
                } else {
                    void fetch(endpoint, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: payload,
                        keepalive: true,
                    });
                }
            } catch {
                // rapporterings-fel ska aldrig påverka appen
            }
        }

        const onError = (event: ErrorEvent) => {
            report(
                event.message || "Unknown error",
                event.error instanceof Error ? event.error.stack : undefined,
            );
        };
        const onRejection = (event: PromiseRejectionEvent) => {
            const reason = event.reason;
            report(
                reason instanceof Error
                    ? `Unhandled rejection: ${reason.message}`
                    : `Unhandled rejection: ${String(reason).slice(0, 300)}`,
                reason instanceof Error ? reason.stack : undefined,
            );
        };

        window.addEventListener("error", onError);
        window.addEventListener("unhandledrejection", onRejection);
        return () => {
            window.removeEventListener("error", onError);
            window.removeEventListener("unhandledrejection", onRejection);
        };
    }, []);

    return <>{children}</>;
}

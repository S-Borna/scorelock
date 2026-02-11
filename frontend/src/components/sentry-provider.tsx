"use client";

import * as Sentry from "@sentry/react";
import { useEffect } from "react";

let initialized = false;

export function SentryProvider({ children }: { children: React.ReactNode }) {
    useEffect(() => {
        const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
        if (dsn && !initialized) {
            Sentry.init({
                dsn,
                tracesSampleRate: 0.2,
                environment: process.env.NODE_ENV,
                release: "scorelock-frontend@0.1.0",
                // Don't send PII
                sendDefaultPii: false,
            });
            initialized = true;
        }
    }, []);

    return <>{children}</>;
}

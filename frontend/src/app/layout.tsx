import { CookieConsent } from "@/components/cookie-consent";
import { Header, Footer } from "@/components/layout-shell";
import { LocaleProvider } from "@/components/locale-provider";
import { SentryProvider } from "@/components/sentry-provider";
import type { Metadata } from "next";
import { Fraunces, Schibsted_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// Nordisk intelligens-editorial: karaktärsfull display-serif + skandinavisk
// grotesk-body + mono för data — bort från generiska Inter.
const display = Fraunces({
    subsets: ["latin"],
    variable: "--font-display",
    display: "swap",
});

const sans = Schibsted_Grotesk({
    subsets: ["latin"],
    variable: "--font-sans",
    display: "swap",
});

const mono = JetBrains_Mono({
    subsets: ["latin"],
    variable: "--font-mono",
    display: "swap",
});

export const metadata: Metadata = {
    metadataBase: new URL("https://scorelock.saidborna.com"),
    title: {
        default: "ScoreLock — AI-driven fotbollsanalys",
        template: "%s | ScoreLock",
    },
    description:
        "AI-genererade förhandsanalyser, matchreferat, value bets och prediktioner för fotboll. Driven av maskininlärning.",
    keywords: [
        "fotboll", "prediktioner", "analys", "betting", "value bets", "AI", "maskininlärning",
        "football", "predictions", "analytics", "machine learning",
    ],
    openGraph: {
        type: "website",
        locale: "sv_SE",
        alternateLocale: "en_GB",
        url: "/",
        siteName: "ScoreLock",
        title: "ScoreLock — AI-driven fotbollsanalys",
        description: "AI-genererade förhandsanalyser, matchreferat, value bets och prediktioner.",
    },
    twitter: {
        card: "summary_large_image",
        title: "ScoreLock — AI-driven fotbollsanalys",
        description: "AI-genererade förhandsanalyser, matchreferat, value bets och prediktioner.",
    },
    robots: { index: true, follow: true },
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="sv" className="dark">
            <body className={`${display.variable} ${sans.variable} ${mono.variable} font-sans bg-surface text-gray-100 antialiased`}>
                <div className="min-h-screen flex flex-col">
                    <SentryProvider>
                        <LocaleProvider>
                            <Header />
                            <main className="flex-1">{children}</main>
                            <Footer />
                            <CookieConsent />
                        </LocaleProvider>
                    </SentryProvider>
                </div>
            </body>
        </html>
    );
}

import { CookieConsent } from "@/components/cookie-consent";
import { SentryProvider } from "@/components/sentry-provider";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: {
        default: "ScoreLock — AI-driven fotbollsanalys",
        template: "%s | ScoreLock",
    },
    description:
        "AI-genererade förhandsanalyser, matchreferat, value bets och prediktioner för fotboll. Driven av maskininlärning.",
    keywords: ["fotboll", "prediktioner", "analys", "betting", "value bets", "AI", "maskininlärning"],
    openGraph: {
        type: "website",
        locale: "sv_SE",
        siteName: "ScoreLock",
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
            <body className={`${inter.className} bg-gray-950 text-gray-100 antialiased`}>
                <div className="min-h-screen flex flex-col">
                    <SentryProvider>
                        <Header />
                        <main className="flex-1">{children}</main>
                        <Footer />
                        <CookieConsent />
                    </SentryProvider>
                </div>
            </body>
        </html>
    );
}

function Header() {
    return (
        <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
            <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                <Link href="/" className="flex items-center gap-2">
                    <span className="text-2xl">⚽</span>
                    <span className="text-xl font-bold text-scorelock-400">ScoreLock</span>
                </Link>
                <div className="hidden md:flex items-center gap-6 text-sm">
                    <Link href="/" className="hover:text-scorelock-400 transition-colors">
                        Artiklar
                    </Link>
                    <Link href="/matches" className="hover:text-scorelock-400 transition-colors">
                        Matcher
                    </Link>
                    <Link href="/predictions" className="hover:text-scorelock-400 transition-colors">
                        Prediktioner
                    </Link>
                    <Link href="/value-bets" className="hover:text-scorelock-400 transition-colors">
                        Value Bets
                    </Link>
                    <Link href="/standings" className="hover:text-scorelock-400 transition-colors">
                        Tabeller
                    </Link>
                    <Link href="/sentiment" className="hover:text-scorelock-400 transition-colors">
                        Sentiment
                    </Link>
                    <Link href="/leaderboard" className="hover:text-scorelock-400 transition-colors">
                        Tipsligan
                    </Link>
                </div>
                <div className="flex items-center gap-3">
                    <Link
                        href="/login"
                        className="text-sm hover:text-scorelock-400 transition-colors hidden sm:block"
                    >
                        Logga in
                    </Link>
                    <Link
                        href="/signup"
                        className="text-sm bg-scorelock-600 hover:bg-scorelock-700 px-4 py-2 rounded-lg transition-colors"
                    >
                        Skapa konto
                    </Link>
                    {/* Mobile menu button */}
                    <MobileMenuButton />
                </div>
            </nav>
        </header>
    );
}

function MobileMenuButton() {
    return (
        <details className="md:hidden relative">
            <summary className="list-none cursor-pointer p-2">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
            </summary>
            <div className="absolute right-0 top-full mt-2 w-48 bg-gray-900 border border-gray-800 rounded-xl shadow-xl p-2 z-50">
                <MobileLink href="/" label="Artiklar" />
                <MobileLink href="/matches" label="Matcher" />
                <MobileLink href="/predictions" label="Prediktioner" />
                <MobileLink href="/value-bets" label="Value Bets" />
                <MobileLink href="/standings" label="Tabeller" />
                <MobileLink href="/sentiment" label="Sentiment" />
                <MobileLink href="/leaderboard" label="Tipsligan" />
                <hr className="border-gray-800 my-1" />
                <MobileLink href="/login" label="Logga in" />
            </div>
        </details>
    );
}

function MobileLink({ href, label }: { href: string; label: string }) {
    return (
        <Link
            href={href}
            className="block px-3 py-2 rounded-lg text-sm hover:bg-gray-800 transition-colors"
        >
            {label}
        </Link>
    );
}

function Footer() {
    return (
        <footer className="border-t border-gray-800 py-8 mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6 text-sm">
                    <div>
                        <h4 className="font-semibold mb-2 text-gray-300">Analys</h4>
                        <Link href="/" className="block text-gray-500 hover:text-gray-300">Artiklar</Link>
                        <Link href="/predictions" className="block text-gray-500 hover:text-gray-300">Prediktioner</Link>
                        <Link href="/value-bets" className="block text-gray-500 hover:text-gray-300">Value Bets</Link>
                    </div>
                    <div>
                        <h4 className="font-semibold mb-2 text-gray-300">Data</h4>
                        <Link href="/matches" className="block text-gray-500 hover:text-gray-300">Matcher</Link>
                        <Link href="/standings" className="block text-gray-500 hover:text-gray-300">Tabeller</Link>
                        <Link href="/sentiment" className="block text-gray-500 hover:text-gray-300">Sentiment</Link>
                    </div>
                    <div>
                        <h4 className="font-semibold mb-2 text-gray-300">Konto</h4>
                        <Link href="/login" className="block text-gray-500 hover:text-gray-300">Logga in</Link>
                        <Link href="/signup" className="block text-gray-500 hover:text-gray-300">Skapa konto</Link>
                        <Link href="/leaderboard" className="block text-gray-500 hover:text-gray-300">Tipsligan</Link>
                    </div>
                    <div>
                        <h4 className="font-semibold mb-2 text-gray-300">Om ScoreLock</h4>
                        <Link href="/privacy" className="block text-gray-500 hover:text-gray-300">Integritetspolicy</Link>
                        <Link href="/terms" className="block text-gray-500 hover:text-gray-300">Användarvillkor</Link>
                        <p className="text-gray-600 text-xs mt-2">AI-driven fotbollsanalys.</p>
                    </div>
                </div>
                <div className="text-center text-xs text-gray-600 pt-4 border-t border-gray-800">
                    <p>© 2026 ScoreLock. Datadriven analysplattform — inte spelrådgivning. 18+.</p>
                    <p className="mt-1">
                        Spela ansvarsfullt. Stödlinjen: 020-819 100 ·{" "}
                        <Link href="/privacy" className="hover:text-gray-400">Integritetspolicy</Link>{" · "}
                        <Link href="/terms" className="hover:text-gray-400">Villkor</Link>
                    </p>
                </div>
            </div>
        </footer>
    );
}

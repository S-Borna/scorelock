import { CookieConsent } from "@/components/cookie-consent";
import { SentryProvider } from "@/components/sentry-provider";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({
    subsets: ["latin"],
    variable: "--font-inter",
});

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
            <body className={`${inter.variable} font-sans bg-surface text-gray-100 antialiased`}>
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

/* ── Navigation items ─────────────────────────────────── */
const NAV_ITEMS = [
    { href: "/matches", label: "Matcher" },
    { href: "/value-bets", label: "Value Bets" },
    { href: "/standings", label: "Tabeller" },
    { href: "/predictions", label: "Prediktioner" },
    { href: "/", label: "Artiklar" },
    { href: "/sentiment", label: "Sentiment" },
    { href: "/leaderboard", label: "Tipsligan" },
];

function Header() {
    return (
        <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-surface-950/80 backdrop-blur-xl supports-[backdrop-filter]:bg-surface-950/60">
            <nav className="container-main h-16 flex items-center justify-between">
                {/* Logo */}
                <Link href="/" className="flex items-center gap-2.5 group">
                    <div className="w-8 h-8 rounded-lg bg-scorelock-600 flex items-center justify-center shadow-glow-sm group-hover:shadow-glow-md transition-shadow duration-300">
                        <svg viewBox="0 0 24 24" className="w-4.5 h-4.5 text-white" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.22.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
                        </svg>
                    </div>
                    <span className="text-lg font-bold tracking-tight">
                        Score<span className="text-scorelock-400">Lock</span>
                    </span>
                </Link>

                {/* Desktop nav */}
                <div className="hidden md:flex items-center gap-1">
                    {NAV_ITEMS.map((item) => (
                        <Link
                            key={item.href}
                            href={item.href}
                            className="nav-link px-3 py-2 rounded-lg hover:bg-white/[0.04]"
                        >
                            {item.label}
                        </Link>
                    ))}
                </div>

                {/* Right side */}
                <div className="flex items-center gap-2">
                    <Link href="/login" className="btn-ghost hidden sm:inline-flex text-sm">
                        Logga in
                    </Link>
                    <Link href="/signup" className="btn-primary text-sm px-4 py-2">
                        Skapa konto
                    </Link>
                    <MobileMenuButton />
                </div>
            </nav>
        </header>
    );
}

function MobileMenuButton() {
    return (
        <details className="md:hidden relative group">
            <summary className="list-none cursor-pointer p-2 rounded-lg hover:bg-white/[0.05] transition-colors">
                <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                </svg>
            </summary>
            <div className="absolute right-0 top-full mt-2 w-56 glass-strong rounded-xl shadow-elevated p-2 z-50 animate-fade-up">
                {NAV_ITEMS.map((item) => (
                    <MobileLink key={item.href} href={item.href} label={item.label} />
                ))}
                <div className="divider my-2" />
                <MobileLink href="/login" label="Logga in" />
            </div>
        </details>
    );
}

function MobileLink({ href, label }: { href: string; label: string }) {
    return (
        <Link
            href={href}
            className="block px-3 py-2.5 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-white/[0.05] transition-all duration-150"
        >
            {label}
        </Link>
    );
}

function Footer() {
    return (
        <footer className="mt-auto border-t border-white/[0.04]">
            <div className="container-main py-12">
                {/* Top section — Logo + links */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-10">
                    {/* Brand column */}
                    <div className="col-span-2 md:col-span-1">
                        <Link href="/" className="flex items-center gap-2 mb-3">
                            <div className="w-7 h-7 rounded-lg bg-scorelock-600 flex items-center justify-center">
                                <svg viewBox="0 0 24 24" className="w-3.5 h-3.5 text-white" fill="currentColor">
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.22.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
                                </svg>
                            </div>
                            <span className="font-bold text-sm">ScoreLock</span>
                        </Link>
                        <p className="text-xs text-gray-500 leading-relaxed">
                            AI-driven fotbollsanalys. Prediktioner, sentiment och value bets.
                        </p>
                    </div>

                    {/* Link columns */}
                    <FooterCol title="Matcher" links={[
                        { href: "/matches", label: "Livescore" },
                        { href: "/value-bets", label: "Value Bets" },
                        { href: "/standings", label: "Tabeller" },
                    ]} />
                    <FooterCol title="Analys" links={[
                        { href: "/predictions", label: "Prediktioner" },
                        { href: "/", label: "Artiklar" },
                        { href: "/sentiment", label: "Sentiment" },
                    ]} />
                    <FooterCol title="Konto" links={[
                        { href: "/login", label: "Logga in" },
                        { href: "/signup", label: "Skapa konto" },
                        { href: "/leaderboard", label: "Tipsligan" },
                    ]} />
                    <FooterCol title="Juridik" links={[
                        { href: "/privacy", label: "Integritetspolicy" },
                        { href: "/terms", label: "Användarvillkor" },
                    ]} />
                </div>

                {/* Bottom section */}
                <div className="divider mb-6" />
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-gray-600">
                    <p>© 2026 ScoreLock. Datadriven analysplattform — inte spelrådgivning. 18+.</p>
                    <p>
                        Spela ansvarsfullt · Stödlinjen: 020-819 100 ·{" "}
                        <Link href="/privacy" className="hover:text-gray-400 transition-colors">Integritetspolicy</Link>{" · "}
                        <Link href="/terms" className="hover:text-gray-400 transition-colors">Villkor</Link>
                    </p>
                </div>
            </div>
        </footer>
    );
}

function FooterCol({ title, links }: { title: string; links: { href: string; label: string }[] }) {
    return (
        <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">{title}</h4>
            <div className="space-y-2">
                {links.map((link) => (
                    <Link
                        key={link.href}
                        href={link.href}
                        className="block text-sm text-gray-400 hover:text-white transition-colors duration-150"
                    >
                        {link.label}
                    </Link>
                ))}
            </div>
        </div>
    );
}

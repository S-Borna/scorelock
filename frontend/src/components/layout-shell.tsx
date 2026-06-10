"use client";

import { LanguageToggle } from "@/components/language-toggle";
import { LiveTicker } from "@/components/live-ticker";
import { useLocale } from "@/components/locale-provider";
import Link from "next/link";

/* ── Navigation items ─────────────────────────────────── */
const NAV_ITEMS = [
    { href: "/vm", labelKey: "nav.vm" },
    { href: "/landslag/sverige", labelKey: "nav.sverige" },
    { href: "/matches", labelKey: "nav.matches" },
    { href: "/value-bets", labelKey: "nav.valueBets" },
    { href: "/standings", labelKey: "nav.standings" },
    { href: "/articles", labelKey: "nav.articles" },
    { href: "/leaderboard", labelKey: "nav.tipping" },
];

/* ── Header ───────────────────────────────────────────── */

export function Header() {
    const { t } = useLocale();

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
                            {t(item.labelKey)}
                        </Link>
                    ))}
                </div>

                {/* Right side */}
                <div className="flex items-center gap-2">
                    <LanguageToggle />
                    <Link href="/login" className="btn-ghost hidden sm:inline-flex text-sm">
                        {t("nav.login")}
                    </Link>
                    <Link href="/signup" className="btn-primary text-sm px-4 py-2">
                        {t("nav.signup")}
                    </Link>

                    {/* Mobile menu */}
                    <details className="md:hidden relative group">
                        <summary className="list-none cursor-pointer p-2 rounded-lg hover:bg-white/[0.05] transition-colors">
                            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                            </svg>
                        </summary>
                        <div className="absolute right-0 top-full mt-2 w-56 glass-strong rounded-xl shadow-elevated p-2 z-50 animate-fade-up">
                            {NAV_ITEMS.map((item) => (
                                <MobileLink key={item.href} href={item.href} label={t(item.labelKey)} />
                            ))}
                            <div className="divider my-2" />
                            <MobileLink href="/login" label={t("nav.login")} />
                        </div>
                    </details>
                </div>
            </nav>
            {/* Livescore-tickern — kärnan, synlig på varje sida när matcher rullar */}
            <LiveTicker />
        </header>
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

/* ── Footer ───────────────────────────────────────────── */

export function Footer() {
    const { t } = useLocale();

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
                            {t("footer.desc")}
                        </p>
                    </div>

                    {/* Link columns */}
                    <FooterCol title={t("footer.matches")} links={[
                        { href: "/matches", label: t("footer.livescore") },
                        { href: "/value-bets", label: t("nav.valueBets") },
                        { href: "/standings", label: t("nav.standings") },
                    ]} />
                    <FooterCol title={t("footer.analysis")} links={[
                        { href: "/predictions", label: t("nav.predictions") },
                        { href: "/articles", label: t("nav.articles") },
                        { href: "/sentiment", label: t("nav.sentiment") },
                    ]} />
                    <FooterCol title={t("footer.account")} links={[
                        { href: "/login", label: t("nav.login") },
                        { href: "/signup", label: t("nav.signup") },
                        { href: "/leaderboard", label: t("nav.tipping") },
                    ]} />
                    <FooterCol title={t("footer.legal")} links={[
                        { href: "/privacy", label: t("footer.privacy") },
                        { href: "/terms", label: t("footer.terms") },
                    ]} />
                </div>

                {/* Signatur — created & designed by */}
                <div className="divider mb-6" />
                <div className="text-center mb-6">
                    <p className="text-[10px] uppercase tracking-[0.35em] text-gray-600 mb-1.5">
                        Created &amp; designed by
                    </p>
                    <p className="font-serif italic text-xl text-gray-200 tracking-tight">
                        Said Borna
                    </p>
                </div>

                {/* Bottom section */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-gray-600">
                    <div className="flex items-center gap-3">
                        <p>{t("footer.copyright")}</p>
                        <a href="https://globaldex.ai/domain/scorelock.saidborna.com" target="_blank" rel="noopener noreferrer">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img src="https://globaldex.ai/api/v1/badge?domain=scorelock.saidborna.com" alt="GlobalDex Score" height={32} width={210} className="h-[24px] w-auto" />
                        </a>
                    </div>
                    <p>
                        {t("footer.responsible")} ·{" "}
                        <Link href="/privacy" className="hover:text-gray-400 transition-colors">{t("footer.privacy")}</Link>{" · "}
                        <Link href="/terms" className="hover:text-gray-400 transition-colors">{t("footer.terms")}</Link>
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

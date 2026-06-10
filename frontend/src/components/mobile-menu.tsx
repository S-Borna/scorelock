"use client";

import { useCallback, useEffect, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { usePathname } from "next/navigation";

/**
 * Mobilmenyn — fullskärms-drawer med editorial tyngd, inte en dropdown-hack.
 *
 * - Animerad hamburger→X (rena transforms, 60fps)
 * - Overlay med backdrop-blur + scroll-lock på body
 * - Nav-länkar i stor Fraunces med staggered entrance
 * - Stängs vid navigering (pathname-ändring), Escape och backdrop-tap
 * - Respekterar safe-area-insets (iPhone-notch/home-indicator)
 */

const MENU_ITEMS: { href: string; label: string; accent?: boolean }[] = [
    { href: "/vm", label: "VM 2026", accent: true },
    { href: "/landslag/sverige", label: "Sverige", accent: true },
    { href: "/matches", label: "Matcher" },
    { href: "/value-bets", label: "Value Bets" },
    { href: "/standings", label: "Tabeller" },
    { href: "/articles", label: "Artiklar" },
    { href: "/leaderboard", label: "Tipsligan" },
];

export function MobileMenu() {
    const [open, setOpen] = useState(false);
    // Portal-mål sätts efter mount (SSR saknar document) — drawern MÅSTE
    // portalas till body: headerns backdrop-blur skapar annars en containing
    // block som fångar fixed-element (drawern blev 96px hög inuti headern).
    const [mounted, setMounted] = useState(false);
    const pathname = usePathname();

    useEffect(() => setMounted(true), []);

    const close = useCallback(() => setOpen(false), []);

    // Stäng vid navigering
    useEffect(() => {
        close();
    }, [pathname, close]);

    // Scroll-lock + Escape
    useEffect(() => {
        if (!open) return;
        const prev = document.body.style.overflow;
        document.body.style.overflow = "hidden";
        const onKey = (e: KeyboardEvent) => {
            if (e.key === "Escape") close();
        };
        window.addEventListener("keydown", onKey);
        return () => {
            document.body.style.overflow = prev;
            window.removeEventListener("keydown", onKey);
        };
    }, [open, close]);

    return (
        <div className="md:hidden">
            {/* Hamburger → X */}
            <button
                type="button"
                aria-label={open ? "Stäng menyn" : "Öppna menyn"}
                aria-expanded={open}
                onClick={() => setOpen((v) => !v)}
                className="relative z-[70] flex h-10 w-10 items-center justify-center rounded-lg transition-colors hover:bg-white/[0.05]"
            >
                <span className="relative block h-3.5 w-5">
                    <span
                        className={
                            "absolute left-0 top-0 h-[1.5px] w-5 rounded-full bg-gray-200 transition-all duration-300 [transition-timing-function:cubic-bezier(0.22,1,0.36,1)] " +
                            (open ? "top-[6.5px] rotate-45" : "")
                        }
                    />
                    <span
                        className={
                            "absolute left-0 top-[6.5px] h-[1.5px] w-5 rounded-full bg-gray-200 transition-all duration-200 " +
                            (open ? "opacity-0 scale-x-0" : "")
                        }
                    />
                    <span
                        className={
                            "absolute left-0 bottom-0 h-[1.5px] w-5 rounded-full bg-gray-200 transition-all duration-300 [transition-timing-function:cubic-bezier(0.22,1,0.36,1)] " +
                            (open ? "bottom-[6px] -rotate-45" : "")
                        }
                    />
                </span>
            </button>

            {mounted && createPortal(
            <>
            {/* Backdrop */}
            <div
                aria-hidden
                onClick={close}
                className={
                    "fixed inset-0 z-[60] bg-surface-950/70 backdrop-blur-md transition-opacity duration-300 " +
                    (open ? "opacity-100" : "pointer-events-none opacity-0")
                }
            />

            {/* Drawer */}
            <nav
                aria-label="Mobilmeny"
                className={
                    "fixed inset-y-0 right-0 z-[65] flex w-[84%] max-w-sm flex-col bg-[#0a0e18] border-l border-white/[0.07] shadow-2xl transition-transform duration-[400ms] [transition-timing-function:cubic-bezier(0.22,1,0.36,1)] " +
                    (open ? "translate-x-0" : "translate-x-full")
                }
                style={{
                    paddingTop: "calc(env(safe-area-inset-top, 0px) + 4.5rem)",
                    paddingBottom: "calc(env(safe-area-inset-bottom, 0px) + 1.5rem)",
                }}
            >
                <div className="flex-1 overflow-y-auto px-7">
                    <ul className="space-y-1">
                        {MENU_ITEMS.map((item, i) => (
                            <li
                                key={item.href}
                                className="transition-all duration-500 [transition-timing-function:cubic-bezier(0.22,1,0.36,1)]"
                                style={{
                                    transitionDelay: open ? `${80 + i * 45}ms` : "0ms",
                                    opacity: open ? 1 : 0,
                                    transform: open ? "translateX(0)" : "translateX(24px)",
                                }}
                            >
                                <Link
                                    href={item.href}
                                    className={
                                        "group flex items-baseline gap-3 border-b border-white/[0.05] py-3.5 " +
                                        (item.accent ? "text-yellow-200" : "text-gray-100")
                                    }
                                >
                                    <span className="font-mono text-[10px] text-gray-600 tabular-nums">
                                        {String(i + 1).padStart(2, "0")}
                                    </span>
                                    <span className="font-serif text-2xl tracking-tight transition-transform duration-300 group-active:translate-x-1">
                                        {item.label}
                                    </span>
                                    {item.accent && (
                                        <span className="ml-auto text-xs text-yellow-300/60">🇸🇪</span>
                                    )}
                                </Link>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Botten: konto-CTA */}
                <div
                    className="px-7 pt-4 transition-all duration-500"
                    style={{
                        transitionDelay: open ? "420ms" : "0ms",
                        opacity: open ? 1 : 0,
                    }}
                >
                    <Link href="/signup" className="btn-primary mb-2 block w-full text-center">
                        Skapa konto
                    </Link>
                    <Link
                        href="/login"
                        className="block w-full py-2 text-center text-sm text-gray-400 hover:text-gray-200 transition-colors"
                    >
                        Logga in
                    </Link>
                </div>
            </nav>
            </>,
            document.body)}
        </div>
    );
}

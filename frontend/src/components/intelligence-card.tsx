"use client";

import { useState } from "react";
import { useLocale } from "@/components/locale-provider";
import { parseUTC } from "@/lib/time";
import type {
    IntelligenceKind,
    MatchIntelligence,
    MatchIntelligenceBundle,
} from "@/lib/types";

const TAB_ORDER: IntelligenceKind[] = ["pre_match", "in_match", "post_match"];

const TAB_LABEL_KEY: Record<IntelligenceKind, string> = {
    pre_match: "intelligence.pre_match",
    in_match: "intelligence.in_match",
    post_match: "intelligence.post_match",
};

function pickFirstAvailable(
    bundle: MatchIntelligenceBundle,
): IntelligenceKind | null {
    for (const kind of TAB_ORDER) {
        if (bundle[kind]) return kind;
    }
    return null;
}

function formatGeneratedAt(iso: string): string {
    try {
        // Backend-tider är naiv UTC → parseUTC + formatera i svensk tid, annars
        // tolkas strängen som webbläsarens lokala tid och blir 2h fel.
        return parseUTC(iso)
            .toLocaleString("sv-SE", {
                timeZone: "Europe/Stockholm",
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
            })
            .replace(",", "");
    } catch {
        return iso;
    }
}

function Body({ text }: { text: string }) {
    const paragraphs = text.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
    return (
        <div className="space-y-3 text-sm text-gray-200 leading-relaxed">
            {paragraphs.map((p, i) => (
                <p key={i}>{p}</p>
            ))}
        </div>
    );
}

export function IntelligenceCard({
    bundle,
    variant = "default",
}: {
    bundle: MatchIntelligenceBundle;
    variant?: "default" | "hero";
}) {
    const { t } = useLocale();
    const [active, setActive] = useState<IntelligenceKind | null>(() =>
        pickFirstAvailable(bundle),
    );

    if (!active) return null;
    const current: MatchIntelligence | null = bundle[active];
    if (!current) return null;

    const minuteLabel =
        current.kind === "in_match" && current.as_of_minute !== null
            ? ` · ${current.as_of_minute}' ${t("intelligence.minute_short")}`
            : "";

    if (variant === "hero") {
        return (
            // Tunn gradient-border via p-px-wrapper — premium-kant i scorelock-blå, inte neon.
            <section className="relative rounded-2xl p-px bg-gradient-to-br from-scorelock-400/30 via-white/[0.07] to-scorelock-600/20">
                <div className="relative overflow-hidden rounded-[15px] bg-surface-950 p-6 md:p-8">
                    <div className="absolute inset-0 bg-gradient-to-br from-scorelock-500/[0.06] via-surface-900/40 to-transparent pointer-events-none" />
                    <div className="absolute -top-32 -right-32 w-64 h-64 rounded-full bg-scorelock-500/[0.08] blur-3xl pointer-events-none" />
                    <div className="relative">
                    <div className="flex items-center justify-between mb-5 flex-wrap gap-2">
                        <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-widest text-scorelock-300">
                            <span className="relative flex h-4 w-4 items-center justify-center">
                                <span className="absolute inset-0 rounded-full bg-scorelock-400/25 animate-ping [animation-duration:2.5s]" />
                                <svg
                                    viewBox="0 0 16 16"
                                    className="relative h-3 w-3 text-scorelock-400"
                                    fill="currentColor"
                                    aria-hidden="true"
                                >
                                    <path d="M8 0l1.7 6.3L16 8l-6.3 1.7L8 16l-1.7-6.3L0 8l6.3-1.7L8 0z" />
                                </svg>
                            </span>
                            ScoreLock AI-analys
                        </div>
                        <span className="text-[10px] text-gray-500 font-mono uppercase tracking-wider">
                            ScoreLock AI
                        </span>
                    </div>

                    <div className="flex gap-1 mb-5 border-b border-white/[0.06]">
                        {TAB_ORDER.map((kind) => {
                            const exists = !!bundle[kind];
                            const isActive = kind === active;
                            return (
                                <button
                                    key={kind}
                                    type="button"
                                    disabled={!exists}
                                    onClick={() => exists && setActive(kind)}
                                    className={
                                        "px-4 py-2.5 text-xs uppercase tracking-wider transition-colors " +
                                        (isActive
                                            ? "text-white border-b-2 border-scorelock-400"
                                            : exists
                                              ? "text-gray-400 hover:text-gray-200"
                                              : "text-gray-700 cursor-not-allowed")
                                    }
                                >
                                    {t(TAB_LABEL_KEY[kind])}
                                </button>
                            );
                        })}
                    </div>

                    <p className="font-display text-2xl md:text-3xl tracking-tight leading-tight text-white mb-5">
                        {current.summary}
                    </p>

                    <div className="max-w-prose text-[15px] leading-relaxed text-gray-200 space-y-3">
                        {current.body
                            .split(/\n\s*\n/)
                            .map((p) => p.trim())
                            .filter(Boolean)
                            .map((p, i) => (
                                <p key={i}>{p}</p>
                            ))}
                    </div>

                    <p className="text-[9px] text-gray-700 mt-7 pt-4 border-t border-white/[0.04] font-mono uppercase tracking-widest">
                        Genererad {formatGeneratedAt(current.generated_at)}
                        {minuteLabel}
                    </p>
                    </div>
                </div>
            </section>
        );
    }

    return (
        <div className="card">
            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                <h2 className="text-base font-semibold text-white">
                    🤖 {t("intelligence.title")}
                </h2>
                <span className="text-xs text-gray-500 font-mono">
                    ScoreLock AI
                </span>
            </div>

            <div className="flex gap-1 mb-4 border-b border-white/[0.06]">
                {TAB_ORDER.map((kind) => {
                    const exists = !!bundle[kind];
                    const isActive = kind === active;
                    return (
                        <button
                            key={kind}
                            type="button"
                            disabled={!exists}
                            onClick={() => exists && setActive(kind)}
                            className={
                                "px-3 py-2 text-xs uppercase tracking-wider transition-colors " +
                                (isActive
                                    ? "text-white border-b-2 border-scorelock-500"
                                    : exists
                                      ? "text-gray-400 hover:text-gray-200"
                                      : "text-gray-600 cursor-not-allowed")
                            }
                        >
                            {t(TAB_LABEL_KEY[kind])}
                        </button>
                    );
                })}
            </div>

            <p className="text-sm font-semibold text-white mb-3">
                {current.summary}
            </p>

            <Body text={current.body} />

            <p className="text-xs text-gray-600 mt-4 font-mono">
                {formatGeneratedAt(current.generated_at)}
                {minuteLabel}
            </p>
        </div>
    );
}

"use client";

import { useState } from "react";
import { useLocale } from "@/components/locale-provider";
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
        const d = new Date(iso);
        const yyyy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        const hh = String(d.getHours()).padStart(2, "0");
        const mi = String(d.getMinutes()).padStart(2, "0");
        return `${yyyy}-${mm}-${dd} ${hh}:${mi}`;
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
}: {
    bundle: MatchIntelligenceBundle;
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

    return (
        <div className="card">
            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                <h2 className="text-base font-semibold text-white">
                    🤖 {t("intelligence.title")}
                </h2>
                <span className="text-xs text-gray-500 font-mono">
                    {current.model_version}
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

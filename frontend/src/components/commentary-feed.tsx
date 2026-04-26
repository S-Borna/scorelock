"use client";

import { useLocale } from "@/components/locale-provider";
import type { CommentaryEntry, CommentaryFeed } from "@/lib/types";

const TYPE_ICON: Record<string, string> = {
    period_start: "🎬",
    period_end: "⏸",
    goal: "⚽",
    card: "🟨",
    substitution: "🔄",
    big_chance: "❗",
    var: "⚖",
    general: "·",
};

function formatMinute(e: CommentaryEntry): string {
    if (e.stoppage && e.stoppage > 0) return `${e.minute}+${e.stoppage}'`;
    return `${e.minute}'`;
}

export function CommentaryFeedCard({
    feed,
    locale,
}: {
    feed: CommentaryFeed;
    locale: "sv" | "en";
}) {
    const { t } = useLocale();
    if (feed.entries.length === 0) return null;

    return (
        <div className="card">
            <h2 className="text-base font-semibold text-white mb-4">
                💬 {t("commentary.title")}
            </h2>
            <div className="space-y-3">
                {feed.entries.map((e) => {
                    const text = locale === "sv" ? e.text_sv : e.text_en;
                    return (
                        <div
                            key={e.id}
                            className="flex items-start gap-3 border-b border-white/[0.04] pb-3 last:border-0 last:pb-0"
                        >
                            <div className="flex flex-col items-center min-w-[2.5rem] pt-0.5">
                                <span className="text-xs text-gray-500 font-mono">
                                    {formatMinute(e)}
                                </span>
                                <span className="text-base leading-none mt-0.5">
                                    {TYPE_ICON[e.comment_type] ?? "·"}
                                </span>
                            </div>
                            <p className="text-sm text-gray-200 leading-relaxed flex-1">
                                {text ?? "—"}
                            </p>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

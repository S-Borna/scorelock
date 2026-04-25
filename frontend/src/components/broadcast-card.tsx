"use client";

import { useLocale } from "@/components/locale-provider";
import type { Broadcast } from "@/lib/types";

export function BroadcastCard({ broadcasts }: { broadcasts: Broadcast[] }) {
    const { t } = useLocale();

    if (broadcasts.length === 0) return null;

    return (
        <div className="card">
            <h2 className="text-base font-semibold mb-4 text-white">
                📺 {t("broadcast.title")}
            </h2>
            <div className="space-y-3">
                {broadcasts.map((b) => (
                    <div
                        key={b.id}
                        className="flex items-center justify-between gap-3 py-2 border-b border-white/[0.06] last:border-0"
                    >
                        <div className="flex items-center gap-3">
                            <span className="badge">{b.provider_type}</span>
                            <span className="font-semibold text-white">{b.channel_name}</span>
                        </div>
                        {b.watch_url && (
                            <a
                                href={b.watch_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn-primary text-xs"
                            >
                                {t("broadcast.watch")} →
                            </a>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}

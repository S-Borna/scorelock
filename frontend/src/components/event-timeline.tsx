"use client";

import { useLocale } from "@/components/locale-provider";
import type { EventType, FixtureEvent } from "@/lib/types";

const ICON: Record<EventType, string> = {
    GOAL: "⚽",
    OWN_GOAL: "⚽",
    PENALTY_GOAL: "🎯",
    MISSED_PENALTY: "✗",
    YELLOW_CARD: "🟨",
    RED_CARD: "🟥",
    SECOND_YELLOW: "🟨🟥",
    SUBSTITUTION: "🔄",
    VAR_GOAL_AWARDED: "🟢 VAR",
    VAR_GOAL_CANCELLED: "🔴 VAR",
    VAR_PENALTY_AWARDED: "🟢 VAR",
    VAR_PENALTY_OVERTURNED: "🔴 VAR",
    VAR_RED_CARD: "🟥 VAR",
    PERIOD_START: "▶",
    PERIOD_END: "⏸",
    MATCH_START: "🎬",
    MATCH_END: "🏁",
};

function formatMinute(e: FixtureEvent): string {
    const m = e.minute;
    if (e.stoppage && e.stoppage > 0) return `${m}+${e.stoppage}'`;
    return `${m}'`;
}

export function EventTimeline({
    events,
    homeTeamId,
}: {
    events: FixtureEvent[];
    homeTeamId: number;
}) {
    const { t } = useLocale();

    if (events.length === 0) return null;

    return (
        <div className="card">
            <h2 className="text-base font-semibold mb-4 text-white">
                ⏱ {t("event.timeline_title")}
            </h2>
            <div className="space-y-2">
                {events.map((e) => {
                    const isHome = e.team_id === homeTeamId;
                    const align = isHome ? "justify-start" : "justify-end";
                    const textAlign = isHome ? "text-left" : "text-right";
                    return (
                        <div
                            key={e.id}
                            className={`flex items-center gap-3 ${align} text-sm`}
                        >
                            {!isHome && (
                                <div className={`flex-1 ${textAlign}`}>
                                    <EventBody event={e} t={t} />
                                </div>
                            )}
                            <div className="flex flex-col items-center min-w-[3rem]">
                                <span className="text-xs text-gray-500 font-mono">
                                    {formatMinute(e)}
                                </span>
                                <span className="text-lg leading-none">
                                    {ICON[e.event_type] ?? "•"}
                                </span>
                            </div>
                            {isHome && (
                                <div className={`flex-1 ${textAlign}`}>
                                    <EventBody event={e} t={t} />
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

function EventBody({
    event,
    t,
}: {
    event: FixtureEvent;
    t: (key: string) => string;
}) {
    if (event.event_type === "SUBSTITUTION") {
        return (
            <div>
                <div className="text-white">
                    <span className="text-green-400">▲</span> {event.player_in_name}
                </div>
                <div className="text-gray-500">
                    <span className="text-red-400">▼</span> {event.player_out_name}
                </div>
            </div>
        );
    }

    return (
        <div>
            <div className="text-white font-semibold">
                {event.primary_player_name ?? "—"}
            </div>
            {event.secondary_player_name && (
                <div className="text-xs text-gray-500">
                    {t("event.assist_label")} {event.secondary_player_name}
                </div>
            )}
            {event.description && !event.secondary_player_name && (
                <div className="text-xs text-gray-500">{event.description}</div>
            )}
        </div>
    );
}

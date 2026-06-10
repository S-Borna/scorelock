import type { Odds } from "@/lib/types";

/**
 * Marknadens bild — implicita 1X2-sannolikheter ur RIKTIGA bookmaker-odds.
 *
 * Visas i stället för ML-prognosen när modellens konfidens är för låg (t.ex.
 * landslagsmatcher som klubbmodellen aldrig tränats på). Bästa odds per utfall
 * → 1/odds → normaliserat (överrundan borträknad). Allt här är äkta marknads-
 * data — inga pseudo-siffror.
 */
export function MarketView({ odds }: { odds: Odds[] }) {
    const oneXTwo = odds.filter((o) => o.market === "1X2");
    if (oneXTwo.length === 0) return null;

    const bestHome = Math.max(...oneXTwo.map((o) => o.home_odds ?? 0));
    const bestDraw = Math.max(...oneXTwo.map((o) => o.draw_odds ?? 0));
    const bestAway = Math.max(...oneXTwo.map((o) => o.away_odds ?? 0));
    if (!bestHome || !bestDraw || !bestAway) return null;

    const rawH = 1 / bestHome;
    const rawD = 1 / bestDraw;
    const rawA = 1 / bestAway;
    const sum = rawH + rawD + rawA;
    const pH = rawH / sum;
    const pD = rawD / sum;
    const pA = rawA / sum;
    const bookies = new Set(oneXTwo.map((o) => o.bookmaker)).size;

    return (
        <div className="space-y-3">
            <div className="flex gap-1 h-2.5 rounded-full overflow-hidden">
                <div className="bg-gradient-to-r from-scorelock-600/80 to-scorelock-500" style={{ width: `${pH * 100}%` }} />
                <div className="bg-white/20" style={{ width: `${pD * 100}%` }} />
                <div className="bg-gradient-to-r from-blue-500 to-blue-400/80" style={{ width: `${pA * 100}%` }} />
            </div>
            <div className="flex justify-between text-xs font-mono tabular-nums">
                <span className="text-scorelock-400">1 · {Math.round(pH * 100)}%</span>
                <span className="text-gray-400">X · {Math.round(pD * 100)}%</span>
                <span className="text-blue-400">2 · {Math.round(pA * 100)}%</span>
            </div>
            <p className="text-[11px] text-gray-500 leading-snug">
                Marknadens implicita sannolikheter ur bästa odds hos {bookies}{" "}
                spelbolag, överrundan borträknad. ScoreLocks ML-prognos visas när
                modellen har täckning för landslagsfotboll.
            </p>
        </div>
    );
}

import type { Prediction } from "@/lib/types";
import { formatProb } from "@/lib/utils";

interface PredictionBarProps {
    prediction: Prediction;
}

export function PredictionBar({ prediction }: PredictionBarProps) {
    const { home_win_prob, draw_prob, away_win_prob } = prediction;

    return (
        <div className="space-y-4">
            {/* Labels */}
            <div className="flex justify-between text-sm">
                <div>
                    <span className="text-gray-500 text-xs block">Hemma</span>
                    <span className="font-mono font-semibold text-scorelock-400">{formatProb(home_win_prob)}</span>
                </div>
                <div className="text-center">
                    <span className="text-gray-500 text-xs block">Oavgjort</span>
                    <span className="font-mono font-semibold text-gray-300">{formatProb(draw_prob)}</span>
                </div>
                <div className="text-right">
                    <span className="text-gray-500 text-xs block">Borta</span>
                    <span className="font-mono font-semibold text-accent-blue">{formatProb(away_win_prob)}</span>
                </div>
            </div>

            {/* Stacked probability bar */}
            <div className="prob-bar-track">
                <div
                    className="prob-bar bg-gradient-to-r from-scorelock-600 to-scorelock-500"
                    style={{ width: `${home_win_prob * 100}%` }}
                />
                <div
                    className="prob-bar bg-gray-500/60"
                    style={{ width: `${draw_prob * 100}%` }}
                />
                <div
                    className="prob-bar bg-gradient-to-r from-accent-blue/80 to-accent-blue"
                    style={{ width: `${away_win_prob * 100}%` }}
                />
            </div>

            {/* Extra stats */}
            <div className="flex justify-between text-xs text-gray-500">
                {prediction.expected_goals != null && (
                    <span>xG: <span className="text-gray-400 font-mono">{prediction.expected_goals.toFixed(1)}</span></span>
                )}
                {prediction.over_25_prob != null && (
                    <span>O2.5: <span className="text-gray-400 font-mono">{formatProb(prediction.over_25_prob)}</span></span>
                )}
                <span>Konfidens: <span className="text-gray-400 font-mono">{formatProb(prediction.confidence)}</span></span>
            </div>

            {/* Value bet indicators */}
            {(prediction.is_value_home || prediction.is_value_draw || prediction.is_value_away) && (
                <div className="flex flex-wrap gap-2 pt-2 border-t border-white/[0.04]">
                    {prediction.is_value_home && (
                        <span className="badge-value">
                            💰 Value: Hemma
                        </span>
                    )}
                    {prediction.is_value_draw && (
                        <span className="badge-value">
                            💰 Value: Oavgjort
                        </span>
                    )}
                    {prediction.is_value_away && (
                        <span className="badge-value">
                            💰 Value: Borta
                        </span>
                    )}
                    {prediction.value_edge != null && (
                        <span className="text-xs text-scorelock-500 font-mono">
                            Edge: {prediction.value_edge.toFixed(1)}%
                        </span>
                    )}
                </div>
            )}
        </div>
    );
}

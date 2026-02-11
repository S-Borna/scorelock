import type { Prediction } from "@/lib/types";
import { formatProb } from "@/lib/utils";

interface PredictionBarProps {
    prediction: Prediction;
}

export function PredictionBar({ prediction }: PredictionBarProps) {
    const { home_win_prob, draw_prob, away_win_prob } = prediction;

    return (
        <div className="space-y-3">
            <div className="flex justify-between text-sm">
                <span>Home {formatProb(home_win_prob)}</span>
                <span>Draw {formatProb(draw_prob)}</span>
                <span>Away {formatProb(away_win_prob)}</span>
            </div>

            {/* Stacked probability bar */}
            <div className="flex h-3 rounded-full overflow-hidden bg-gray-800">
                <div
                    className="prob-bar bg-scorelock-500"
                    style={{ width: `${home_win_prob * 100}%` }}
                />
                <div
                    className="prob-bar bg-gray-500"
                    style={{ width: `${draw_prob * 100}%` }}
                />
                <div
                    className="prob-bar bg-red-500"
                    style={{ width: `${away_win_prob * 100}%` }}
                />
            </div>

            {/* Extra stats */}
            <div className="flex justify-between text-xs text-gray-500">
                {prediction.expected_goals != null && (
                    <span>xG: {prediction.expected_goals.toFixed(1)}</span>
                )}
                {prediction.over_25_prob != null && (
                    <span>O2.5: {formatProb(prediction.over_25_prob)}</span>
                )}
                <span>Confidence: {formatProb(prediction.confidence)}</span>
            </div>

            {/* Value bet indicators */}
            {(prediction.is_value_home || prediction.is_value_draw || prediction.is_value_away) && (
                <div className="flex gap-2 mt-2">
                    {prediction.is_value_home && (
                        <span className="badge bg-green-900/50 text-green-400 border border-green-800">
                            💰 Value: Home
                        </span>
                    )}
                    {prediction.is_value_draw && (
                        <span className="badge bg-green-900/50 text-green-400 border border-green-800">
                            💰 Value: Draw
                        </span>
                    )}
                    {prediction.is_value_away && (
                        <span className="badge bg-green-900/50 text-green-400 border border-green-800">
                            💰 Value: Away
                        </span>
                    )}
                    {prediction.value_edge != null && (
                        <span className="text-xs text-green-500">
                            Edge: {prediction.value_edge.toFixed(1)}%
                        </span>
                    )}
                </div>
            )}
        </div>
    );
}

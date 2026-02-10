"""Match prediction serving for ScoreLock.

Loads trained XGBoost models and generates predictions for matches.
Training is handled by app.ml.trainer — this module only serves.
"""

import json
import numpy as np
from dataclasses import dataclass
from pathlib import Path
from scipy.stats import poisson
import joblib
import structlog

from app.ml.features import FeatureComputer

logger = structlog.get_logger()

MODEL_DIR = Path(__file__).parent / "trained_models"


@dataclass
class MatchPrediction:
    """Output of the prediction model."""

    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    confidence: float
    over_25_prob: float
    expected_goals: float
    model_version: str


class MatchPredictor:
    """Serves predictions using trained XGBoost models."""

    def __init__(self) -> None:
        self.result_model = None
        self.goals_model = None
        self.metadata: dict = {}
        self.is_loaded = False

    def load(self, path: Path | None = None) -> bool:
        """Load trained models from disk. Returns True if successful."""
        path = path or MODEL_DIR
        result_path = path / "result_model.joblib"
        goals_path = path / "goals_model.joblib"
        meta_path = path / "metadata.json"

        if not result_path.exists() or not goals_path.exists():
            logger.warning("models_not_found", path=str(path))
            return False

        try:
            self.result_model = joblib.load(result_path)
            self.goals_model = joblib.load(goals_path)

            if meta_path.exists():
                with open(meta_path) as f:
                    self.metadata = json.load(f)

            self.is_loaded = True
            logger.info("models_loaded", version=self.model_version, path=str(path))
            return True

        except Exception as exc:
            logger.error("model_load_failed", error=str(exc))
            return False

    @property
    def model_version(self) -> str:
        return self.metadata.get("version", "unknown")

    def predict(self, features: np.ndarray) -> MatchPrediction:
        """Generate prediction from a feature vector.

        Args:
            features: 2D numpy array of shape (1, n_features)

        Returns:
            MatchPrediction with probabilities and expected goals.
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        # 1X2 probabilities
        probs = self.result_model.predict_proba(features)[0]
        home_prob = float(probs[0])
        draw_prob = float(probs[1])
        away_prob = float(probs[2])

        # Confidence = distance from uniform (33%)
        confidence = float(max(probs) - (1 / 3))

        # Expected goals
        expected_goals = max(0.0, float(self.goals_model.predict(features)[0]))

        # Over 2.5 probability (Poisson approximation)
        over_25_prob = float(1 - poisson.cdf(2, expected_goals)) if expected_goals > 0 else 0.5

        return MatchPrediction(
            home_win_prob=round(home_prob, 4),
            draw_prob=round(draw_prob, 4),
            away_win_prob=round(away_prob, 4),
            confidence=round(confidence, 4),
            over_25_prob=round(over_25_prob, 4),
            expected_goals=round(expected_goals, 2),
            model_version=self.model_version,
        )

    def predict_match(
        self,
        feature_computer: FeatureComputer,
        home_team_id: int,
        away_team_id: int,
        kickoff,
        season: int,
    ) -> MatchPrediction:
        """Higher-level: predict from team IDs using a populated FeatureComputer."""
        features = feature_computer.compute_match_features(
            home_team_id, away_team_id, kickoff, season,
        )
        return self.predict(features)


# ── Value Bet Detection ────────────────────────────────────


def identify_value_bets(
    prediction: MatchPrediction,
    bookmaker_odds: dict,
    min_edge: float = 0.05,
) -> dict:
    """Compare model probabilities against bookmaker odds to find value.

    Args:
        prediction: Our model's prediction
        bookmaker_odds: {"home": 2.10, "draw": 3.40, "away": 3.50}
        min_edge: Minimum edge (probability difference) to flag as value

    Returns:
        Dict with value bet info or empty if no value found.
    """
    # Convert odds to implied probabilities
    implied = {
        "home": 1 / bookmaker_odds["home"],
        "draw": 1 / bookmaker_odds["draw"],
        "away": 1 / bookmaker_odds["away"],
    }

    # Normalize (remove overround)
    total = sum(implied.values())
    implied = {k: v / total for k, v in implied.items()}

    # Compare against our model
    edges = {
        "home": prediction.home_win_prob - implied["home"],
        "draw": prediction.draw_prob - implied["draw"],
        "away": prediction.away_win_prob - implied["away"],
    }

    value_bets = {k: v for k, v in edges.items() if v >= min_edge}

    if not value_bets:
        return {}

    best = max(value_bets, key=value_bets.get)

    # Kelly Criterion: f* = (bp - q) / b
    model_prob = {
        "home": prediction.home_win_prob,
        "draw": prediction.draw_prob,
        "away": prediction.away_win_prob,
    }[best]

    b = bookmaker_odds[best] - 1
    kelly = (b * model_prob - (1 - model_prob)) / b
    kelly = max(0, min(kelly, 0.25))  # Cap at 25%

    return {
        "suggested_bet": best,
        "edge_percent": round(value_bets[best] * 100, 2),
        "kelly_fraction": round(kelly, 4),
        "is_value_home": "home" in value_bets,
        "is_value_draw": "draw" in value_bets,
        "is_value_away": "away" in value_bets,
        "value_edge": round(max(value_bets.values()) * 100, 2),
    }


# ── Singleton ──────────────────────────────────────────────

_predictor: MatchPredictor | None = None


def get_predictor() -> MatchPredictor:
    """Get or create the singleton predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = MatchPredictor()
        _predictor.load()  # is_loaded will be False if no models on disk
    return _predictor


def reload_predictor() -> MatchPredictor:
    """Force reload models from disk (e.g. after retraining)."""
    global _predictor
    _predictor = MatchPredictor()
    _predictor.load()
    return _predictor

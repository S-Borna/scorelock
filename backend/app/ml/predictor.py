"""Match prediction model using XGBoost.

This module handles:
1. Feature engineering from raw match data
2. Model training with walk-forward validation
3. Prediction serving with calibrated probabilities
4. Value bet identification against bookmaker odds
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from xgboost import XGBClassifier, XGBRegressor
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import brier_score_loss, log_loss
import joblib
import structlog
from pathlib import Path

logger = structlog.get_logger()

MODEL_DIR = Path(__file__).parent / "trained_models"
MODEL_DIR.mkdir(exist_ok=True)

MODEL_VERSION = "0.1.0"


@dataclass
class MatchFeatures:
    """Feature vector for a single match prediction."""

    # Team form (last 5 matches)
    home_form_points: float  # Points from last 5 (max 15)
    away_form_points: float
    home_form_goals_scored: float  # Avg goals scored last 5
    away_form_goals_scored: float
    home_form_goals_conceded: float
    away_form_goals_conceded: float

    # xG data
    home_xg_for: float  # Season avg xG for
    home_xg_against: float
    away_xg_for: float
    away_xg_against: float

    # Head to head
    h2h_home_wins: int  # Last 10 H2H
    h2h_draws: int
    h2h_away_wins: int
    h2h_avg_goals: float

    # League position
    home_league_position: int
    away_league_position: int
    home_points: int
    away_points: int

    # Home/away splits
    home_home_record: float  # Points per game at home
    away_away_record: float  # Points per game away

    # Rest days
    home_days_rest: int
    away_days_rest: int

    # Injuries (count of key players missing)
    home_injuries: int
    away_injuries: int

    def to_array(self) -> np.ndarray:
        """Convert to numpy array for model input."""
        return np.array([
            self.home_form_points, self.away_form_points,
            self.home_form_goals_scored, self.away_form_goals_scored,
            self.home_form_goals_conceded, self.away_form_goals_conceded,
            self.home_xg_for, self.home_xg_against,
            self.away_xg_for, self.away_xg_against,
            self.h2h_home_wins, self.h2h_draws, self.h2h_away_wins, self.h2h_avg_goals,
            self.home_league_position, self.away_league_position,
            self.home_points, self.away_points,
            self.home_home_record, self.away_away_record,
            self.home_days_rest, self.away_days_rest,
            self.home_injuries, self.away_injuries,
        ]).reshape(1, -1)

    @staticmethod
    def feature_names() -> list[str]:
        return [
            "home_form_points", "away_form_points",
            "home_form_goals_scored", "away_form_goals_scored",
            "home_form_goals_conceded", "away_form_goals_conceded",
            "home_xg_for", "home_xg_against",
            "away_xg_for", "away_xg_against",
            "h2h_home_wins", "h2h_draws", "h2h_away_wins", "h2h_avg_goals",
            "home_league_position", "away_league_position",
            "home_points", "away_points",
            "home_home_record", "away_away_record",
            "home_days_rest", "away_days_rest",
            "home_injuries", "away_injuries",
        ]


@dataclass
class MatchPrediction:
    """Output of the prediction model."""

    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    confidence: float
    over_25_prob: float
    expected_goals: float
    model_version: str = MODEL_VERSION


class MatchPredictor:
    """XGBoost-based match prediction model."""

    def __init__(self):
        self.result_model: XGBClassifier | None = None
        self.goals_model: XGBRegressor | None = None
        self.is_trained = False

    def train(self, X: pd.DataFrame, y_result: pd.Series, y_goals: pd.Series):
        """
        Train models with walk-forward cross-validation.

        Args:
            X: Feature matrix (one row per match)
            y_result: Match result (0=Home, 1=Draw, 2=Away)
            y_goals: Total goals in match
        """
        logger.info("training_started", samples=len(X))

        # ── 1X2 Classifier ────────────────────────────
        self.result_model = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            random_state=42,
        )

        # Walk-forward validation
        tscv = TimeSeriesSplit(n_splits=5)
        brier_scores = []

        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y_result.iloc[train_idx], y_result.iloc[val_idx]

            self.result_model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False,
            )

            probs = self.result_model.predict_proba(X_val)
            # Calculate Brier score for home win probability
            y_home = (y_val == 0).astype(int)
            brier = brier_score_loss(y_home, probs[:, 0])
            brier_scores.append(brier)

        # Train final model on all data
        self.result_model.fit(X, y_result, verbose=False)

        # Calibrate probabilities
        self.result_model = CalibratedClassifierCV(
            self.result_model, cv=3, method="isotonic"
        )
        self.result_model.fit(X, y_result)

        # ── Goals Regressor ────────────────────────────
        self.goals_model = XGBRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            objective="reg:squarederror",
            random_state=42,
        )
        self.goals_model.fit(X, y_goals)

        self.is_trained = True
        avg_brier = np.mean(brier_scores)
        logger.info("training_complete", avg_brier_score=avg_brier)

    def predict(self, features: MatchFeatures) -> MatchPrediction:
        """Generate prediction for a single match."""
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        X = features.to_array()

        # 1X2 probabilities
        probs = self.result_model.predict_proba(X)[0]
        home_prob, draw_prob, away_prob = probs[0], probs[1], probs[2]

        # Confidence = how far the top probability is from 33% (random)
        confidence = max(probs) - (1 / 3)

        # Expected goals
        expected_goals = float(self.goals_model.predict(X)[0])
        over_25_prob = self._estimate_over_25(expected_goals)

        return MatchPrediction(
            home_win_prob=round(home_prob, 4),
            draw_prob=round(draw_prob, 4),
            away_win_prob=round(away_prob, 4),
            confidence=round(confidence, 4),
            over_25_prob=round(over_25_prob, 4),
            expected_goals=round(expected_goals, 2),
        )

    def _estimate_over_25(self, expected_goals: float) -> float:
        """Estimate P(goals > 2.5) from expected goals using Poisson approx."""
        from scipy.stats import poisson
        # P(X <= 2) where X ~ Poisson(expected_goals)
        prob_under = poisson.cdf(2, expected_goals)
        return round(1 - prob_under, 4)

    def save(self, path: Path | None = None):
        """Save trained models to disk."""
        path = path or MODEL_DIR
        joblib.dump(self.result_model, path / "result_model.joblib")
        joblib.dump(self.goals_model, path / "goals_model.joblib")
        logger.info("models_saved", path=str(path))

    def load(self, path: Path | None = None):
        """Load trained models from disk."""
        path = path or MODEL_DIR
        self.result_model = joblib.load(path / "result_model.joblib")
        self.goals_model = joblib.load(path / "goals_model.joblib")
        self.is_trained = True
        logger.info("models_loaded", path=str(path))


def identify_value_bets(
    prediction: MatchPrediction,
    bookmaker_odds: dict,
    min_edge: float = 0.05,
) -> dict:
    """
    Compare model probabilities against bookmaker odds to find value.

    Args:
        prediction: Our model's prediction
        bookmaker_odds: {"home": 2.10, "draw": 3.40, "away": 3.50}
        min_edge: Minimum edge (probability difference) to flag as value

    Returns:
        Dict with value bet info or empty if no value found
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
    # where b = odds - 1, p = our probability, q = 1 - p
    model_prob = getattr(prediction, f"{best}_win_prob" if best != "draw" else "draw_prob")
    b = bookmaker_odds[best] - 1
    kelly = (b * model_prob - (1 - model_prob)) / b
    kelly = max(0, min(kelly, 0.25))  # Cap at 25% of bankroll

    return {
        "suggested_bet": best,
        "edge_percent": round(value_bets[best] * 100, 2),
        "kelly_fraction": round(kelly, 4),
        "is_value_home": "home" in value_bets,
        "is_value_draw": "draw" in value_bets,
        "is_value_away": "away" in value_bets,
    }

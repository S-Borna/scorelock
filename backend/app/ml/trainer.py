"""Model training pipeline for ScoreLock match predictions.

Orchestrates: data loading -> feature engineering -> model training -> saving.
Can be run as a standalone script or via Celery task.

Usage:
    docker compose exec backend python -m app.ml.trainer
"""

import asyncio
import json
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from xgboost import XGBClassifier, XGBRegressor
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import brier_score_loss, accuracy_score
import joblib
import structlog

from app.ml.features import FeatureComputer, FEATURE_NAMES

logger = structlog.get_logger()

MODEL_DIR = Path(__file__).parent / "trained_models"
MODEL_DIR.mkdir(exist_ok=True)


def get_model_version() -> str:
    """Generate model version from current timestamp."""
    return datetime.utcnow().strftime("v%Y%m%d-%H%M")


async def load_training_data() -> list[dict]:
    """Load all finished fixtures from DB for training."""
    from app.core.database import async_session
    from sqlalchemy import select
    from app.models.models import Fixture, MatchStatus

    async with async_session() as session:
        result = await session.execute(
            select(Fixture)
            .where(
                Fixture.status == MatchStatus.FINISHED,
                Fixture.home_goals.is_not(None),
                Fixture.away_goals.is_not(None),
            )
            .order_by(Fixture.kickoff)
        )
        fixtures = list(result.scalars().all())

    return [
        {
            "fixture_id": f.id,
            "home_team_id": f.home_team_id,
            "away_team_id": f.away_team_id,
            "home_goals": f.home_goals,
            "away_goals": f.away_goals,
            "kickoff": f.kickoff,
            "season": f.season,
            "league_id": f.league_id,
        }
        for f in fixtures
    ]


def train_models(
    X: pd.DataFrame,
    y_result: pd.Series,
    y_goals: pd.Series,
) -> dict:
    """Train XGBoost models with walk-forward cross-validation.

    Returns:
        Dict with trained models, metrics, and feature importances.
    """
    logger.info("training_started", samples=len(X), features=len(X.columns))

    # ── 1X2 Classifier ────────────────────────────────
    base_clf = XGBClassifier(
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

    # Walk-forward cross-validation (adaptive splits)
    n_splits = min(5, max(2, len(X) // 100))
    tscv = TimeSeriesSplit(n_splits=n_splits)
    brier_scores: list[float] = []
    accuracies: list[float] = []

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y_result.iloc[train_idx], y_result.iloc[val_idx]

        base_clf.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        probs = base_clf.predict_proba(X_val)
        preds = base_clf.predict(X_val)

        y_home = (y_val == 0).astype(int)
        brier = brier_score_loss(y_home, probs[:, 0])
        brier_scores.append(brier)

        acc = accuracy_score(y_val, preds)
        accuracies.append(acc)

        logger.info(
            "cv_fold_complete",
            fold=fold,
            brier=round(brier, 4),
            accuracy=round(acc, 4),
            val_size=len(X_val),
        )

    # Train final model on all data
    base_clf.fit(X, y_result, verbose=False)

    # Calibrate probabilities (only if enough data)
    if len(X) >= 200:
        n_cv = min(3, n_splits)
        result_model = CalibratedClassifierCV(base_clf, cv=n_cv, method="isotonic")
        result_model.fit(X, y_result)
    else:
        result_model = base_clf

    # ── Goals Regressor ────────────────────────────────
    goals_model = XGBRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        objective="reg:squarederror",
        random_state=42,
    )
    goals_model.fit(X, y_goals, verbose=False)

    metrics = {
        "avg_brier_score": round(float(np.mean(brier_scores)), 4),
        "avg_accuracy": round(float(np.mean(accuracies)), 4),
        "training_samples": len(X),
        "features": len(X.columns),
        "cv_folds": n_splits,
    }

    logger.info("training_complete", **metrics)

    return {
        "result_model": result_model,
        "goals_model": goals_model,
        "metrics": metrics,
        "feature_importances": dict(
            zip(
                FEATURE_NAMES,
                [round(float(v), 4) for v in base_clf.feature_importances_],
            )
        ),
    }


def save_models(
    result_model,
    goals_model,
    metrics: dict,
    feature_importances: dict,
    version: str | None = None,
) -> str:
    """Save trained models and metadata to disk."""
    version = version or get_model_version()

    joblib.dump(result_model, MODEL_DIR / "result_model.joblib")
    joblib.dump(goals_model, MODEL_DIR / "goals_model.joblib")

    metadata = {
        "version": version,
        "trained_at": datetime.utcnow().isoformat(),
        "metrics": metrics,
        "feature_importances": feature_importances,
        "feature_names": FEATURE_NAMES,
    }
    with open(MODEL_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("models_saved", version=version, path=str(MODEL_DIR))
    return version


async def run_training_pipeline() -> dict:
    """Full training pipeline: load data -> features -> train -> save.

    Compares new model against existing model's metrics. Only saves
    if the new model is better or no old model exists.

    Returns:
        Training result dict with status and metrics.
    """
    # 1. Load data
    fixtures = await load_training_data()
    if len(fixtures) < 50:
        msg = f"Only {len(fixtures)} finished fixtures (need >= 50)"
        logger.warning("insufficient_training_data", count=len(fixtures))
        return {"status": "skipped", "reason": msg}

    # 2. Feature engineering
    computer = FeatureComputer()
    X, y_result, y_goals = computer.compute_training_dataset(fixtures)

    if len(X) < 30:
        msg = f"Only {len(X)} usable samples after feature computation"
        logger.warning("insufficient_features", count=len(X))
        return {"status": "skipped", "reason": msg}

    # 3. Read old model metrics for comparison
    old_metrics = {}
    meta_path = MODEL_DIR / "metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path) as f:
                old_meta = json.load(f)
                old_metrics = old_meta.get("metrics", {})
        except Exception:
            pass

    # 4. Train
    result = train_models(X, y_result, y_goals)
    new_metrics = result["metrics"]

    # 5. Compare: save only if new model is better (lower Brier or more data)
    old_brier = old_metrics.get("avg_brier_score", 1.0)
    new_brier = new_metrics.get("avg_brier_score", 1.0)
    old_samples = old_metrics.get("training_samples", 0)
    new_samples = new_metrics.get("training_samples", 0)

    should_save = (
        not old_metrics  # No old model → always save
        or new_brier <= old_brier  # Better or equal calibration
        or new_samples > old_samples * 1.1  # 10%+ more training data
    )

    comparison = {
        "old_brier": old_brier,
        "new_brier": new_brier,
        "old_samples": old_samples,
        "new_samples": new_samples,
        "improvement": round(old_brier - new_brier, 4) if old_metrics else None,
    }

    if should_save:
        version = save_models(
            result["result_model"],
            result["goals_model"],
            new_metrics,
            result["feature_importances"],
        )

        # Reload the predictor singleton
        try:
            from app.ml.predictor import reload_predictor

            reload_predictor()
            logger.info("predictor_reloaded", version=version)
        except Exception as exc:
            logger.warning("predictor_reload_failed", error=str(exc))

        return {
            "status": "ok",
            "version": version,
            "metrics": new_metrics,
            "comparison": comparison,
            "saved": True,
        }
    else:
        logger.info(
            "retrain_skipped_worse",
            old_brier=old_brier,
            new_brier=new_brier,
        )
        return {
            "status": "ok",
            "version": old_meta.get("version", "unknown"),
            "metrics": new_metrics,
            "comparison": comparison,
            "saved": False,
            "reason": "New model not better than existing",
        }


# ── CLI entry point ────────────────────────────────────────

if __name__ == "__main__":
    import sys

    result = asyncio.run(run_training_pipeline())
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") == "ok" else 1)

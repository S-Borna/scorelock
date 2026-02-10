"""Tests for the match prediction model and feature engineering."""

import numpy as np
import pytest
from datetime import datetime

from app.ml.predictor import MatchPrediction, MatchPredictor, identify_value_bets
from app.ml.features import (
    FeatureComputer,
    TeamTracker,
    H2HTracker,
    MatchRecord,
    FEATURE_NAMES,
)


# ── Feature Engineering Tests ──────────────────────────────


class TestTeamTracker:
    """Tests for TeamTracker form and stats computation."""

    def _make_tracker_with_matches(self, count: int = 10) -> TeamTracker:
        tracker = TeamTracker()
        for i in range(count):
            tracker.add_match(MatchRecord(
                date=datetime(2025, 1, 1 + i),
                opponent_id=100 + i,
                is_home=(i % 2 == 0),
                goals_for=2 if i % 3 == 0 else 1,
                goals_against=0 if i % 4 == 0 else 1,
                season=2025,
                league_id=39,
            ))
        return tracker

    def test_form_returns_dict_with_keys(self) -> None:
        tracker = self._make_tracker_with_matches()
        form = tracker.get_form(datetime(2025, 1, 15))
        assert "points" in form
        assert "gf" in form
        assert "ga" in form

    def test_form_empty_when_no_prior_matches(self) -> None:
        tracker = TeamTracker()
        form = tracker.get_form(datetime(2025, 1, 1))
        assert form["points"] == 0.0
        assert form["gf"] == 0.0
        assert form["ga"] == 0.0

    def test_form_uses_only_matches_before_date(self) -> None:
        tracker = self._make_tracker_with_matches()
        form_late = tracker.get_form(datetime(2025, 1, 11))
        assert form_late["points"] > 0

    def test_season_stats_returns_dict(self) -> None:
        tracker = self._make_tracker_with_matches()
        stats = tracker.get_season_stats(2025, datetime(2025, 1, 15))
        assert "ppg" in stats
        assert "gf_pg" in stats
        assert "ga_pg" in stats
        assert stats["ppg"] > 0

    def test_home_ppg(self) -> None:
        tracker = self._make_tracker_with_matches()
        ppg = tracker.get_home_ppg(2025, datetime(2025, 1, 15))
        assert isinstance(ppg, float)

    def test_away_ppg(self) -> None:
        tracker = self._make_tracker_with_matches()
        ppg = tracker.get_away_ppg(2025, datetime(2025, 1, 15))
        assert isinstance(ppg, float)

    def test_days_rest_default(self) -> None:
        tracker = TeamTracker()
        rest = tracker.get_days_rest(datetime(2025, 1, 15))
        assert rest == 7

    def test_days_rest_computed(self) -> None:
        tracker = self._make_tracker_with_matches()
        rest = tracker.get_days_rest(datetime(2025, 1, 15))
        assert rest >= 1

    def test_has_enough_data(self) -> None:
        tracker = TeamTracker()
        assert not tracker.has_enough_data(datetime(2025, 1, 1))
        tracker = self._make_tracker_with_matches(count=5)
        assert tracker.has_enough_data(datetime(2025, 1, 15))


class TestH2HTracker:
    """Tests for H2H statistics."""

    def test_empty_h2h(self) -> None:
        h2h = H2HTracker()
        stats = h2h.get_stats(1, 2, datetime(2025, 1, 1))
        assert stats["home_wins"] == 0
        assert stats["draws"] == 0
        assert stats["away_wins"] == 0
        assert stats["avg_goals"] == 2.5

    def test_h2h_counts(self) -> None:
        h2h = H2HTracker()
        h2h.add_match(datetime(2025, 1, 1), 3, 1, 1, 2)
        h2h.add_match(datetime(2025, 1, 8), 1, 1, 2, 1)
        h2h.add_match(datetime(2025, 1, 15), 0, 2, 1, 2)
        stats = h2h.get_stats(1, 2, datetime(2025, 2, 1))
        assert stats["home_wins"] == 1
        assert stats["draws"] == 1
        assert stats["away_wins"] == 1
        assert stats["avg_goals"] == pytest.approx(8 / 3, rel=0.01)


class TestFeatureComputer:
    """Tests for the full feature computation pipeline."""

    def _make_fixtures(self, count: int = 20) -> list[dict]:
        fixtures = []
        for i in range(count):
            fixtures.append({
                "fixture_id": i + 1,
                "home_team_id": 1 if i % 2 == 0 else 2,
                "away_team_id": 2 if i % 2 == 0 else 1,
                "home_goals": (i % 3),
                "away_goals": (i % 2),
                "kickoff": datetime(2025, 1, 1 + i),
                "season": 2025,
                "league_id": 39,
            })
        return fixtures

    def test_training_dataset_shape(self) -> None:
        computer = FeatureComputer()
        fixtures = self._make_fixtures(count=30)
        X, y_result, y_goals = computer.compute_training_dataset(fixtures)
        assert len(X.columns) == len(FEATURE_NAMES)
        assert len(y_result) == len(X)
        assert len(y_goals) == len(X)
        assert len(X) > 0

    def test_feature_names_match(self) -> None:
        computer = FeatureComputer()
        fixtures = self._make_fixtures(count=30)
        X, _, _ = computer.compute_training_dataset(fixtures)
        assert list(X.columns) == FEATURE_NAMES

    def test_compute_match_features_shape(self) -> None:
        computer = FeatureComputer()
        fixtures = self._make_fixtures(count=20)
        computer.populate_from_fixtures(fixtures)
        features = computer.compute_match_features(1, 2, datetime(2025, 2, 1), 2025)
        assert features.shape == (1, 20)

    def test_result_labels(self) -> None:
        computer = FeatureComputer()
        fixtures = self._make_fixtures(count=30)
        _, y_result, _ = computer.compute_training_dataset(fixtures)
        unique = set(y_result.unique())
        assert unique.issubset({0, 1, 2})


# ── Predictor Tests ────────────────────────────────────────


class TestMatchPredictor:
    """Tests for the prediction model serving."""

    def test_unloaded_predictor_raises(self) -> None:
        predictor = MatchPredictor()
        with pytest.raises(RuntimeError, match="Model not loaded"):
            predictor.predict(np.zeros((1, 20)))

    def test_model_version_default(self) -> None:
        predictor = MatchPredictor()
        assert predictor.model_version == "unknown"


class TestMatchPrediction:
    """Tests for MatchPrediction dataclass."""

    def test_probabilities_sum_approximately_one(self) -> None:
        pred = MatchPrediction(
            home_win_prob=0.45,
            draw_prob=0.30,
            away_win_prob=0.25,
            confidence=0.12,
            over_25_prob=0.55,
            expected_goals=2.7,
            model_version="test-v1",
        )
        total = pred.home_win_prob + pred.draw_prob + pred.away_win_prob
        assert abs(total - 1.0) < 0.01


# ── Value Bet Tests ────────────────────────────────────────


class TestValueBets:
    """Tests for value bet identification."""

    def test_value_bet_found_when_model_disagrees(self) -> None:
        prediction = MatchPrediction(
            home_win_prob=0.55,
            draw_prob=0.25,
            away_win_prob=0.20,
            confidence=0.22,
            over_25_prob=0.60,
            expected_goals=2.8,
            model_version="test-v1",
        )
        odds = {"home": 2.10, "draw": 3.40, "away": 3.50}
        result = identify_value_bets(prediction, odds, min_edge=0.05)
        assert result["suggested_bet"] == "home"
        assert result["edge_percent"] > 0
        assert result["is_value_home"] is True

    def test_no_value_bet_when_model_agrees(self) -> None:
        prediction = MatchPrediction(
            home_win_prob=0.33,
            draw_prob=0.33,
            away_win_prob=0.34,
            confidence=0.01,
            over_25_prob=0.50,
            expected_goals=2.5,
            model_version="test-v1",
        )
        odds = {"home": 3.00, "draw": 3.00, "away": 3.00}
        result = identify_value_bets(prediction, odds, min_edge=0.05)
        assert result == {}

    def test_kelly_fraction_capped(self) -> None:
        prediction = MatchPrediction(
            home_win_prob=0.80,
            draw_prob=0.10,
            away_win_prob=0.10,
            confidence=0.47,
            over_25_prob=0.70,
            expected_goals=3.2,
            model_version="test-v1",
        )
        odds = {"home": 3.00, "draw": 4.00, "away": 5.00}
        result = identify_value_bets(prediction, odds, min_edge=0.05)
        assert result["kelly_fraction"] <= 0.25

    def test_value_bet_with_draw_value(self) -> None:
        prediction = MatchPrediction(
            home_win_prob=0.25,
            draw_prob=0.50,
            away_win_prob=0.25,
            confidence=0.17,
            over_25_prob=0.40,
            expected_goals=2.1,
            model_version="test-v1",
        )
        odds = {"home": 2.50, "draw": 4.00, "away": 2.50}
        result = identify_value_bets(prediction, odds, min_edge=0.05)
        if result:
            assert result["is_value_draw"] is True

"""Tests for the match prediction model."""

from app.ml.predictor import MatchFeatures, MatchPrediction, identify_value_bets


def test_match_features_to_array():
    """Feature vector has correct shape."""
    features = MatchFeatures(
        home_form_points=10.0, away_form_points=7.0,
        home_form_goals_scored=1.8, away_form_goals_scored=1.2,
        home_form_goals_conceded=0.8, away_form_goals_conceded=1.4,
        home_xg_for=1.7, home_xg_against=0.9,
        away_xg_for=1.3, away_xg_against=1.5,
        h2h_home_wins=4, h2h_draws=3, h2h_away_wins=3, h2h_avg_goals=2.6,
        home_league_position=3, away_league_position=12,
        home_points=45, away_points=28,
        home_home_record=2.3, away_away_record=0.9,
        home_days_rest=4, away_days_rest=3,
        home_injuries=1, away_injuries=2,
    )
    arr = features.to_array()
    assert arr.shape == (1, 24)


def test_identify_value_bet_found():
    """Value bet detected when model disagrees with bookmaker."""
    prediction = MatchPrediction(
        home_win_prob=0.55,  # Model says 55%
        draw_prob=0.25,
        away_win_prob=0.20,
        confidence=0.22,
        over_25_prob=0.60,
        expected_goals=2.8,
    )
    # Bookmaker implies ~47.6% for home (after removing overround)
    odds = {"home": 2.10, "draw": 3.40, "away": 3.50}

    result = identify_value_bets(prediction, odds, min_edge=0.05)
    assert result["suggested_bet"] == "home"
    assert result["edge_percent"] > 0
    assert result["is_value_home"] is True


def test_identify_value_bet_none():
    """No value bet when model agrees with bookmaker."""
    prediction = MatchPrediction(
        home_win_prob=0.33,
        draw_prob=0.33,
        away_win_prob=0.34,
        confidence=0.01,
        over_25_prob=0.50,
        expected_goals=2.5,
    )
    odds = {"home": 3.00, "draw": 3.00, "away": 3.00}

    result = identify_value_bets(prediction, odds, min_edge=0.05)
    assert result == {}

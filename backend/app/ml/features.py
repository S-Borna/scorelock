"""Feature engineering for match prediction.

Computes feature vectors from historical match data for both
model training (chronological walk-forward) and live prediction serving.

Feature set (20 features):
  - Team form (last 5): points, goals scored/conceded
  - H2H (last 10): wins, draws, avg goals
  - Season stats: PPG, goals per game
  - Home/away splits: PPG at home, PPG away
  - Rest days since last match
"""

import numpy as np
import pandas as pd
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import structlog

logger = structlog.get_logger()

FORM_WINDOW = 5
H2H_WINDOW = 10
MIN_MATCHES_FOR_FEATURES = 3

FEATURE_NAMES = [
    "home_form_points",
    "away_form_points",
    "home_form_gf",
    "away_form_gf",
    "home_form_ga",
    "away_form_ga",
    "h2h_home_wins",
    "h2h_draws",
    "h2h_away_wins",
    "h2h_avg_goals",
    "home_season_ppg",
    "away_season_ppg",
    "home_season_gf_pg",
    "away_season_gf_pg",
    "home_season_ga_pg",
    "away_season_ga_pg",
    "home_home_ppg",
    "away_away_ppg",
    "home_days_rest",
    "away_days_rest",
]


@dataclass
class MatchRecord:
    """A single match result for tracking team history."""

    date: datetime
    opponent_id: int
    is_home: bool
    goals_for: int
    goals_against: int
    season: int
    league_id: int


class TeamTracker:
    """Tracks a team's match history for feature computation."""

    def __init__(self) -> None:
        self.matches: list[MatchRecord] = []

    def add_match(self, record: MatchRecord) -> None:
        self.matches.append(record)

    def get_form(self, before: datetime, n: int = FORM_WINDOW) -> dict:
        """Get form stats from the last N matches before a given date."""
        recent = [m for m in self.matches if m.date < before][-n:]
        if not recent:
            return {"points": 0.0, "gf": 0.0, "ga": 0.0}

        points = sum(
            3
            if m.goals_for > m.goals_against
            else (1 if m.goals_for == m.goals_against else 0)
            for m in recent
        )
        gf = sum(m.goals_for for m in recent) / len(recent)
        ga = sum(m.goals_against for m in recent) / len(recent)
        return {"points": float(points), "gf": gf, "ga": ga}

    def get_season_stats(self, season: int, before: datetime) -> dict:
        """Cumulative season stats before a given date."""
        season_matches = [
            m for m in self.matches if m.season == season and m.date < before
        ]
        if not season_matches:
            return {"ppg": 0.0, "gf_pg": 0.0, "ga_pg": 0.0}

        played = len(season_matches)
        points = sum(
            3
            if m.goals_for > m.goals_against
            else (1 if m.goals_for == m.goals_against else 0)
            for m in season_matches
        )
        gf = sum(m.goals_for for m in season_matches)
        ga = sum(m.goals_against for m in season_matches)
        return {
            "ppg": points / played,
            "gf_pg": gf / played,
            "ga_pg": ga / played,
        }

    def get_home_ppg(self, season: int, before: datetime) -> float:
        """Points per game at home this season."""
        home = [
            m
            for m in self.matches
            if m.season == season and m.is_home and m.date < before
        ]
        if not home:
            return 0.0
        points = sum(
            3
            if m.goals_for > m.goals_against
            else (1 if m.goals_for == m.goals_against else 0)
            for m in home
        )
        return points / len(home)

    def get_away_ppg(self, season: int, before: datetime) -> float:
        """Points per game away this season."""
        away = [
            m
            for m in self.matches
            if m.season == season and not m.is_home and m.date < before
        ]
        if not away:
            return 0.0
        points = sum(
            3
            if m.goals_for > m.goals_against
            else (1 if m.goals_for == m.goals_against else 0)
            for m in away
        )
        return points / len(away)

    def get_days_rest(self, before: datetime) -> int:
        """Days since last match."""
        prior = [m for m in self.matches if m.date < before]
        if not prior:
            return 7  # Default
        return max(1, (before - prior[-1].date).days)

    def has_enough_data(self, before: datetime) -> bool:
        """Check if team has enough data for feature computation."""
        prior = [m for m in self.matches if m.date < before]
        return len(prior) >= MIN_MATCHES_FOR_FEATURES


class H2HTracker:
    """Tracks head-to-head history between two teams."""

    def __init__(self) -> None:
        # (date, home_goals, away_goals, home_team_id, away_team_id)
        self.matches: list[tuple[datetime, int, int, int, int]] = []

    def add_match(
        self,
        date: datetime,
        home_goals: int,
        away_goals: int,
        home_id: int,
        away_id: int,
    ) -> None:
        self.matches.append((date, home_goals, away_goals, home_id, away_id))

    def get_stats(
        self,
        home_team_id: int,
        away_team_id: int,
        before: datetime,
        n: int = H2H_WINDOW,
    ) -> dict:
        """H2H stats from the perspective of the current home team."""
        recent = [m for m in self.matches if m[0] < before][-n:]
        if not recent:
            return {"home_wins": 0, "draws": 0, "away_wins": 0, "avg_goals": 2.5}

        home_wins = 0
        away_wins = 0
        draws = 0
        total_goals = 0

        for _date, hg, ag, hid, _aid in recent:
            total_goals += hg + ag
            if hg == ag:
                draws += 1
            elif (hid == home_team_id and hg > ag) or (hid != home_team_id and ag > hg):
                home_wins += 1
            else:
                away_wins += 1

        return {
            "home_wins": home_wins,
            "draws": draws,
            "away_wins": away_wins,
            "avg_goals": total_goals / len(recent),
        }


class FeatureComputer:
    """Computes feature vectors from match data.

    For training: processes fixtures chronologically, maintaining running state.
    For prediction: computes features for upcoming matches using current DB state.
    """

    def __init__(self) -> None:
        self.team_trackers: dict[int, TeamTracker] = defaultdict(TeamTracker)
        self.h2h_trackers: dict[frozenset, H2HTracker] = defaultdict(H2HTracker)

    def compute_training_dataset(
        self,
        fixtures: list[dict],
    ) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
        """Build training dataset from chronologically sorted finished fixtures.

        Args:
            fixtures: List of dicts with keys:
                home_team_id, away_team_id, home_goals, away_goals,
                kickoff (datetime), season (int), league_id (int)

        Returns:
            X: Feature matrix (DataFrame)
            y_result: Match results (0=Home, 1=Draw, 2=Away)
            y_goals: Total goals per match
        """
        rows: list[list[float]] = []
        results: list[int] = []
        goals: list[int] = []

        fixtures = sorted(fixtures, key=lambda f: f["kickoff"])

        for fix in fixtures:
            home_id = fix["home_team_id"]
            away_id = fix["away_team_id"]
            kickoff = fix["kickoff"]
            season = fix["season"]
            home_goals = fix["home_goals"]
            away_goals = fix["away_goals"]

            home_tracker = self.team_trackers[home_id]
            away_tracker = self.team_trackers[away_id]

            # Only compute features if both teams have enough history
            if home_tracker.has_enough_data(kickoff) and away_tracker.has_enough_data(
                kickoff
            ):
                features = self._compute_features(home_id, away_id, kickoff, season)
                rows.append(features)

                # Target: result
                if home_goals > away_goals:
                    results.append(0)
                elif home_goals == away_goals:
                    results.append(1)
                else:
                    results.append(2)

                goals.append(home_goals + away_goals)

            # Always update trackers (even if we didn't compute features)
            self._record_match(fix)

        X = pd.DataFrame(rows, columns=FEATURE_NAMES)
        y_result = pd.Series(results, name="result")
        y_goals = pd.Series(goals, name="total_goals")

        logger.info(
            "training_dataset_built",
            total_fixtures=len(fixtures),
            training_samples=len(rows),
            skipped=len(fixtures) - len(rows),
        )

        return X, y_result, y_goals

    def compute_match_features(
        self,
        home_team_id: int,
        away_team_id: int,
        kickoff: datetime,
        season: int,
    ) -> np.ndarray:
        """Compute feature vector for a single upcoming match.

        The trackers must be populated with recent matches first
        (call populate_from_fixtures).

        Returns: 2D numpy array of shape (1, 20)
        """
        features = self._compute_features(home_team_id, away_team_id, kickoff, season)
        return np.array(features).reshape(1, -1)

    def populate_from_fixtures(self, fixtures: list[dict]) -> None:
        """Populate trackers from a list of finished fixtures.

        Use this to set up state before computing features for upcoming matches.
        """
        for fix in sorted(fixtures, key=lambda f: f["kickoff"]):
            self._record_match(fix)

    # ── Internal ───────────────────────────────────────────

    def _record_match(self, fix: dict) -> None:
        """Record a single match into team and H2H trackers."""
        home_id = fix["home_team_id"]
        away_id = fix["away_team_id"]
        kickoff = fix["kickoff"]
        season = fix["season"]
        home_goals = fix["home_goals"]
        away_goals = fix["away_goals"]

        self.team_trackers[home_id].add_match(
            MatchRecord(
                date=kickoff,
                opponent_id=away_id,
                is_home=True,
                goals_for=home_goals,
                goals_against=away_goals,
                season=season,
                league_id=fix["league_id"],
            )
        )
        self.team_trackers[away_id].add_match(
            MatchRecord(
                date=kickoff,
                opponent_id=home_id,
                is_home=False,
                goals_for=away_goals,
                goals_against=home_goals,
                season=season,
                league_id=fix["league_id"],
            )
        )

        h2h_key = frozenset([home_id, away_id])
        self.h2h_trackers[h2h_key].add_match(
            kickoff,
            home_goals,
            away_goals,
            home_id,
            away_id,
        )

    def _compute_features(
        self,
        home_id: int,
        away_id: int,
        kickoff: datetime,
        season: int,
    ) -> list[float]:
        """Compute the 20-dimensional feature vector."""
        home = self.team_trackers[home_id]
        away = self.team_trackers[away_id]
        h2h_key = frozenset([home_id, away_id])
        h2h = self.h2h_trackers[h2h_key]

        home_form = home.get_form(kickoff)
        away_form = away.get_form(kickoff)

        h2h_stats = h2h.get_stats(home_id, away_id, kickoff)

        home_season = home.get_season_stats(season, kickoff)
        away_season = away.get_season_stats(season, kickoff)

        home_home_ppg = home.get_home_ppg(season, kickoff)
        away_away_ppg = away.get_away_ppg(season, kickoff)

        home_rest = home.get_days_rest(kickoff)
        away_rest = away.get_days_rest(kickoff)

        return [
            home_form["points"],
            away_form["points"],
            home_form["gf"],
            away_form["gf"],
            home_form["ga"],
            away_form["ga"],
            float(h2h_stats["home_wins"]),
            float(h2h_stats["draws"]),
            float(h2h_stats["away_wins"]),
            h2h_stats["avg_goals"],
            home_season["ppg"],
            away_season["ppg"],
            home_season["gf_pg"],
            away_season["gf_pg"],
            home_season["ga_pg"],
            away_season["ga_pg"],
            home_home_ppg,
            away_away_ppg,
            float(min(home_rest, 30)),
            float(min(away_rest, 30)),
        ]

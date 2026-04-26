"""Fantasy points scoring engine — Premier League Fantasy-style rules.

Pure function: takes a player's gameweek stats dict + position code,
returns total fantasy points. Bonus points (BPS) are added separately
post-match by the GW-finalize task.
"""

POSITION_GK = "GK"
POSITION_DEF = "DEF"
POSITION_MID = "MID"
POSITION_FWD = "FWD"

GOAL_POINTS = {
    POSITION_GK: 6,
    POSITION_DEF: 6,
    POSITION_MID: 5,
    POSITION_FWD: 4,
}

ASSIST_POINTS = 3
CLEAN_SHEET_POINTS = {
    POSITION_GK: 4,
    POSITION_DEF: 4,
    POSITION_MID: 1,
    POSITION_FWD: 0,
}
SAVES_PER_POINT = 3
PENALTY_SAVED_POINTS = 5
PENALTY_MISSED_POINTS = -2
OWN_GOAL_POINTS = -2
YELLOW_CARD_POINTS = -1
RED_CARD_POINTS = -3
GOALS_CONCEDED_PER_PENALTY = 2
APPEARANCE_FULL_THRESHOLD = 60


def _normalize_position(position_code: str | None) -> str:
    """Coerce raw position codes into one of GK/DEF/MID/FWD."""
    if not position_code:
        return POSITION_MID
    code = position_code.upper().strip()
    if code in {"GK", "G", "GOALKEEPER"}:
        return POSITION_GK
    if code in {"DEF", "D", "DEFENDER", "CB", "LCB", "RCB", "LB", "RB", "WB"}:
        return POSITION_DEF
    if code in {
        "MID",
        "M",
        "MIDFIELDER",
        "CM",
        "DM",
        "AM",
        "LCM",
        "RCM",
        "LM",
        "RM",
        "LAM",
        "RAM",
        "LDM",
        "RDM",
        "CAM",
    }:
        return POSITION_MID
    if code in {"FWD", "F", "FORWARD", "ST", "CF", "LW", "RW", "WG"}:
        return POSITION_FWD
    return POSITION_MID


def compute_points(stats: dict, position_code: str | None) -> int:
    """Calculate fantasy points for one player in one fixture.

    Args:
        stats: Raw stats dict with keys minutes_played, goals, assists,
            clean_sheet, yellow_cards, red_cards, saves, goals_conceded,
            own_goals, penalties_missed, penalties_saved, bonus_points.
        position_code: Player's position string (raw — normalized internally).

    Returns:
        Total fantasy points (int, can be negative).
    """
    pos = _normalize_position(position_code)
    minutes = int(stats.get("minutes_played") or 0)

    if minutes <= 0:
        return 0

    points = 0

    # Appearance
    if minutes >= APPEARANCE_FULL_THRESHOLD:
        points += 2
    else:
        points += 1

    # Goals
    goals = int(stats.get("goals") or 0)
    points += goals * GOAL_POINTS[pos]

    # Assists
    assists = int(stats.get("assists") or 0)
    points += assists * ASSIST_POINTS

    # Clean sheet — only if played >= 60 min
    if stats.get("clean_sheet") and minutes >= APPEARANCE_FULL_THRESHOLD:
        points += CLEAN_SHEET_POINTS[pos]

    # Goals conceded — penalty for GK/DEF (every 2 conceded = -1)
    if pos in {POSITION_GK, POSITION_DEF}:
        conceded = int(stats.get("goals_conceded") or 0)
        points -= conceded // GOALS_CONCEDED_PER_PENALTY

    # Saves — GK only
    if pos == POSITION_GK:
        saves = int(stats.get("saves") or 0)
        points += saves // SAVES_PER_POINT

    # Penalty events
    points += int(stats.get("penalties_saved") or 0) * PENALTY_SAVED_POINTS
    points += int(stats.get("penalties_missed") or 0) * PENALTY_MISSED_POINTS

    # Negative events
    points += int(stats.get("own_goals") or 0) * OWN_GOAL_POINTS
    points += int(stats.get("yellow_cards") or 0) * YELLOW_CARD_POINTS
    points += int(stats.get("red_cards") or 0) * RED_CARD_POINTS

    # Bonus points (BPS — added by GW-finalize task)
    points += int(stats.get("bonus_points") or 0)

    return points

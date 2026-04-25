/**
 * TypeScript types mirroring backend Pydantic schemas.
 */

export interface League {
    id: number;
    name: string;
    country: string;
    logo_url: string | null;
    type: string;
    current_season: number | null;
}

export interface Team {
    id: number;
    name: string;
    short_name: string | null;
    logo_url: string | null;
    country: string | null;
}

export interface Fixture {
    id: number;
    league: League;
    home_team: Team;
    away_team: Team;
    kickoff: string;
    status: "scheduled" | "live" | "halftime" | "finished" | "postponed" | "cancelled";
    home_goals: number | null;
    away_goals: number | null;
    round: string | null;
}

export interface FixtureDetail extends Fixture {
    home_goals_ht: number | null;
    away_goals_ht: number | null;
    stats: Record<string, unknown> | null;
    prediction: Prediction | null;
    odds: Odds[];
}

export interface Prediction {
    fixture_id: number;
    home_win_prob: number;
    draw_prob: number;
    away_win_prob: number;
    confidence: number;
    over_25_prob: number | null;
    expected_goals: number | null;
    is_value_home: boolean;
    is_value_draw: boolean;
    is_value_away: boolean;
    value_edge: number | null;
    model_version: string;
    created_at: string;
}

export interface Odds {
    bookmaker: string;
    market: string;
    home_odds: number | null;
    draw_odds: number | null;
    away_odds: number | null;
    over_odds: number | null;
    under_odds: number | null;
    line: number | null;
    fetched_at: string;
}

export interface ValueBet {
    fixture: Fixture;
    prediction: Prediction;
    best_odds: Odds;
    edge_percent: number;
    suggested_bet: string;
    kelly_fraction: number;
}

export interface Standing {
    position: number;
    team: Team;
    points: number;
    played: number;
    won: number;
    drawn: number;
    lost: number;
    goals_for: number;
    goals_against: number;
    goal_diff: number;
    form: string | null;
    xg_for: number | null;
    xg_against: number | null;
}

export interface Sentiment {
    team_id: number;
    score: number;
    buzz_score: number;
    source: string;
    summary: string | null;
    analyzed_at: string;
}

export interface User {
    id: number;
    email: string;
    name: string | null;
    tier: "free" | "pro" | "elite";
    created_at: string;
}

export interface AuthToken {
    access_token: string;
    token_type: string;
}

export interface Article {
    id: number;
    type: string;
    slug: string;
    title: string;
    summary: string | null;
    body: string;
    language: string;
    league_id: number | null;
    fixture_id: number | null;
    round: string | null;
    tags: string[] | null;
    auto_generated: boolean;
    published_at: string | null;
}

export interface ArticleList {
    articles: Article[];
    total: number;
    limit: number;
    offset: number;
}


// ── Tipping League ───────────────────────────────────────

export interface UserPrediction {
    id: number;
    user_id: number;
    fixture_id: number;
    predicted_outcome: "H" | "D" | "A";
    predicted_home_goals: number | null;
    predicted_away_goals: number | null;
    points_earned: number | null;
    was_correct_outcome: boolean | null;
    was_exact_score: boolean | null;
    created_at: string;
    fixture?: Fixture;
}

export interface LeaderboardEntry {
    user_id: number;
    user_name: string | null;
    total_points: number;
    total_tips: number;
    correct_outcomes: number;
    exact_scores: number;
    accuracy: number;
    current_streak: number;
}

export interface AIvsUserStats {
    user_total_points: number;
    user_total_tips: number;
    user_accuracy: number;
    ai_correct: number;
    ai_total: number;
    ai_accuracy: number;
    user_wins: number;
    ai_wins: number;
    ties: number;
}

export interface WeeklyTopTipper {
    user_id: number;
    user_name: string | null;
    points_this_week: number;
    tips_this_week: number;
    accuracy_this_week: number;
}


// ── Broadcasts (Phase 1: Where to Watch) ─────────────────

export interface Broadcast {
    id: number;
    provider_type: "TV" | "STREAMING" | "RADIO";
    channel_name: string;
    watch_url: string | null;
    language_iso_2: string | null;
    country_iso_2: string;
}

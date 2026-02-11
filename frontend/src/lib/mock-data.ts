/**
 * Mock data for offline/dev mode when backend is unavailable.
 * Allows the frontend to render with realistic sample data.
 */

import type {
    Article,
    ArticleList,
    Fixture,
    FixtureDetail,
    League,
    LeaderboardEntry,
    Odds,
    Prediction,
    Sentiment,
    Standing,
    Team,
    ValueBet,
    WeeklyTopTipper,
} from "./types";

// ── Leagues ──────────────────────────────────────────────

const PL: League = { id: 1, name: "Premier League", country: "England", logo_url: null, type: "league", current_season: 2025 };
const LL: League = { id: 2, name: "La Liga", country: "Spain", logo_url: null, type: "league", current_season: 2025 };
const SA: League = { id: 3, name: "Serie A", country: "Italy", logo_url: null, type: "league", current_season: 2025 };
const ALL: League = { id: 5, name: "Allsvenskan", country: "Sweden", logo_url: null, type: "league", current_season: 2025 };

// ── Teams ────────────────────────────────────────────────

const teams: Record<string, Team> = {
    arsenal: { id: 1, name: "Arsenal", short_name: "ARS", logo_url: null, country: "England" },
    chelsea: { id: 2, name: "Chelsea", short_name: "CHE", logo_url: null, country: "England" },
    liverpool: { id: 3, name: "Liverpool", short_name: "LIV", logo_url: null, country: "England" },
    mancity: { id: 4, name: "Manchester City", short_name: "MCI", logo_url: null, country: "England" },
    tottenham: { id: 5, name: "Tottenham", short_name: "TOT", logo_url: null, country: "England" },
    manunited: { id: 6, name: "Manchester United", short_name: "MUN", logo_url: null, country: "England" },
    realmadrid: { id: 10, name: "Real Madrid", short_name: "RMA", logo_url: null, country: "Spain" },
    barcelona: { id: 11, name: "Barcelona", short_name: "BAR", logo_url: null, country: "Spain" },
    juventus: { id: 20, name: "Juventus", short_name: "JUV", logo_url: null, country: "Italy" },
    acmilan: { id: 21, name: "AC Milan", short_name: "MIL", logo_url: null, country: "Italy" },
    malmoff: { id: 30, name: "Malmö FF", short_name: "MFF", logo_url: null, country: "Sweden" },
    aik: { id: 31, name: "AIK", short_name: "AIK", logo_url: null, country: "Sweden" },
    hammarby: { id: 32, name: "Hammarby", short_name: "HIF", logo_url: null, country: "Sweden" },
    djurgarden: { id: 33, name: "Djurgårdens IF", short_name: "DIF", logo_url: null, country: "Sweden" },
};

// ── Helpers ──────────────────────────────────────────────

const now = new Date();
const tomorrow = new Date(now.getTime() + 86400000);
const dayAfter = new Date(now.getTime() + 2 * 86400000);
const yesterday = new Date(now.getTime() - 86400000);

function isoDate(d: Date, hour = 15, min = 0): string {
    const copy = new Date(d);
    copy.setHours(hour, min, 0, 0);
    return copy.toISOString();
}

// ── Fixtures ─────────────────────────────────────────────

const mockFixtures: Fixture[] = [
    { id: 1001, league: PL, home_team: teams.arsenal, away_team: teams.chelsea, kickoff: isoDate(tomorrow, 16), status: "scheduled", home_goals: null, away_goals: null, round: "Omgång 25" },
    { id: 1002, league: PL, home_team: teams.liverpool, away_team: teams.mancity, kickoff: isoDate(tomorrow, 18, 30), status: "scheduled", home_goals: null, away_goals: null, round: "Omgång 25" },
    { id: 1003, league: LL, home_team: teams.realmadrid, away_team: teams.barcelona, kickoff: isoDate(dayAfter, 21), status: "scheduled", home_goals: null, away_goals: null, round: "Omgång 23" },
    { id: 1004, league: SA, home_team: teams.juventus, away_team: teams.acmilan, kickoff: isoDate(dayAfter, 20, 45), status: "scheduled", home_goals: null, away_goals: null, round: "Omgång 24" },
    { id: 1005, league: ALL, home_team: teams.malmoff, away_team: teams.hammarby, kickoff: isoDate(dayAfter, 15), status: "scheduled", home_goals: null, away_goals: null, round: "Omgång 3" },
    { id: 1006, league: PL, home_team: teams.tottenham, away_team: teams.manunited, kickoff: isoDate(yesterday, 15), status: "finished", home_goals: 2, away_goals: 1, round: "Omgång 24" },
    { id: 1007, league: ALL, home_team: teams.aik, away_team: teams.djurgarden, kickoff: isoDate(yesterday, 19), status: "finished", home_goals: 1, away_goals: 1, round: "Omgång 2" },
];

// ── Predictions ──────────────────────────────────────────

function mockPrediction(fixtureId: number, h: number, d: number, a: number): Prediction {
    return {
        fixture_id: fixtureId,
        home_win_prob: h,
        draw_prob: d,
        away_win_prob: a,
        confidence: Math.max(h, d, a),
        over_25_prob: 0.58,
        expected_goals: 2.7,
        is_value_home: h > 0.5,
        is_value_draw: false,
        is_value_away: a > 0.5,
        value_edge: 4.2,
        model_version: "v20260210-demo",
        created_at: now.toISOString(),
    };
}

// ── Odds ─────────────────────────────────────────────────

function mockOdds(bk: string, h: number, d: number, a: number): Odds {
    return { bookmaker: bk, market: "1X2", home_odds: h, draw_odds: d, away_odds: a, over_odds: null, under_odds: null, line: null, fetched_at: now.toISOString() };
}

// ── Fixture Details ──────────────────────────────────────

const mockFixtureDetails: Record<number, FixtureDetail> = {
    1001: {
        ...mockFixtures[0],
        home_goals_ht: null, away_goals_ht: null, stats: null,
        prediction: mockPrediction(1001, 0.52, 0.24, 0.24),
        odds: [mockOdds("Bet365", 1.95, 3.40, 4.00), mockOdds("Unibet", 1.90, 3.50, 4.10)],
    },
    1002: {
        ...mockFixtures[1],
        home_goals_ht: null, away_goals_ht: null, stats: null,
        prediction: mockPrediction(1002, 0.38, 0.28, 0.34),
        odds: [mockOdds("Bet365", 2.60, 3.30, 2.70), mockOdds("Betsson", 2.55, 3.35, 2.75)],
    },
    1006: {
        ...mockFixtures[5],
        home_goals_ht: 1, away_goals_ht: 0, stats: null,
        prediction: mockPrediction(1006, 0.45, 0.27, 0.28),
        odds: [mockOdds("Unibet", 2.10, 3.40, 3.50)],
    },
};

// ── Articles ─────────────────────────────────────────────

const mockArticles: Article[] = [
    {
        id: 1, type: "MATCH_PREVIEW", slug: "arsenal-vs-chelsea-forhandsanalys",
        title: "Arsenal vs Chelsea — Söndagens stormatch",
        summary: "Arsenal har vunnit fyra raka hemma och släppt in bara två mål. Chelsea saknar Palmer och Caicedo.",
        body: `## Arsenal vs Chelsea — Förhandsanalys\n\nArsenal har vunnit fyra raka hemmamatcher och släppt in bara två mål under den perioden. Chelsea å sin sida saknar Cole Palmer och Moisés Caicedo genom skador.\n\n### Form\nArsenal: VVVVO (senaste 5)\nChelsea: VOFÖV (senaste 5)\n\n### H2H\nHistoriskt har Arsenal tagit 7 av 9 poäng i de senaste hemmadrabbningarna mot Chelsea.\n\n### Odds & Value\nMed odds 1.95 på hemmaseger — där vår modell ger 52% sannolikhet mot bookmakers implicita 51% — finns ett litet edge.\n\n### ScoreLocks prognos\n**Arsenal 2–1 Chelsea**\n\nFormkurvan och hemmastatistiken talar starkt för Arsenal.`,
        language: "sv", league_id: 1, fixture_id: 1001, round: "Omgång 25",
        tags: ["Arsenal", "Chelsea", "Premier League"], auto_generated: true,
        published_at: new Date(now.getTime() - 3600000).toISOString(),
    },
    {
        id: 2, type: "VALUE_BET_ALERT", slug: "value-bets-11-feb",
        title: "💰 Dagens Value Bets — 11 februari",
        summary: "Tre intressanta value bets med positivt edge enligt vår ML-modell.",
        body: `## Dagens Value Bets\n\n### 1. Arsenal ML @ 1.95 (Edge: +4.2%)\nVår modell ger Arsenal 52% sannolikhet, bookmakers prisar in 51.3%. Litet men stabilt edge.\n\n### 2. Liverpool vs Man City — Över 2.5 @ 1.75 (Edge: +6.1%)\nBåda lagen har snittat 3.2 mål per match senaste 5 omgångarna.\n\n### 3. Malmö FF ML @ 2.10 (Edge: +3.8%)\nMalmö hemma mot Hammarby — historiskt stark hemma, undervärderade av marknaden.\n\n---\n*Kelly Criterion: Satsa 2-4% av bankrullen per bet.*\n*Spela ansvarsfullt. 18+.*`,
        language: "sv", league_id: null, fixture_id: null, round: null,
        tags: ["Value Bets", "Arsenal", "Liverpool", "Malmö FF"], auto_generated: true,
        published_at: new Date(now.getTime() - 7200000).toISOString(),
    },
    {
        id: 3, type: "MATCH_REPORT", slug: "tottenham-manchester-united-referat",
        title: "Tottenham 2–1 Manchester United — Son avgjorde",
        summary: "Son Heung-min satte 2-1 i 78:e minuten och säkrade tre poäng för Spurs.",
        body: `## Tottenham 2–1 Manchester United\n\n### Matchreferat\nTottenham tog ledningen redan i den 12:e minuten genom Richarlison som nickade in ett inlägg från Udogie. United svarade genom Rashford i den 35:e minuten efter en snabb omställning.\n\nAndra halvlek var jämn tills Son Heung-min avgjorde i den 78:e minuten med ett välplacerat avslut från straffområdets kant.\n\n### Nyckelmoment\n- 12' Richarlison 1-0 (Udogie assist)\n- 35' Rashford 1-1 (Garnacho assist)\n- 78' Son 2-1\n\n### Tabellpåverkan\nTottenham klättrar till 5:e plats, United ligger kvar på 8:e.`,
        language: "sv", league_id: 1, fixture_id: 1006, round: "Omgång 24",
        tags: ["Tottenham", "Manchester United", "Premier League"], auto_generated: true,
        published_at: new Date(now.getTime() - 43200000).toISOString(),
    },
    {
        id: 4, type: "ROUND_SUMMARY", slug: "premier-league-omgang-24-sammanfattning",
        title: "Premier League Omgång 24 — Tabelltoppen tätnar",
        summary: "Arsenal och Liverpool vann medan City tappade poäng igen. Allsvenskan drar igång.",
        body: `## Premier League Omgång 24\n\n### Omgångens berättelse\nTabelltoppen i Premier League fortsätter att tätna. Arsenal och Liverpool säkrade alla tre poäng medan Manchester City återigen tappade poäng.\n\n### Omgångens hjälte\n🌟 **Son Heung-min** — Avgjorde Londonlaget mot United med ett strålande mål.\n\n### Omgångens besvikelse\n😞 **Manchester City** — Fortsätter sin svaga form och har nu bara 2 segrar på de senaste 8 matcherna.\n\n### Tabelltoppen\n1. Arsenal — 58p\n2. Liverpool — 55p\n3. Chelsea — 49p\n4. Man City — 47p\n\n### Nästa omgång\nStormatch: Arsenal vs Chelsea och Liverpool vs Man City i omgång 25.`,
        language: "sv", league_id: 1, fixture_id: null, round: "Omgång 24",
        tags: ["Premier League", "Omgång 24"], auto_generated: true,
        published_at: new Date(now.getTime() - 86400000).toISOString(),
    },
    {
        id: 5, type: "MATCH_PREVIEW", slug: "real-madrid-barcelona-el-clasico",
        title: "El Clásico — Real Madrid vs Barcelona",
        summary: "Säsongens första El Clásico avgörs på Santiago Bernabéu. Vinicius Jr mot Yamal.",
        body: `## El Clásico — Real Madrid vs Barcelona\n\nSäsongens mest efterlängtade match spelas på Santiago Bernabéu.\n\n### Form\nReal Madrid: VVVVV\nBarcelona: VVOVV\n\n### Nyckelmatchup\nVinicius Jr vs Lamine Yamal — generationernas möte på var sin flygel.\n\n### ScoreLocks prognos\n**Real Madrid 2–2 Barcelona**`,
        language: "sv", league_id: 2, fixture_id: 1003, round: "Omgång 23",
        tags: ["Real Madrid", "Barcelona", "La Liga", "El Clásico"], auto_generated: true,
        published_at: new Date(now.getTime() - 1800000).toISOString(),
    },
    {
        id: 6, type: "MATCH_PREVIEW", slug: "malmo-ff-hammarby-allsvenskan",
        title: "Malmö FF vs Hammarby — Tidigt topp-möte",
        summary: "Allsvenskan omgång 3: Malmö FF tar emot Hammarby på Eleda Stadion.",
        body: `## Malmö FF vs Hammarby\n\nAllsvenskans tredje omgång bjuder på ett tidigt toppmöte.\n\n### ScoreLocks prognos\n**Malmö FF 2–0 Hammarby**`,
        language: "sv", league_id: 5, fixture_id: 1005, round: "Omgång 3",
        tags: ["Malmö FF", "Hammarby", "Allsvenskan"], auto_generated: true,
        published_at: new Date(now.getTime() - 5400000).toISOString(),
    },
];

// ── Standings ────────────────────────────────────────────

const mockStandings: Record<number, Standing[]> = {
    1: [ // Premier League
        { position: 1, team: teams.arsenal, points: 58, played: 24, won: 18, drawn: 4, lost: 2, goals_for: 52, goals_against: 18, goal_diff: 34, form: "VVVVO", xg_for: 48.2, xg_against: 20.1 },
        { position: 2, team: teams.liverpool, points: 55, played: 24, won: 17, drawn: 4, lost: 3, goals_for: 55, goals_against: 22, goal_diff: 33, form: "VVVVV", xg_for: 50.1, xg_against: 23.5 },
        { position: 3, team: teams.chelsea, points: 49, played: 24, won: 15, drawn: 4, lost: 5, goals_for: 48, goals_against: 28, goal_diff: 20, form: "VOFÖV", xg_for: 44.3, xg_against: 26.8 },
        { position: 4, team: teams.mancity, points: 47, played: 24, won: 14, drawn: 5, lost: 5, goals_for: 50, goals_against: 25, goal_diff: 25, form: "OOVVF", xg_for: 52.0, xg_against: 22.0 },
        { position: 5, team: teams.tottenham, points: 42, played: 24, won: 13, drawn: 3, lost: 8, goals_for: 45, goals_against: 32, goal_diff: 13, form: "VVFOV", xg_for: 40.5, xg_against: 30.2 },
        { position: 6, team: teams.manunited, points: 35, played: 24, won: 10, drawn: 5, lost: 9, goals_for: 32, goals_against: 35, goal_diff: -3, form: "FOVFV", xg_for: 30.2, xg_against: 33.8 },
    ],
    5: [ // Allsvenskan
        { position: 1, team: teams.malmoff, points: 7, played: 2, won: 2, drawn: 1, lost: 0, goals_for: 5, goals_against: 1, goal_diff: 4, form: "VVO", xg_for: 4.8, xg_against: 1.2 },
        { position: 2, team: teams.djurgarden, points: 5, played: 2, won: 1, drawn: 2, lost: 0, goals_for: 3, goals_against: 2, goal_diff: 1, form: "VOO", xg_for: 3.5, xg_against: 2.0 },
        { position: 3, team: teams.hammarby, points: 4, played: 2, won: 1, drawn: 1, lost: 1, goals_for: 4, goals_against: 3, goal_diff: 1, form: "VFO", xg_for: 3.2, xg_against: 3.0 },
        { position: 4, team: teams.aik, points: 2, played: 2, won: 0, drawn: 2, lost: 1, goals_for: 2, goals_against: 3, goal_diff: -1, form: "OOF", xg_for: 2.1, xg_against: 2.8 },
    ],
};

// ── Sentiment ────────────────────────────────────────────

function mockSentiment(teamId: number, score: number, buzz: number): Sentiment {
    return { team_id: teamId, score, buzz_score: buzz, source: "mock", summary: null, analyzed_at: now.toISOString() };
}

const mockSentiments: Record<number, Sentiment[]> = {
    1: [mockSentiment(1, 0.72, 85)],
    2: [mockSentiment(2, 0.45, 70)],
    3: [mockSentiment(3, 0.81, 90)],
    4: [mockSentiment(4, 0.35, 75)],
    30: [mockSentiment(30, 0.68, 60)],
    31: [mockSentiment(31, 0.42, 55)],
    32: [mockSentiment(32, 0.55, 50)],
    33: [mockSentiment(33, 0.60, 58)],
};

// ── Value Bets ───────────────────────────────────────────

const mockValueBets: ValueBet[] = [
    {
        fixture: mockFixtures[0],
        prediction: mockPrediction(1001, 0.52, 0.24, 0.24),
        best_odds: mockOdds("Bet365", 1.95, 3.40, 4.00),
        edge_percent: 4.2,
        suggested_bet: "Hemma (Arsenal)",
        kelly_fraction: 0.032,
    },
    {
        fixture: mockFixtures[1],
        prediction: mockPrediction(1002, 0.38, 0.28, 0.34),
        best_odds: mockOdds("Unibet", 2.60, 3.30, 2.70),
        edge_percent: 6.1,
        suggested_bet: "Över 2.5 mål",
        kelly_fraction: 0.045,
    },
    {
        fixture: mockFixtures[4],
        prediction: mockPrediction(1005, 0.49, 0.26, 0.25),
        best_odds: mockOdds("Betsson", 2.10, 3.30, 3.50),
        edge_percent: 3.8,
        suggested_bet: "Hemma (Malmö FF)",
        kelly_fraction: 0.028,
    },
];

// ── Affiliate Links ──────────────────────────────────────

const mockAffiliateLinks = [
    { id: 1, bookmaker: "bet365", bookmaker_display: "Bet365", logo_url: null, base_url: "https://www.bet365.com", tracking_id: "scorelock_demo", market: "1X2", country: "SE", priority: 100 },
    { id: 2, bookmaker: "unibet", bookmaker_display: "Unibet", logo_url: null, base_url: "https://www.unibet.se", tracking_id: "scorelock_demo", market: "1X2", country: "SE", priority: 90 },
    { id: 3, bookmaker: "betsson", bookmaker_display: "Betsson", logo_url: null, base_url: "https://www.betsson.com", tracking_id: "scorelock_demo", market: "1X2", country: "SE", priority: 80 },
    { id: 4, bookmaker: "leovegas", bookmaker_display: "LeoVegas", logo_url: null, base_url: "https://www.leovegas.se", tracking_id: "scorelock_demo", market: "1X2", country: "SE", priority: 70 },
];

// ── Leaderboard ──────────────────────────────────────────

const mockLeaderboard: LeaderboardEntry[] = [
    { user_id: 1, user_name: "FotbollsFansen92", total_points: 47, total_tips: 28, correct_outcomes: 19, exact_scores: 4, accuracy: 67.9, current_streak: 3 },
    { user_id: 2, user_name: "OddsMästaren", total_points: 41, total_tips: 30, correct_outcomes: 17, exact_scores: 3, accuracy: 56.7, current_streak: 1 },
    { user_id: 3, user_name: "AISlayer", total_points: 38, total_tips: 25, correct_outcomes: 16, exact_scores: 3, accuracy: 64.0, current_streak: 5 },
    { user_id: 4, user_name: "StockholmTipset", total_points: 35, total_tips: 32, correct_outcomes: 15, exact_scores: 2, accuracy: 46.9, current_streak: 0 },
    { user_id: 5, user_name: "MalmöBansen", total_points: 29, total_tips: 20, correct_outcomes: 13, exact_scores: 2, accuracy: 65.0, current_streak: 2 },
    { user_id: 6, user_name: "GöteborgTipp", total_points: 25, total_tips: 22, correct_outcomes: 11, exact_scores: 1, accuracy: 50.0, current_streak: 0 },
    { user_id: 7, user_name: "PLExpert", total_points: 22, total_tips: 18, correct_outcomes: 10, exact_scores: 1, accuracy: 55.6, current_streak: 1 },
    { user_id: 8, user_name: "BetSmart", total_points: 19, total_tips: 15, correct_outcomes: 9, exact_scores: 1, accuracy: 60.0, current_streak: 0 },
];

const mockWeeklyTop: WeeklyTopTipper = {
    user_id: 3,
    user_name: "AISlayer",
    points_this_week: 12,
    tips_this_week: 6,
    accuracy_this_week: 83.3,
};

// ── Route resolver ───────────────────────────────────────

/**
 * Given an API path, return mock data or null if no mock exists.
 */
export function getMockData(path: string): unknown | null {
    // Strip query params for matching
    const [basePath] = path.split("?");

    // Articles
    if (basePath === "/api/v1/articles") {
        return { articles: mockArticles, total: mockArticles.length, limit: 20, offset: 0 } satisfies ArticleList;
    }
    if (basePath.startsWith("/api/v1/articles/")) {
        const slug = basePath.replace("/api/v1/articles/", "");
        return mockArticles.find((a) => a.slug === slug) ?? mockArticles[0];
    }

    // Fixtures
    if (basePath === "/api/v1/fixtures" || basePath === "/api/v1/fixtures/upcoming") {
        return mockFixtures;
    }
    if (basePath.startsWith("/api/v1/fixtures/")) {
        const id = parseInt(basePath.replace("/api/v1/fixtures/", ""));
        return mockFixtureDetails[id] ?? { ...mockFixtures[0], home_goals_ht: null, away_goals_ht: null, stats: null, prediction: mockPrediction(1001, 0.52, 0.24, 0.24), odds: [mockOdds("Bet365", 1.95, 3.40, 4.00)] };
    }

    // Predictions
    if (basePath === "/api/v1/predictions/today" || basePath === "/api/v1/predictions") {
        return mockFixtures.filter((f) => f.status === "scheduled").map((f) =>
            mockPrediction(f.id, 0.45 + Math.random() * 0.15, 0.24, 0.26),
        );
    }

    // Value bets
    if (basePath === "/api/v1/value-bets") {
        return mockValueBets;
    }

    // Standings
    if (basePath === "/api/v1/standings") {
        return Object.values(mockStandings).flat();
    }
    if (basePath.startsWith("/api/v1/standings/")) {
        const leagueId = parseInt(basePath.replace("/api/v1/standings/", ""));
        return mockStandings[leagueId] ?? mockStandings[1];
    }

    // Sentiment
    if (basePath.startsWith("/api/v1/sentiment/")) {
        const teamId = parseInt(basePath.replace("/api/v1/sentiment/", ""));
        return mockSentiments[teamId] ?? [];
    }
    if (basePath === "/api/v1/sentiment") {
        return Object.values(mockSentiments).flat();
    }

    // Affiliate
    if (basePath === "/api/v1/affiliate/links") {
        return mockAffiliateLinks;
    }

    // Leaderboard
    if (basePath === "/api/v1/leaderboard") {
        return mockLeaderboard;
    }
    if (basePath === "/api/v1/tips/weekly-top") {
        return mockWeeklyTop;
    }
    if (basePath === "/api/v1/tips/mine") {
        return [];
    }
    if (basePath === "/api/v1/tips/ai-vs-me") {
        return { user_total_points: 0, user_total_tips: 0, user_accuracy: 0, ai_correct: 0, ai_total: 0, ai_accuracy: 0, user_wins: 0, ai_wins: 0, ties: 0 };
    }

    // Leagues
    if (basePath === "/api/v1/leagues") {
        return [PL, LL, SA, ALL];
    }

    return null;
}

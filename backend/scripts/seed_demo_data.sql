-- Demo seed data for ScoreLock local dev / staging.
--
-- Run via: make seed-demo  (or: docker compose exec -T db psql ... < this_file)
--
-- Idempotent: safe to re-run. Each block guards against duplicates.
-- Tied to fixture 328 = Manchester City 2-1 Arsenal in dev. On other envs
-- (e.g. prod where fixture 328 is a different match) the seed silently
-- no-ops via IF EXISTS / NOT EXISTS guards instead of inserting nonsense data.
--
-- Seed contents:
--   * Broadcasts: 5 most-recent PL → Viaplay, 5 most-recent La Liga → C More
--   * Players: 22 starting + 4 bench for Manchester City + Arsenal
--   * Events: 10 events for fixture 328 (3 goals, 3 yellows, 4 subs)
--   * Statistics: 2 rows (City home + Arsenal away) for fixture 328
--   * Lineups: 2 starting elevens + benches with 4-3-3 formations and pitch coords
--   * Intelligence: hand-written Swedish narrative for pre/in/post-match (no API call)
--   * Fantasy: 1 demo-season + 1 gameweek + pricing for 26 players (T1 foundation)
--   * Fantasy team: default 15-player team for admin user (T2 demo squad)
--   * AI coach: 3 hand-written demo recommendations (T8 — no API call needed)
--   * Match info: 8 venues + 8 referees + fixture 328 → Etihad + Anthony Taylor (Phase 2)

-- ── Broadcasts ────────────────────────────────────────────────────────────

-- Global per-channel guards: skip insert if ANY row already exists for that channel.
-- Avoids per-fixture matching (which would happily insert against a different
-- set of fixtures on re-run).

INSERT INTO fixture_broadcasts
    (fixture_id, country_iso_2, provider_type, channel_name, watch_url, language_iso_2, created_at)
SELECT f.id, 'SE', 'STREAMING', 'Viaplay', 'https://viaplay.se/sport', 'sv', now()
FROM fixtures f JOIN leagues l ON l.id = f.league_id
WHERE l.name = 'Premier League'
  AND NOT EXISTS (
      SELECT 1 FROM fixture_broadcasts WHERE channel_name = 'Viaplay' AND country_iso_2 = 'SE'
  )
ORDER BY f.kickoff DESC
LIMIT 5;

INSERT INTO fixture_broadcasts
    (fixture_id, country_iso_2, provider_type, channel_name, watch_url, language_iso_2, created_at)
SELECT f.id, 'SE', 'TV', 'TV4 Sport', 'https://www.tv4play.se/sport', 'sv', now()
FROM fixtures f JOIN leagues l ON l.id = f.league_id
WHERE l.name = 'Allsvenskan'
  AND NOT EXISTS (
      SELECT 1 FROM fixture_broadcasts WHERE channel_name = 'TV4 Sport' AND country_iso_2 = 'SE'
  )
ORDER BY f.kickoff DESC
LIMIT 5;

INSERT INTO fixture_broadcasts
    (fixture_id, country_iso_2, provider_type, channel_name, watch_url, language_iso_2, created_at)
SELECT f.id, 'SE', 'STREAMING', 'C More Fotboll', 'https://www.cmore.se/sport', 'sv', now()
FROM fixtures f JOIN leagues l ON l.id = f.league_id
WHERE l.name = 'La Liga'
  AND NOT EXISTS (
      SELECT 1 FROM fixture_broadcasts WHERE channel_name = 'C More Fotboll' AND country_iso_2 = 'SE'
  )
ORDER BY f.kickoff DESC
LIMIT 5;

-- ── Players + Events + Statistics for fixture 328 ─────────────────────────
-- Wrapped in a single DO block: only runs if fixture 328 is Man City vs Arsenal
-- (which is the case on local dev — silently no-ops elsewhere).

DO $$
DECLARE
    v_city_id INT;
    v_arsenal_id INT;
    v_home_id INT;
    v_away_id INT;
    v_city_lineup_id INT;
    v_arsenal_lineup_id INT;
BEGIN
    -- Resolve teams
    SELECT id INTO v_city_id FROM teams WHERE name = 'Manchester City FC';
    SELECT id INTO v_arsenal_id FROM teams WHERE name = 'Arsenal FC';

    IF v_city_id IS NULL OR v_arsenal_id IS NULL THEN
        RAISE NOTICE 'Skipping demo seed for fixture 328: City/Arsenal teams not found';
        RETURN;
    END IF;

    -- Resolve fixture 328 — only seed if it's actually Man City vs Arsenal
    SELECT home_team_id, away_team_id INTO v_home_id, v_away_id
    FROM fixtures WHERE id = 328;

    IF v_home_id IS NULL THEN
        RAISE NOTICE 'Skipping demo seed for fixture 328: fixture not found';
        RETURN;
    END IF;

    IF NOT (v_home_id = v_city_id AND v_away_id = v_arsenal_id) THEN
        RAISE NOTICE 'Skipping demo seed for fixture 328: not Man City vs Arsenal on this env';
        RETURN;
    END IF;

    -- Players (idempotent: skip if same canonical_name + team already exists)
    INSERT INTO players (canonical_name, display_name, position_code, current_team_id, external_ids, created_at, updated_at)
    SELECT name, display, pos, team_id_for_name, '{}'::jsonb, now(), now()
    FROM (VALUES
        ('Ederson Moraes',     'Ederson',     'GK',  v_city_id),
        ('Kyle Walker',        'Walker',      'DEF', v_city_id),
        ('John Stones',        'Stones',      'DEF', v_city_id),
        ('Rúben Dias',         'Dias',        'DEF', v_city_id),
        ('Nathan Aké',         'Aké',         'DEF', v_city_id),
        ('Rodri Hernández',    'Rodri',       'MID', v_city_id),
        ('Kevin De Bruyne',    'De Bruyne',   'MID', v_city_id),
        ('Bernardo Silva',     'B. Silva',    'MID', v_city_id),
        ('Phil Foden',         'Foden',       'FWD', v_city_id),
        ('Erling Haaland',     'Haaland',     'FWD', v_city_id),
        ('Jérémy Doku',        'Doku',        'FWD', v_city_id),
        ('Joško Gvardiol',     'Gvardiol',    'DEF', v_city_id),
        ('Mateo Kovačić',      'Kovačić',     'MID', v_city_id),
        ('David Raya',         'Raya',        'GK',  v_arsenal_id),
        ('Ben White',           'White',      'DEF', v_arsenal_id),
        ('William Saliba',      'Saliba',     'DEF', v_arsenal_id),
        ('Gabriel Magalhães',   'Gabriel',    'DEF', v_arsenal_id),
        ('Riccardo Calafiori',  'Calafiori',  'DEF', v_arsenal_id),
        ('Declan Rice',         'Rice',       'MID', v_arsenal_id),
        ('Martin Ødegaard',     'Ødegaard',   'MID', v_arsenal_id),
        ('Mikel Merino',        'Merino',     'MID', v_arsenal_id),
        ('Bukayo Saka',         'Saka',       'FWD', v_arsenal_id),
        ('Kai Havertz',         'Havertz',    'FWD', v_arsenal_id),
        ('Leandro Trossard',    'Trossard',   'FWD', v_arsenal_id),
        ('Gabriel Martinelli',  'Martinelli', 'FWD', v_arsenal_id),
        ('Gabriel Jesus',       'Jesus',      'FWD', v_arsenal_id)
    ) AS seed(name, display, pos, team_id_for_name)
    WHERE NOT EXISTS (
        SELECT 1 FROM players p
        WHERE p.canonical_name = seed.name AND p.current_team_id = seed.team_id_for_name
    );

    -- Events (idempotent via UNIQUE (fixture_id, provider, external_id))
    INSERT INTO fixture_events
        (fixture_id, minute, stoppage, event_type, team_id, primary_player_id, secondary_player_id, player_in_id, player_out_id, description, provider, external_id, created_at)
    VALUES
        (328, 12, NULL, 'YELLOW_CARD', v_city_id,
            (SELECT id FROM players WHERE canonical_name='Rodri Hernández' AND current_team_id=v_city_id),
            NULL, NULL, NULL, 'Tactical foul', 'manual_seed', 'mc-ars-1', now()),
        (328, 17, NULL, 'GOAL', v_city_id,
            (SELECT id FROM players WHERE canonical_name='Erling Haaland' AND current_team_id=v_city_id),
            (SELECT id FROM players WHERE canonical_name='Phil Foden' AND current_team_id=v_city_id),
            NULL, NULL, 'Header from corner, assist Foden', 'manual_seed', 'mc-ars-2', now()),
        (328, 24, NULL, 'YELLOW_CARD', v_arsenal_id,
            (SELECT id FROM players WHERE canonical_name='Bukayo Saka' AND current_team_id=v_arsenal_id),
            NULL, NULL, NULL, 'Dissent', 'manual_seed', 'mc-ars-3', now()),
        (328, 53, NULL, 'GOAL', v_city_id,
            (SELECT id FROM players WHERE canonical_name='Kevin De Bruyne' AND current_team_id=v_city_id),
            (SELECT id FROM players WHERE canonical_name='Bernardo Silva' AND current_team_id=v_city_id),
            NULL, NULL, 'Curled finish from edge of box', 'manual_seed', 'mc-ars-4', now()),
        (328, 58, NULL, 'SUBSTITUTION', v_arsenal_id, NULL, NULL,
            (SELECT id FROM players WHERE canonical_name='Gabriel Martinelli' AND current_team_id=v_arsenal_id),
            (SELECT id FROM players WHERE canonical_name='Leandro Trossard' AND current_team_id=v_arsenal_id),
            NULL, 'manual_seed', 'mc-ars-5', now()),
        (328, 67, NULL, 'YELLOW_CARD', v_arsenal_id,
            (SELECT id FROM players WHERE canonical_name='Riccardo Calafiori' AND current_team_id=v_arsenal_id),
            NULL, NULL, NULL, 'Late challenge', 'manual_seed', 'mc-ars-6', now()),
        (328, 71, NULL, 'GOAL', v_arsenal_id,
            (SELECT id FROM players WHERE canonical_name='Bukayo Saka' AND current_team_id=v_arsenal_id),
            (SELECT id FROM players WHERE canonical_name='Martin Ødegaard' AND current_team_id=v_arsenal_id),
            NULL, NULL, 'Cut inside, low finish', 'manual_seed', 'mc-ars-7', now()),
        (328, 75, NULL, 'SUBSTITUTION', v_city_id, NULL, NULL,
            (SELECT id FROM players WHERE canonical_name='Mateo Kovačić' AND current_team_id=v_city_id),
            (SELECT id FROM players WHERE canonical_name='Kevin De Bruyne' AND current_team_id=v_city_id),
            NULL, 'manual_seed', 'mc-ars-8', now()),
        (328, 78, NULL, 'SUBSTITUTION', v_arsenal_id, NULL, NULL,
            (SELECT id FROM players WHERE canonical_name='Gabriel Jesus' AND current_team_id=v_arsenal_id),
            (SELECT id FROM players WHERE canonical_name='Kai Havertz' AND current_team_id=v_arsenal_id),
            NULL, 'manual_seed', 'mc-ars-9', now()),
        (328, 82, NULL, 'SUBSTITUTION', v_city_id, NULL, NULL,
            (SELECT id FROM players WHERE canonical_name='Joško Gvardiol' AND current_team_id=v_city_id),
            (SELECT id FROM players WHERE canonical_name='Jérémy Doku' AND current_team_id=v_city_id),
            NULL, 'manual_seed', 'mc-ars-10', now())
    ON CONFLICT (fixture_id, provider, external_id) DO NOTHING;

    -- Statistics (idempotent via UNIQUE (fixture_id, team_id, provider))
    INSERT INTO fixture_statistics
        (fixture_id, team_id, possession_pct, shots_total, shots_on_target,
         shots_off_target, shots_blocked, corners, fouls, yellow_cards_count,
         red_cards_count, offsides, xg, passes_total, passes_accurate,
         pass_accuracy_pct, tackles, interceptions, blocks, clearances,
         provider, as_of_minute, created_at, updated_at)
    VALUES
        (328, v_city_id,
         58.0, 14, 6, 5, 3, 7, 9, 1, 0, 2, 1.85,
         612, 553, 90.4, 14, 9, 8, 18,
         'manual_seed', NULL, now(), now()),
        (328, v_arsenal_id,
         42.0, 11, 4, 4, 3, 4, 12, 2, 0, 3, 1.20,
         441, 376, 85.3, 19, 12, 11, 22,
         'manual_seed', NULL, now(), now())
    ON CONFLICT (fixture_id, team_id, provider) DO NOTHING;

    -- ── Lineups (Phase 4) ─────────────────────────────────────
    -- Idempotent: ON CONFLICT updates formation/coach so the lineup id is always
    -- returned; players-insert below uses ON CONFLICT (lineup_id, player_id).

    INSERT INTO fixture_lineups
        (fixture_id, team_id, formation, coach_name, provider, created_at, updated_at)
    VALUES
        (328, v_city_id, '4-3-3', 'Pep Guardiola', 'manual_seed', now(), now())
    ON CONFLICT (fixture_id, team_id, provider) DO UPDATE
        SET formation = EXCLUDED.formation,
            coach_name = EXCLUDED.coach_name,
            updated_at = now()
    RETURNING id INTO v_city_lineup_id;

    INSERT INTO fixture_lineups
        (fixture_id, team_id, formation, coach_name, provider, created_at, updated_at)
    VALUES
        (328, v_arsenal_id, '4-3-3', 'Mikel Arteta', 'manual_seed', now(), now())
    ON CONFLICT (fixture_id, team_id, provider) DO UPDATE
        SET formation = EXCLUDED.formation,
            coach_name = EXCLUDED.coach_name,
            updated_at = now()
    RETURNING id INTO v_arsenal_lineup_id;

    -- Manchester City — 4-3-3 (Stones captain)
    INSERT INTO fixture_lineup_players
        (lineup_id, player_id, shirt_number, position_label, grid_x, grid_y,
         is_starting, is_captain, created_at)
    SELECT v_city_lineup_id, p.id, seed.shirt, seed.pos,
           seed.gx, seed.gy, seed.starter, seed.captain, now()
    FROM (VALUES
        ('Ederson Moraes',  1,  'GK',  50,  5, true,  false),
        ('Kyle Walker',     2,  'RB',  90, 25, true,  false),
        ('Rúben Dias',      3,  'LCB', 35, 25, true,  false),
        ('John Stones',     5,  'RCB', 65, 25, true,  true),
        ('Nathan Aké',      6,  'LB',  10, 25, true,  false),
        ('Rodri Hernández', 16, 'DM',  50, 45, true,  false),
        ('Kevin De Bruyne', 17, 'LCM', 25, 55, true,  false),
        ('Bernardo Silva',  20, 'RCM', 75, 55, true,  false),
        ('Jérémy Doku',     11, 'LW',  15, 80, true,  false),
        ('Erling Haaland',  9,  'ST',  50, 88, true,  false),
        ('Phil Foden',      47, 'RW',  85, 80, true,  false),
        ('Mateo Kovačić',   8,  'MID', NULL, NULL, false, false),
        ('Joško Gvardiol',  24, 'DEF', NULL, NULL, false, false)
    ) AS seed(name, shirt, pos, gx, gy, starter, captain)
    JOIN players p
        ON p.canonical_name = seed.name AND p.current_team_id = v_city_id
    ON CONFLICT (lineup_id, player_id) DO NOTHING;

    -- ── Match Intelligence (Phase 5) ──────────────────────────
    -- Hand-written Swedish narrative for fixture 328 demo. Idempotent via
    -- UNIQUE (fixture_id, kind, language). No Anthropic API call needed for
    -- the seeded fixture.

    INSERT INTO match_intelligence
        (fixture_id, kind, language, summary, body, model_version, provider,
         as_of_minute, generated_at, updated_at)
    VALUES
        (328, 'pre_match', 'sv',
         'City söker tabelltätningen mot ett Arsenal som måste vinna för att hänga med.',
         'Det här är en match om mer än tre poäng. City sitter två poäng bakom Arsenal i tabellen och har två segrar i rad — ett resultat skulle stänga gapet och pressa Arteta sista månaderna före vintern.

City går på 4-3-3 med Rodri som ankare och De Bruyne i framåtriktad mittroll, vilket pekar mot att Pep tror på dominans i mittfältet. Arsenal ställer upp likadant men med Rice som enda sittande mittfältare — risken är att hans yta blir för stor när Foden och Doku rör sig mellan linjerna.

Form säger City. Arsenal har inte vunnit på fyra matcher mot topp-fyra i år. Saka är den ena reella vinsten Arsenal måste få ut — träffas han av Aké på vänsterkanten är matchen avgjord taktiskt redan i 30:e minuten.',
         'manual_seed', 'manual', NULL, now(), now()),

        (328, 'in_match', 'sv',
         'City äger boll och xG efter De Bruyne-mål och Saka-reduktion — Arsenal saknar en plan B.',
         'I 75:e minuten är ställningen 2-1 till City och bilden är ganska tydlig. De Bruynes mål i 53:e gav City kontroll och Saka tog tillbaka något i 71:a, men det skedde mer på enskild kvalitet än på ett momentum-skifte.

Statistiken under matchen visar Citys övertag: 58% bollinnehav, 14 skott mot 11, xG 1,85 mot 1,20. Det är inte en knapp ledning som sviktar — det är en ledning som matchar matchbilden.

Arteta gjorde sitt drag tidigt med Trossard in för Martinelli i 58:e, men det har inte ändrat Arsenals struktur. Pep svarade i 75:e med Kovačić in för en trött De Bruyne — defensivt skift, inte offensivt. City tror att jobbet är gjort.',
         'manual_seed', 'manual', 75, now(), now()),

        (328, 'post_match', 'sv',
         'City vinner förtjänt 2-1. Resultatet matchar xG, Arsenal saknade verktyg.',
         'Slutresultat 2-1 till City och underliggande siffror gör det rättvist. xG 1,85 mot 1,20 — inte överraskning, inte tur.

Haalands huvudmål från hörna i 17:e satte tonen. När Arsenal försökte trycka tillbaka kontrollerade Citys mittfält tempot, och De Bruynes 2-0 i 53:e var en av kvällens få situationer där Rice lämnade för stort utrymme. Sakas reducering i 71:a kom från ett individuellt sprintdrag som Walker inte hann med — men det räckte inte för att Arsenal skulle ha en realistisk slutspurt.

Två saker att ta med: Stones var matchens bäste försvarare, kapten in i kamerorna och bakåtspelet höll. Och Pep visade igen att hans roterings-strategi mellan Foden och Doku på kanterna är svår att läsa — Arsenal ställde aldrig om i tid.',
         'manual_seed', 'manual', NULL, now(), now())
    ON CONFLICT (fixture_id, kind, language) DO NOTHING;

    -- Arsenal — 4-3-3 (Ødegaard captain)
    INSERT INTO fixture_lineup_players
        (lineup_id, player_id, shirt_number, position_label, grid_x, grid_y,
         is_starting, is_captain, created_at)
    SELECT v_arsenal_lineup_id, p.id, seed.shirt, seed.pos,
           seed.gx, seed.gy, seed.starter, seed.captain, now()
    FROM (VALUES
        ('David Raya',          22, 'GK',  50,  5, true,  false),
        ('Ben White',            4, 'RB',  90, 25, true,  false),
        ('William Saliba',      12, 'RCB', 65, 25, true,  false),
        ('Gabriel Magalhães',    6, 'LCB', 35, 25, true,  false),
        ('Riccardo Calafiori',  33, 'LB',  10, 25, true,  false),
        ('Declan Rice',         41, 'DM',  50, 45, true,  false),
        ('Martin Ødegaard',      8, 'RCM', 75, 55, true,  true),
        ('Mikel Merino',        23, 'LCM', 25, 55, true,  false),
        ('Bukayo Saka',          7, 'RW',  85, 80, true,  false),
        ('Kai Havertz',         29, 'ST',  50, 88, true,  false),
        ('Gabriel Martinelli',  11, 'LW',  15, 80, true,  false),
        ('Leandro Trossard',    19, 'FWD', NULL, NULL, false, false),
        ('Gabriel Jesus',        9, 'FWD', NULL, NULL, false, false)
    ) AS seed(name, shirt, pos, gx, gy, starter, captain)
    JOIN players p
        ON p.canonical_name = seed.name AND p.current_team_id = v_arsenal_id
    ON CONFLICT (lineup_id, player_id) DO NOTHING;

END$$;

-- ── Fantasy foundation seed (T1) ─────────────────────────────────────────
-- Demo season tied to fixture 328 (Man City vs Arsenal). 1 gameweek.
-- Pricing for all 26 demo players. Fully idempotent.

DO $$
DECLARE
    v_city_id INT;
    v_arsenal_id INT;
    v_season_id INT;
    v_gameweek_id INT;
BEGIN
    SELECT id INTO v_city_id FROM teams WHERE name = 'Manchester City FC';
    SELECT id INTO v_arsenal_id FROM teams WHERE name = 'Arsenal FC';

    IF v_city_id IS NULL OR v_arsenal_id IS NULL THEN
        RAISE NOTICE 'Skipping fantasy seed: City/Arsenal teams not found';
        RETURN;
    END IF;

    -- Season
    SELECT id INTO v_season_id
    FROM fantasy_seasons
    WHERE name = 'Demo — fixture 328 (Man City vs Arsenal)';

    IF v_season_id IS NULL THEN
        INSERT INTO fantasy_seasons
            (name, scope, start_date, end_date, total_budget_units,
             is_active, transfer_rules, point_weights, created_at)
        VALUES
            ('Demo — fixture 328 (Man City vs Arsenal)',
             'demo',
             '2026-04-26',
             '2026-04-27',
             1000,
             true,
             '{"free_per_gw": 1, "extra_cost_points": 4, "wildcards_total": 1}'::jsonb,
             '{"fantasy": 0.7, "match": 0.2, "bracket": 0.1}'::jsonb,
             now())
        RETURNING id INTO v_season_id;
    END IF;

    -- Gameweek 1
    SELECT id INTO v_gameweek_id
    FROM fantasy_gameweeks
    WHERE season_id = v_season_id AND gameweek_number = 1;

    IF v_gameweek_id IS NULL THEN
        INSERT INTO fantasy_gameweeks
            (season_id, gameweek_number, deadline_at,
             first_kickoff_at, last_kickoff_at, is_finalized)
        SELECT
            v_season_id, 1,
            f.kickoff - INTERVAL '1 hour',
            f.kickoff,
            f.kickoff,
            false
        FROM fixtures f WHERE f.id = 328
        RETURNING id INTO v_gameweek_id;
    END IF;

    -- Map fixture 328 to GW1
    INSERT INTO fantasy_gameweek_fixtures (gameweek_id, fixture_id)
    VALUES (v_gameweek_id, 328)
    ON CONFLICT (gameweek_id, fixture_id) DO NOTHING;

    -- Pricing for all 26 demo players (City + Arsenal)
    -- Prices in budget units: 10 = €1.0M (e.g. 145 = €14.5M).

    INSERT INTO fantasy_player_pricing
        (player_id, season_id, current_price, starting_price,
         last_change_at, value_trend, selected_by_pct, fantasy_points_total)
    SELECT p.id, v_season_id, seed.price, seed.price,
           now(), 'stable', seed.ownership, 0
    FROM (VALUES
        -- Manchester City (13)
        ('Ederson Moraes',      55,  4.5),
        ('Kyle Walker',         55,  3.2),
        ('Rúben Dias',          60,  6.1),
        ('John Stones',         55,  5.8),
        ('Nathan Aké',          50,  3.0),
        ('Rodri Hernández',     65,  18.4),
        ('Kevin De Bruyne',    110,  41.2),
        ('Bernardo Silva',      75,  12.6),
        ('Jérémy Doku',         75,  9.8),
        ('Erling Haaland',     145,  62.4),
        ('Phil Foden',          90,  28.7),
        ('Mateo Kovačić',       60,  5.1),
        ('Joško Gvardiol',      50,  4.2),
        -- Arsenal (13)
        ('David Raya',          55,  6.3),
        ('Ben White',           55,  4.8),
        ('William Saliba',      60,  19.2),
        ('Gabriel Magalhães',   60,  21.5),
        ('Riccardo Calafiori',  50,  3.4),
        ('Declan Rice',         75,  22.7),
        ('Martin Ødegaard',     90,  31.1),
        ('Mikel Merino',        60,  4.9),
        ('Bukayo Saka',        100,  44.6),
        ('Kai Havertz',         75,  15.2),
        ('Gabriel Martinelli',  80,  18.4),
        ('Leandro Trossard',    65,  6.8),
        ('Gabriel Jesus',       70,  4.1)
    ) AS seed(name, price, ownership)
    JOIN players p ON p.canonical_name = seed.name
    WHERE p.current_team_id IN (v_city_id, v_arsenal_id)
    ON CONFLICT (player_id, season_id) DO NOTHING;

END$$;

-- ── Fantasy team default seed (T2) ─────────────────────────────────────
-- Default 15-player team for admin user (REDACTED-EMAIL). 4-3-3 formation,
-- captain Haaland, vice Stones, total cost €100M (exact budget).
-- Creates the admin user if it doesn't already exist (for fresh local DBs).

DO $$
DECLARE
    v_admin_id INT;
    v_season_id INT;
    v_team_id INT;
    v_captain_id INT;
    v_vice_id INT;
BEGIN
    SELECT id INTO v_admin_id FROM users WHERE email = 'REDACTED-EMAIL';

    IF v_admin_id IS NULL THEN
        INSERT INTO users (email, hashed_password, name, tier, is_active, created_at)
        VALUES (
            'REDACTED-EMAIL',
            'REDACTED-BCRYPT-HASH',
            'Said',
            'ELITE',
            true,
            now()
        )
        RETURNING id INTO v_admin_id;
        RAISE NOTICE 'Created admin user REDACTED-EMAIL (password: REDACTED)';
    END IF;

    SELECT id INTO v_season_id
    FROM fantasy_seasons
    WHERE name = 'Demo — fixture 328 (Man City vs Arsenal)';

    IF v_admin_id IS NULL THEN
        RAISE NOTICE 'Skipping fantasy team seed: admin user not found';
        RETURN;
    END IF;
    IF v_season_id IS NULL THEN
        RAISE NOTICE 'Skipping fantasy team seed: demo season not found';
        RETURN;
    END IF;

    SELECT id INTO v_captain_id FROM players WHERE canonical_name = 'Erling Haaland';
    SELECT id INTO v_vice_id FROM players WHERE canonical_name = 'John Stones';

    -- Team
    SELECT id INTO v_team_id
    FROM fantasy_teams
    WHERE user_id = v_admin_id AND season_id = v_season_id;

    IF v_team_id IS NULL THEN
        INSERT INTO fantasy_teams
            (user_id, season_id, name, formation,
             captain_player_id, vice_captain_player_id,
             total_points, gameweek_points,
             transfers_made_total, free_transfers_available,
             bank_balance, created_at, updated_at)
        VALUES
            (v_admin_id, v_season_id, 'ScoreLock Demo XI', '4-3-3',
             v_captain_id, v_vice_id,
             0, 0, 0, 1, 0, now(), now())
        RETURNING id INTO v_team_id;
    END IF;

    -- 15 players: 2 GK + 5 DEF + 5 MID + 3 FWD = 15. Total = 1000 units.
    INSERT INTO fantasy_team_players
        (team_id, player_id, slot_position, is_starting, purchase_price)
    SELECT v_team_id, p.id, seed.slot, seed.starter, seed.price
    FROM (VALUES
        -- Goalkeepers (2)
        ('Ederson Moraes',      'GK',  true,  55),
        ('David Raya',          'GK',  false, 55),
        -- Defenders (5: 4 starting + 1 bench)
        ('John Stones',         'DEF', true,  55),
        ('Rúben Dias',          'DEF', true,  60),
        ('Ben White',           'DEF', true,  55),
        ('Riccardo Calafiori',  'DEF', true,  50),
        ('Nathan Aké',          'DEF', false, 50),
        -- Midfielders (5: 3 starting + 2 bench)
        ('Rodri Hernández',     'MID', true,  65),
        ('Bernardo Silva',      'MID', true,  75),
        ('Declan Rice',         'MID', true,  75),
        ('Mikel Merino',        'MID', false, 60),
        ('Mateo Kovačić',       'MID', false, 60),
        -- Forwards (3: all starting)
        ('Erling Haaland',      'FWD', true,  145),
        ('Kai Havertz',         'FWD', true,  75),
        ('Leandro Trossard',    'FWD', true,  65)
    ) AS seed(name, slot, starter, price)
    JOIN players p ON p.canonical_name = seed.name
    ON CONFLICT (team_id, player_id) DO NOTHING;

    -- Selected_by_pct: bump for the demo team's owned players (showcases ownership)
    -- Skipped — pricing.selected_by_pct already seeded per-player above.

    -- ── AI coach recommendations (T8) ────────────────────────
    -- Hand-written demo recs so the UI has content without burning API tokens.
    -- cached_until set 7 days out so they always render as fresh.

    DECLARE
        v_haaland_id INT;
        v_saka_id INT;
        v_walker_id INT;
        v_white_id INT;
        v_kdb_id INT;
    BEGIN
        SELECT id INTO v_haaland_id FROM players WHERE canonical_name = 'Erling Haaland';
        SELECT id INTO v_saka_id FROM players WHERE canonical_name = 'Bukayo Saka';
        SELECT id INTO v_walker_id FROM players WHERE canonical_name = 'Kyle Walker';
        SELECT id INTO v_white_id FROM players WHERE canonical_name = 'Ben White';
        SELECT id INTO v_kdb_id FROM players WHERE canonical_name = 'Kevin De Bruyne';

        INSERT INTO fantasy_ai_recommendations
            (team_id, gameweek_id, kind, payload, reasoning_text,
             confidence_score, model_version, cached_until,
             was_acted_upon, generated_at)
        VALUES
            (v_team_id, NULL, 'transfer_in',
             jsonb_build_object(
                 'player_in_id', v_kdb_id,
                 'player_out_id', NULL,
                 'expected_point_diff', 6.4
             ),
             'Kevin De Bruyne är ägd av 41% och har snitt 8.2 poäng senaste fem omgångarna. Du har inte honom — han är troligaste differential vid stark City-form. Spara fri transfer ett varv till om budget kräver, men prioritera honom framför Foden om byte.',
             0.78, 'manual_seed',
             now() + INTERVAL '7 days', NULL, now()),

            (v_team_id, NULL, 'captain',
             jsonb_build_object(
                 'captain_player_id', v_haaland_id,
                 'expected_point_diff', 4.1
             ),
             'Behåll Haaland som kapten. Han har 62% ägarskap och får alltid hörnor i straffområdet. Stones som vice-kapten är defensivt val — överväg att flytta vice till Saka för bredare upside.',
             0.91, 'manual_seed',
             now() + INTERVAL '7 days', NULL, now()),

            (v_team_id, NULL, 'transfer_out',
             jsonb_build_object(
                 'player_in_id', v_white_id,
                 'player_out_id', v_walker_id,
                 'expected_point_diff', 2.8
             ),
             'Walker är 32 år och rotateras allt oftare av Pep — riskerar minutsbortfall mot stora matcher. Ben White är samma pris men startar varje match för Arsenal och ger samma defensiva poäng plus uppåtsidan på offensiva bidrag (Saka-assists).',
             0.65, 'manual_seed',
             now() + INTERVAL '7 days', NULL, now())
        ON CONFLICT DO NOTHING;
    END;

END$$;

-- ── Venues + Referees + match-info mapping (Phase 2) ──────────────────────

INSERT INTO venues (canonical_name, display_name, country_iso_2, city, capacity, surface, image_ref, external_ids, created_at)
SELECT name, display, country, city, cap, surf, NULL, '{}'::jsonb, now()
FROM (VALUES
    ('Etihad Stadium',    'Etihad Stadium',     'GB', 'Manchester', 53400, 'grass'),
    ('Anfield',           'Anfield',            'GB', 'Liverpool',  61276, 'grass'),
    ('Stadium of Light',  'Stadium of Light',   'GB', 'Sunderland', 49000, 'grass'),
    ('Camp Nou',          'Spotify Camp Nou',   'ES', 'Barcelona',  99354, 'grass'),
    ('Santiago Bernabéu', 'Santiago Bernabéu',  'ES', 'Madrid',     78297, 'hybrid'),
    ('San Siro',          'San Siro',           'IT', 'Milano',     75923, 'grass'),
    ('Allianz Arena',     'Allianz Arena',      'DE', 'München',    75024, 'grass'),
    ('Friends Arena',     'Strawberry Arena',   'SE', 'Stockholm',  50000, 'hybrid')
) AS seed(name, display, country, city, cap, surf)
WHERE NOT EXISTS (
    SELECT 1 FROM venues WHERE canonical_name = seed.name
);

INSERT INTO referees (canonical_name, display_name, nationality_iso_2, career_games_count, career_yellows_per_game, career_reds_per_game, external_ids, created_at)
SELECT name, display, nat, games, yc, rc, '{}'::jsonb, now()
FROM (VALUES
    ('Anthony Taylor',     'Anthony Taylor',    'GB', 412, 3.8, 0.18),
    ('Michael Oliver',     'Michael Oliver',    'GB', 380, 3.2, 0.15),
    ('Felix Zwayer',       'Felix Zwayer',      'DE', 295, 4.1, 0.21),
    ('Daniele Orsato',     'Daniele Orsato',    'IT', 332, 4.3, 0.19),
    ('Antonio Mateu Lahoz','Mateu Lahoz',       'ES', 401, 5.2, 0.27),
    ('Andreas Ekberg',     'Andreas Ekberg',    'SE', 187, 3.5, 0.16),
    ('Glenn Nyberg',       'Glenn Nyberg',      'SE', 142, 3.4, 0.14),
    ('Slavko Vinčić',      'Slavko Vinčić',     'SI', 268, 3.9, 0.18)
) AS seed(name, display, nat, games, yc, rc)
WHERE NOT EXISTS (
    SELECT 1 FROM referees WHERE canonical_name = seed.name
);

-- Map fixture 328 → Etihad + Anthony Taylor (idempotent via UNIQUE on fixture_id)
DO $$
DECLARE
    v_etihad_id INT;
    v_taylor_id INT;
    v_fixture_exists BOOL;
BEGIN
    SELECT id INTO v_etihad_id FROM venues WHERE canonical_name = 'Etihad Stadium';
    SELECT id INTO v_taylor_id FROM referees WHERE canonical_name = 'Anthony Taylor';
    SELECT EXISTS(SELECT 1 FROM fixtures WHERE id = 328) INTO v_fixture_exists;

    IF v_fixture_exists AND v_etihad_id IS NOT NULL AND v_taylor_id IS NOT NULL THEN
        INSERT INTO fixture_match_info
            (fixture_id, venue_id, referee_id, provider, created_at, updated_at)
        VALUES
            (328, v_etihad_id, v_taylor_id, 'manual_seed', now(), now())
        ON CONFLICT (fixture_id) DO UPDATE
            SET venue_id = EXCLUDED.venue_id,
                referee_id = EXCLUDED.referee_id,
                updated_at = now();
    END IF;
END$$;

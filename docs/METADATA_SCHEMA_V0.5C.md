# ScoreLock Metadata Schema v0.5c

> Design document. No application code, no Alembic migration, no schema execution in this version. Cites repo state at commit `86e6664`.
> Purpose: lock the canonical metadata schema needed to serve the competitor-grade match-detail product (Flashscore depth, LiveScore clarity, SofaScore VAR + momentum, FotMob TV/venue/weather/next-goal-odds + Swedish localization). Migrations land in v0.6a → v0.6f. Provider wiring lands in v0.5d.

---

## Executive Summary

- The current schema (13 tables, 4 migrations, head `5b8d3a2f7e91`) is provider-coupled at the column level (`api_football_id` is a first-class field on `leagues`, `teams`, `fixtures`) and has zero rows for everything that match-detail needs (no players, no lineups, no events, no statistics, no venues, no referees, no broadcasts, no weather, no odds movement, no commentary, no momentum, no MoM votes).
- Provider abstraction (`backend/app/providers/`, v0.5a) is wired structurally but unused at runtime. Schema is the next blocking layer: without canonical tables, normalizers in v0.5d have no destination to write to.
- The 12-section match-detail page from `docs/COMPETITOR_SYNTHESIS_V0.3.md` requires 20 new tables and 7 extensions to existing tables. None are speculative — every table maps to a P0/P1 feature observed in the four captured competitors.
- The schema is provider-neutral by design. External provider IDs live in a dedicated `provider_entity_mappings` table (recommended hybrid: `external_ids` JSONB cache on hot rows + the mapping table as truth). Canonical IDs are internal `bigserial` PKs that providers never see.
- Raw provider payloads land in `provider_payloads` — a **regular Postgres table** with a `(provider, operation, fetched_at DESC)` index and scheduled retention DELETE, **not** a TimescaleDB hypertable in v0.6. Promotion to hypertable is deferred to v0.7+ once write/storage volume is observed. Rationale: read patterns are point lookups (replay by id, latest-by-entity), not time-window scans — hypertable benefits don't apply yet. This also removes the TimescaleDB-extension prerequisite from v0.6a; only v0.6e (odds_snapshots, fixture_momentum) requires the extension.
- Time-series tables (`odds_snapshots`, `fixture_momentum`) become TimescaleDB hypertables — TimescaleDB is already running locally (`timescale/timescaledb:latest-pg16`) and unused. `fixture_statistics` stays relational (one row per `(fixture, team)` pair, updated in place); progression-over-time is deferred to v0.7.
- Identity drift (the `api_football_id` columns on `leagues`/`teams`/`fixtures`) is preserved as legacy convenience columns through v0.6a → v0.6f. Hard removal is a v0.7 cleanup behind a deprecation gate, not part of this schema lift. This protects every current caller in `backend/app/services/tasks.py`, `seed.py`, `historical.py`.
- Naming convention: tables that are scoped to a single fixture get the `fixture_` prefix (`fixture_events`, `fixture_lineups`, `fixture_statistics`, `fixture_commentary`, `fixture_broadcasts`, `fixture_momentum`). Reference data is unprefixed (`sports`, `countries`, `competitions`, `seasons`, `players`, `venues`, `referees`, `bookmakers`).
- The `leagues` → `competitions` rename is **deferred to v0.7+. v0.6 keeps the existing table name `leagues` and extends it in place.** The competitor taxonomy (CL, EL, UECL, World Cup) does not fit the word "league" cosmetically, but the rename is operationally destructive (FK redirection across `seasons`, `fixtures`, `standings`, `articles`, `provider_entity_mappings` plus API/frontend coordination) and is not justified during the v0.6 metadata lift. v0.6a3 instead extends `leagues` with all the columns the design calls for (`sport_id`, `country_id`, `tier`, `slug`, `external_ids JSONB`) and widens `leagues.type` enum to include `'international'`, `'qualification'`, `'knockout'`. The `competitions` table spec stays in this document as the v0.7+ rename target — design reference only. Net result: **zero destructive renames or column drops in any v0.6 batch.**
- Migration sequencing is **eight small additive batches** (v0.6a1, v0.6a2, v0.6a3, v0.6b, v0.6c, v0.6d, v0.6e, v0.6f). v0.6a is split into three sub-batches because the original combined batch crossed multiple risk axes (reference data + audit tables + extending live tables). Every batch ships with a verified down-migration, a seeded mock fixture set, and a contract test. No batch crosses two of (identity, write-path, read-path) — every batch has exactly one risk axis.
- Time-series and JSONB choices are explicit per table (not "stuff in JSONB"). `fixtures.stats JSONB` (currently an empty catchall on every row) is **deprecated, not migrated** — `fixture_statistics` replaces it as a typed table. The column stays for one version cycle in case a backfill is needed, then is dropped in v0.7.
- This design unlocks v0.6f (read APIs), then v0.7 (frontend rebuild), then v0.8 (live ingest), then v0.9 (odds movement), then v1.0 (premium demo). Without this schema, every downstream version slips because there's no normalized destination for provider data.

---

## Current Schema Inventory

13 tables verified by reading `backend/app/models/models.py` (438 LOC) and 4 Alembic revisions (`246c910cfb31`, `1f5b8ca20887`, `3a7c2e1f5d89`, `5b8d3a2f7e91`). Pydantic surface verified in `backend/app/schemas/schemas.py` (308 LOC).

| Table / Model | Current purpose | Useful existing fields | Missing fields | Action |
|---|---|---|---|---|
| `users` | Auth + Stripe linking + tier gating | `id`, `email` (unique), `hashed_password`, `tier` (FREE/PRO/ELITE), `stripe_customer_id`, `stripe_subscription_id`, `is_active`, `created_at` | `country_iso_2` (for region-aware affiliate routing), `locale` (sv/en), `last_seen_at`, soft-delete flag | **Keep** — no schema change in v0.5c. Locale + country deferred to a later i18n pass; not blocking. |
| `leagues` | League/cup catalogue, API-Football-coupled | `id`, `api_football_id` (unique, indexed), `name`, `country` (string), `logo_url`, `type` ("league" \| "cup"), `current_season`, `is_active`, `phase` | Sport FK (currently implicit football), country FK (currently free-text), tier (1/2/3), gender (m/w), age group, slug, `external_ids` for non-API-Football providers, competition_type taxonomy beyond league/cup (international, qualification, knockout) | **Extend in v0.6a3** — add `sport_id`, `country_id`, `tier`, `slug`, `external_ids JSONB` cache; widen `type` enum to include `'international'`, `'qualification'`, `'knockout'`; keep `api_football_id` as deprecated. **Do NOT rename to `competitions` in v0.6** — table name stays `leagues` through v0.6f; rename is a v0.7+ project gated on API/frontend readiness. |
| `teams` | Team catalogue, API-Football-coupled | `id`, `api_football_id` (unique, indexed), `name`, `short_name`, `logo_url`, `country` (string), `venue_name` (free-text!), `venue_capacity` | Country FK, primary venue FK (currently free-text!), tricot colors, founded year, market value, gender, canonical slug, `external_ids` | **Extend in v0.6a3** (country FK, slug, colors, `external_ids`); **promote `venue_name` → `venues` FK in v0.6b**. |
| `fixtures` | Match record, API-Football-coupled | `id`, `api_football_id` (unique, indexed), `league_id` FK, `season`, `round`, `home_team_id` FK, `away_team_id` FK, `kickoff` (naive `DateTime`!), `status` (SCHEDULED/LIVE/HALFTIME/FINISHED/POSTPONED/CANCELLED), `home_goals`, `away_goals`, `home_goals_ht`, `away_goals_ht`, `stats JSONB` (untyped catchall), `updated_at` | Venue FK, referee FK, season FK (currently denormalized int), `live_minute`, `live_stoppage`, `attendance`, `postponed_from`, `external_ids`, full status vocabulary (no `IN_PLAY` distinct from `LIVE`, no `SUSPENDED`, no `AWARDED`, no `IN_PROGRESS_EXTRA_TIME`, no `IN_PROGRESS_PENALTIES`) | **Extend in v0.6a3** (`season_id`, `live_minute`, `live_stoppage`, `attendance`, `external_ids`, expanded status enum) and **v0.6b** (`venue_id`, `referee_id`); **deprecate `stats JSONB` in v0.6c** in favor of `fixture_statistics`. **`kickoff DateTime` is NOT touched in v0.6** — it stays naive; no additive `kickoff_utc` or `kickoff_tz` columns added in v0.6a–f. TZ migration is v0.7+ work, requires app-layer dual-write coordination. |
| `standings` | League-table snapshot per season | `id`, `league_id` FK, `season`, `team_id` FK, `position`, `points`, `played`, `won`, `drawn`, `lost`, `goals_for`, `goals_against`, `goal_diff`, `form` (string "WWDLW"), `xg_for`, `xg_against`, `updated_at`, unique `(league_id, season, team_id)` | Home/away splits (`home_played`, `home_wins`, etc.), zone (`CL`/`EL`/`UECL`/`RELEGATION`/`NONE`), provider attribution | **Extend in v0.6a3** (`season_id`, zone, home/away splits as nullable columns) — additive only, current rows untouched. |
| `odds` | Per-(fixture, bookmaker, market) latest odds, overwritten on each fetch | `id`, `fixture_id` FK, `bookmaker` (string!), `market` ("1X2" \| "Over/Under 2.5" \| ...), `home_odds`, `draw_odds`, `away_odds`, `over_odds`, `under_odds`, `line` (e.g. 2.5), `fetched_at` | Bookmaker FK (currently free-text), market taxonomy (currently freeform string), region/country code, in-play flag, suspended flag, source provider | **Extend in v0.6e** (`bookmaker_id` FK, `market_code` enum, `is_in_play`, `region`); **read-path stays identical** — `odds_snapshots` is added alongside as the time-series source-of-truth. |
| `predictions` | ML model output per fixture | `id`, `fixture_id` FK, `home_win_prob`, `draw_prob`, `away_win_prob`, `confidence`, `over_25_prob`, `expected_goals`, `is_value_home/draw/away`, `value_edge`, `model_version`, `features_used JSONB`, `actual_result`, `was_correct`, `created_at` | Per-market prediction (BTTS, correct score, next goal), Kelly fraction column (currently in Pydantic only), confidence bands, latency to kickoff, retraining batch ID | **Extend in v0.6e** — add `markets_json JSONB` for non-1X2 predictions; otherwise keep as-is. Not blocking v0.5c. |
| `articles` | AI-generated content per fixture/league/round | `id`, `type` (preview/report/round_summary/value_bet_alert/news_rewrite), `slug` (unique), `title`, `summary`, `body`, `language` (default 'sv'), `league_id` FK?, `fixture_id` FK?, `round`, `tags JSONB`, `meta_data JSONB` (model_version, prompt tokens), `auto_generated`, `published_at`, `updated_at` | Author attribution (model_version is in meta_data, not a column), `team_ids` association (currently via fixture only), reading-time, view count, social-share count | **Extend in v0.6f** — add `model_version` column extracted from meta_data, `team_associations` join table if M:N becomes hot. Not blocking v0.5c. |
| `users` (covered above) | — | — | — | — |
| `user_predictions` | User tipping (H/D/A + optional exact score) | `id`, `user_id` FK, `fixture_id` FK, `predicted_outcome` ("H"/"D"/"A"), `predicted_home_goals`, `predicted_away_goals`, `points_earned`, `was_correct_outcome`, `was_exact_score`, `created_at`, `scored_at`, unique `(user_id, fixture_id)` | None for current MVP. MoM voting is a separate concept (new table `user_motm_votes`), not an extension of this. | **Keep** — no schema change. MoM is a sibling table. |
| `affiliate_links` | Bookmaker affiliate URL catalogue, seeded with 4 SE bookmakers (bet365, unibet, betsson, leovegas) per migration `3a7c2e1f5d89` | `id`, `bookmaker` (string, indexed), `bookmaker_display`, `logo_url`, `base_url`, `tracking_id`, `market`, `country` (default 'SE'), `is_active`, `priority`, `created_at` | Bookmaker FK (currently the canonical bookmaker concept lives only as a string here AND in `odds.bookmaker` — duplicated). When `bookmakers` lookup arrives in v0.6e, this table FKs to it. | **Extend in v0.6e** — add `bookmaker_id` FK; deprecate `bookmaker` string column; backfill via name-match. Migration risk: medium (named-match across 4 seed rows is trivial). |
| `affiliate_clicks` | Click telemetry (GDPR-aware ip_hash) | `id`, `link_id` FK, `fixture_id` FK?, `user_id` FK?, `page_source`, `ip_hash` (SHA), `user_agent`, `clicked_at` | None for v0.5c | **Keep** — no schema change. |
| `sentiment_scores` | Team/fixture sentiment from RSS/news | `id`, `team_id` FK, `fixture_id` FK?, `score` (-1..+1), `buzz_score` (0..1), `source` ("news"/"reddit"/"twitter"), `summary`, `raw_data JSONB`, `analyzed_at` | None blocking v0.5c. RSS pipeline has 5/9 dead feeds — backlog item, not a schema fix. | **Keep** — no schema change. Sentiment is decoupled from match-detail metadata. |
| `prediction_views` | Freemium gating (per-user views/week) | `id`, `user_id` FK, `fixture_id` FK, `viewed_at`, index `(user_id, viewed_at)` | None for v0.5c | **Keep** — no schema change. |

**Counts**:
- Existing tables: **13**
- Tables to **keep** as-is: 6 (users, sentiment_scores, prediction_views, user_predictions, affiliate_clicks, articles)
- Tables to **extend** in v0.6a1–f: 7 (leagues, teams, fixtures, standings, odds, predictions, articles, affiliate_links — articles + affiliate_links extensions are minor)
- Tables to **deprecate** (column-level, not table-level): 1 (`fixtures.stats JSONB`; column stays through v0.6f, drop deferred to v0.7)
- Tables to **rename in v0.6**: **0**. The `leagues → competitions` rename is deferred to v0.7+; v0.6 keeps the existing table name and extends in place. **Zero destructive changes in v0.6.**

---

## Competitor-Derived Schema Requirements

Maps the 32-feature taxonomy from `docs/COMPETITOR_SYNTHESIS_V0.3.md` to schema actions. P0 = blocks v1.0; P1 = differentiator; P2 = nice-to-have.

| Feature | Required entities/tables | P | Source competitor(s) | Current support | Schema action |
|---|---|---|---|---|---|
| Players (identity, photo, position) | `players`, `provider_entity_mappings` | P0 | All 4 (Flashscore Player stats tab, LiveScore Line-ups, SofaScore clickable names, FotMob MoM poll) | **No** | New `players` table in v0.6b |
| Lineups (projected → confirmed) | `fixture_lineups`, `fixture_lineup_players`, `players` | P0 | All 4 | **No** | New `fixture_lineups` + `fixture_lineup_players` in v0.6c |
| Formations (4-3-3, 3-5-2 etc.) | Column on `fixture_lineups.formation_code` | P0 | All 4 | **No** | Column on new `fixture_lineups` in v0.6c |
| Match events (timeline) | `fixture_events`, `players` | P0 | All 4 | **No** | New `fixture_events` in v0.6c |
| Substitutions (in/out players + minute) | `fixture_events` rows with `event_type='SUBSTITUTION'`, `player_in_id`, `player_out_id` | P0 | All 4 | **No** | Covered by `fixture_events` schema in v0.6c |
| VAR decisions (goal cancelled, penalty, red card overturned) | `fixture_events` rows with `event_type` in `('VAR_GOAL_AWARDED','VAR_GOAL_CANCELLED','VAR_PENALTY_AWARDED','VAR_PENALTY_OVERTURNED','VAR_RED_CARD')` | P1 | SofaScore (visible), FotMob (partial) | **No** | Covered by `fixture_events.event_type` enum in v0.6c. Provider-conditional populate (only providers that emit VAR) |
| Yellow / red / second yellow cards | `fixture_events` with `event_type` in `('YELLOW_CARD','RED_CARD','SECOND_YELLOW')` | P0 | All 4 | **No** | Covered by `fixture_events` in v0.6c |
| Goals + assists + own-goals + penalty | `fixture_events` with `event_type` in `('GOAL','OWN_GOAL','PENALTY_GOAL','MISSED_PENALTY')`, `primary_player_id` (scorer), `assist_player_id` | P0 | All 4 | **No** | Covered by `fixture_events` in v0.6c |
| Match statistics (possession, shots, corners, fouls) | `fixture_statistics` | P0 | SofaScore + FotMob (full); Flashscore + LiveScore (partial via README) | **No** (only `fixtures.stats JSONB` empty catchall) | New `fixture_statistics` in v0.6c, replaces `fixtures.stats JSONB` |
| xG (expected goals) | Column on `fixture_statistics.xg`, also on `predictions.expected_goals` (already exists) | P0 | SofaScore + FotMob | Partial — `predictions.expected_goals` exists, `standings.xg_for/xg_against` exists; per-team in-match xG missing | Covered by `fixture_statistics.xg` in v0.6c |
| Player ratings (per-player, per-match) | Column on `fixture_lineup_players.provider_rating_value` + `provider_rating_source` | P1 | SofaScore (proprietary moat), FotMob (proprietary) | **No** | Covered by `fixture_lineup_players` in v0.6c. **Hard rule**: do not invent our own rating; consume provider only |
| Momentum graph (attack pressure over time) | `fixture_momentum` (TimescaleDB hypertable) | P1 | SofaScore + FotMob | **No** | New `fixture_momentum` in v0.6e |
| Live commentary (text per minute) | `fixture_commentary` | P0 | Flashscore (full), FotMob (snippet); LiveScore + SofaScore partial | **No** | New `fixture_commentary` in v0.6c |
| Referee (name, nationality, career stats) | `referees` + FK from `fixtures` | P0 | LiveScore, SofaScore, FotMob | **No** | New `referees` in v0.6b |
| Venue (name, city, country, capacity, surface) | `venues` + FK from `fixtures` and `teams` | P0 | All 4 | Partial — `teams.venue_name` and `teams.venue_capacity` are free-text columns, not normalized | New `venues` in v0.6b; `teams.venue_id` and `fixtures.venue_id` FKs added; old free-text columns deprecated |
| Weather at kickoff | `weather_snapshots` linked to `venues` + `fixtures` | P1 | FotMob only | **No** | New `weather_snapshots` in v0.6d |
| TV channel + streaming provider per region | `fixture_broadcasts` | P0 (FotMob's strongest moat; key SE differentiator) | FotMob only | **No** | New `fixture_broadcasts` in v0.6d |
| Pre-match odds snapshots (movement over time) | `odds_snapshots` (TimescaleDB hypertable) + `bookmakers` lookup | P0 | All 4 (movement signal in value-bet card per FotMob) | Partial — `odds` table exists with `fetched_at` but rows are overwritten, no movement preserved | New `odds_snapshots` + `bookmakers` in v0.6e; existing `odds` becomes a latest-snapshot cache |
| In-play / next-goal odds | `odds_snapshots` rows with `is_in_play=true` and `market_code='NEXT_GOAL'` | P1 | FotMob (next-goal widget), SofaScore (line markets inline) | **No** | Covered by `odds_snapshots` taxonomy in v0.6e. Requires Odds API in-play tier (open question) |
| Bookmaker (logo, license, region) | `bookmakers` (with FK from `odds_snapshots` and `affiliate_links`) | P0 | All 4 | Partial — bookmaker is a string in `odds.bookmaker` and a string in `affiliate_links.bookmaker`; no canonical lookup | New `bookmakers` in v0.6e |
| H2H (last N meetings) | Derivable from existing `fixtures` | P0 | All 4 | Partial — endpoint `/h2h/{t1}/{t2}` exists at `backend/app/api/routes.py:388–426` | No new table; v0.6f endpoint extension only |
| Standings impact projection | Derivable from existing `standings` + `fixtures` | P1 | None of the four directly | Partial — `standings` exists, projection logic doesn't | No new table; v0.6f endpoint extension only |
| News / social context (related articles per fixture) | Existing `articles` table with `fixture_id` FK | P1 | Flashscore (News tab), FotMob (Rapport tab) | Partial — table exists, 0 rows in prod | No new table; v0.6f endpoint extension only |
| Man-of-the-Match poll (community vote) | `user_motm_votes` | P1 | FotMob only | **No** | New `user_motm_votes` in v0.6c |

**Coverage delta**:
- 32 features in the taxonomy, 11 already covered by existing schema, 21 require new tables or extensions.
- 0 features blocked by competitor IP / proprietary moats — every P0/P1 has a provider-supplied data path.

---

## Proposed Canonical Tables

20 new tables. Each spec is the v0.6 design target. Column types are PostgreSQL primitives (no `Any`, no untyped JSONB unless explicitly documented). Every table participates in `provider_entity_mappings` unless marked **No external mapping**.

### 1. `sports`

- **Purpose**: Top-level sport lookup. Football-only at launch; multi-sport extensibility per provider abstraction.
- **Columns**: `id BIGSERIAL`, `code VARCHAR(20) NOT NULL UNIQUE` (e.g. `'football'`), `display_name VARCHAR(100) NOT NULL`, `icon_ref VARCHAR(255)`, `is_active BOOLEAN DEFAULT TRUE`, `created_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: none.
- **Unique**: `(code)`.
- **Indexes**: implicit on `(code)` via unique.
- **Provider mapping**: every provider maps to a canonical `sport_code`. No `provider_entity_mappings` rows (sport identity is universal).
- **Nullable vs required**: only `icon_ref` nullable.
- **Migration risk**: very low — additive, single seeded row.
- **Validation**: post-migration row count == 1 (`'football'`); FK resolution test from `competitions.sport_id`.

### 2. `countries`

- **Purpose**: ISO 3166-1 country lookup. Used by `competitions`, `teams`, `players`, `referees`, `venues`, `fixture_broadcasts` (per-country broadcast rights).
- **Columns**: `id BIGSERIAL`, `iso_2 VARCHAR(2) NOT NULL UNIQUE`, `iso_3 VARCHAR(3) NOT NULL UNIQUE`, `display_name VARCHAR(100) NOT NULL`, `display_name_sv VARCHAR(100)`, `flag_ref VARCHAR(255)`, `is_active BOOLEAN DEFAULT TRUE`.
- **PK**: `id`.
- **FKs**: none.
- **Unique**: `(iso_2)`, `(iso_3)`.
- **Indexes**: `(iso_2)` via unique.
- **Provider mapping**: providers report ISO codes (or names that map to ISO). No mapping table needed (ISO codes are stable).
- **Nullable vs required**: `display_name_sv`, `flag_ref` nullable.
- **Migration risk**: low — additive, ~250 seeded rows from ISO 3166-1 reference list.
- **Validation**: row count ≥ 250 post-seed; check that `iso_2='SE'` resolves to `Sverige` in Swedish locale.

### 3. `competitions` (deferred — design target for v0.7+; **not created in v0.6**)

- **Status**: **Not created in v0.6.** The role this table would play is filled by extending the existing `leagues` table in v0.6a3 with the same columns (`sport_id`, `country_id`, `code`, `display_name`, `competition_type`, `tier`, `external_ids`, etc.) and widening `leagues.type` enum to include `'international'`, `'qualification'`, `'knockout'`. The full table spec below is preserved as the v0.7+ rename target — design reference only.
- **Purpose** (when created in v0.7+): Replace `leagues` as the canonical lookup for leagues + cups + international tournaments. The word "league" doesn't fit CL/EL/UECL/World Cup — "competition" is the correct umbrella per provider conventions (SportMonks, Stats Perform, FotMob all use it).
- **Columns**: `id BIGSERIAL`, `sport_id BIGINT NOT NULL FK→sports.id`, `country_id BIGINT FK→countries.id` (NULL for international like CL/EL/UECL/World Cup), `code VARCHAR(50) NOT NULL UNIQUE` (ScoreLock-internal slug, e.g. `'premier-league'`, `'champions-league'`), `display_name VARCHAR(150) NOT NULL`, `display_name_sv VARCHAR(150)`, `competition_type VARCHAR(20) NOT NULL CHECK (competition_type IN ('league','cup','international','qualification','knockout'))`, `tier INT` (1 for top flight, 2 for second tier, NULL for cups), `gender VARCHAR(2) DEFAULT 'm' CHECK (gender IN ('m','w'))`, `age_group VARCHAR(10) DEFAULT 'senior'`, `logo_ref VARCHAR(255)`, `phase INT DEFAULT 1` (launch phase: 1/2/3), `is_active BOOLEAN DEFAULT TRUE`, `external_ids JSONB DEFAULT '{}'` (cache of provider IDs for hot-path), `created_at TIMESTAMPTZ DEFAULT NOW()`, `updated_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: `sport_id → sports.id`, `country_id → countries.id`.
- **Unique**: `(code)`.
- **Indexes**: `(sport_id, country_id)`, `(competition_type, tier)`, GIN on `external_ids`.
- **Provider mapping**: yes — `provider_entity_mappings` rows for every provider that returns this competition.
- **Nullable vs required**: `country_id`, `display_name_sv`, `tier`, `logo_ref`, `external_ids` (default `{}`) nullable.
- **Migration risk** (v0.7+ rename, not v0.6): medium-high — destructive table rename plus FK redirection across `seasons`, `fixtures`, `standings`, `articles`, `provider_entity_mappings` plus API + frontend coordination. Out of v0.6 scope.
- **Validation** (v0.7+ post-rename): every FK previously pointing to `leagues.id` now points to `competitions.id`; row count preserved exactly; API + frontend smoke tests green.

### 4. `seasons`

- **Purpose**: Season identity per competition. Replaces the denormalized `season INT` columns scattered across `fixtures`, `standings`, `predictions`. Some providers label seasons by start year (2025), others by end year (2026); canonical is `year_start`.
- **Columns**: `id BIGSERIAL`, `competition_id BIGINT NOT NULL FK→competitions.id`, `year_start INT NOT NULL`, `label VARCHAR(20) NOT NULL` (e.g. `'2025/26'`), `start_date DATE`, `end_date DATE`, `is_current BOOLEAN DEFAULT FALSE`, `external_ids JSONB DEFAULT '{}'`, `created_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: `competition_id → competitions.id`.
- **Unique**: `(competition_id, year_start)`.
- **Indexes**: `(competition_id, is_current)` (for "current season" lookup), `(year_start)`.
- **Provider mapping**: yes.
- **Nullable vs required**: `start_date`, `end_date`, `external_ids` nullable.
- **Migration risk**: low — additive. Backfill from existing `(league_id, season)` pairs in `fixtures` and `standings` is mechanical.
- **Validation**: every distinct `(league_id, season)` from `fixtures` resolves to exactly one `seasons` row post-backfill.

### 5. `provider_payloads`

- **Purpose**: Immutable raw provider response store. Source-of-truth for replay-normalization, conflict debugging, legal evidence. **Regular Postgres table in v0.6**, per `docs/PROVIDER_ABSTRACTION_V0.4.md` § Raw Payload and External ID Strategy. Promotion to TimescaleDB hypertable is **deferred to v0.7+** once write/storage volume justifies it.
- **Columns**: `id BIGSERIAL`, `provider VARCHAR(50) NOT NULL`, `operation VARCHAR(50) NOT NULL` (matches `Operation` enum in `backend/app/providers/base.py`), `scope VARCHAR(255)` (e.g. league code, fixture external_id), `external_id VARCHAR(255)`, `request_params JSONB`, `response_status INT`, `response_headers JSONB` (whitelist-filtered: `content-type`, `date`, `x-ratelimit-*`, `x-requests-*`), `payload JSONB NOT NULL`, `payload_size_bytes INT`, `fetched_at TIMESTAMPTZ NOT NULL`, `normalized_at TIMESTAMPTZ`, `normalization_version INT`, `is_pii_scrubbed BOOLEAN DEFAULT FALSE`.
- **PK**: `id` (single-column; no composite needed without hypertable).
- **FKs**: none (loose-coupled to canonical tables; relationship is via `external_id` lookup through `provider_entity_mappings`).
- **Unique**: none (the same provider may legitimately re-fetch).
- **Indexes**: `(provider, operation, fetched_at DESC)` for "latest payload by provider+operation"; `(external_id, fetched_at DESC)` for entity history; `(fetched_at)` standalone for retention DELETE scans.
- **Hypertable**: **No.** Defer until write volume + read patterns justify. Read patterns today are point lookups (replay by `id`, latest by entity) — hypertable benefits (chunk pruning on time-window scans) don't apply. If volume crosses ~100M rows OR storage exceeds 50 GB, reassess in v0.7+ via in-place hypertable conversion (`SELECT create_hypertable('provider_payloads', 'fetched_at', migrate_data => true)`).
- **Retention**: implemented as a **scheduled `DELETE` Celery task** (`prune_provider_payloads`, runs daily at 04:00 UTC), not via TimescaleDB drop_chunks. Same retention windows: live-match payloads (`operation IN ('live_fixtures','events','statistics','in_play_odds')`) → 30 days; pre/post payloads (`operation IN ('lineups','fixtures','standings')`) → 180 days; schema-rare (`teams`, `players`, leagues) → indefinite. Index on `(fetched_at)` keeps the DELETE scan efficient.
- **Provider mapping**: source table for it, not consumer.
- **Nullable vs required**: `scope`, `external_id`, `request_params`, `response_headers`, `normalized_at`, `normalization_version` nullable.
- **Migration risk**: low — plain `CREATE TABLE` + 3 indexes. No TimescaleDB extension required in v0.6a2.
- **Validation**: insert one test payload; `SELECT count(*) FROM provider_payloads WHERE provider='test'` returns 1; the DELETE retention task dry-run reports correct row counts on a seeded fixture set.

### 6. `provider_entity_mappings`

- **Purpose**: Provider-external-ID ↔ canonical-internal-ID mapping. The truth source. Every entity that providers identify (`competitions`, `seasons`, `teams`, `players`, `fixtures`, `venues`, `referees`, `bookmakers`) gets rows here per provider that returns it.
- **Columns**: `id BIGSERIAL`, `entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('competition','season','team','player','fixture','venue','referee','bookmaker'))`, `canonical_id BIGINT NOT NULL` (FK is logical, not declared — varies by entity_type), `provider VARCHAR(50) NOT NULL`, `external_id VARCHAR(255) NOT NULL`, `confidence DECIMAL(3,2) DEFAULT 1.00` (for fuzzy-matched mappings; 1.00 = certain), `first_seen_at TIMESTAMPTZ DEFAULT NOW()`, `last_seen_at TIMESTAMPTZ DEFAULT NOW()`, `created_by VARCHAR(50) DEFAULT 'auto'` (`'auto'` \| `'admin'` \| `'manual_resolve'`).
- **PK**: `id`.
- **FKs**: none declared (logical FK varies — `canonical_id` resolves against `entity_type`-specific table; enforced at app layer in normalizer).
- **Unique**: `(entity_type, provider, external_id)` — one canonical_id per (provider, external_id) pair.
- **Indexes**: `(entity_type, canonical_id)` for reverse lookup ("what providers know about team X?"), `(entity_type, provider, external_id)` via unique, `(last_seen_at)` for stale-mapping detection.
- **Provider mapping**: this IS the mapping table. Never has rows for itself.
- **Nullable vs required**: `confidence`, `first_seen_at`, `last_seen_at`, `created_by` defaulted; `entity_type`, `canonical_id`, `provider`, `external_id` required.
- **Migration risk**: low — additive. Initial backfill from existing `api_football_id` columns is straightforward (write rows where `entity_type='competition'`, `provider='api_football'`, `external_id=leagues.api_football_id::text`, `canonical_id=leagues.id`). Same for teams + fixtures.
- **Validation**: backfill produces N rows where N = `(SELECT count(*) FROM leagues) + (SELECT count(*) FROM teams) + (SELECT count(*) FROM fixtures)`; a sample fixture round-trips ID lookup correctly.

### 7. `players`

- **Purpose**: Player identity catalogue. Required for lineups, MoM polls, player-level events (scorer, booked, subbed). Currently absent.
- **Columns**: `id BIGSERIAL`, `canonical_name VARCHAR(150) NOT NULL`, `display_name VARCHAR(150) NOT NULL`, `nationality_country_id BIGINT FK→countries.id`, `position_code VARCHAR(10) CHECK (position_code IN ('GK','DEF','MID','FWD','UNK'))`, `date_of_birth DATE`, `height_cm INT`, `weight_kg INT`, `preferred_foot VARCHAR(10) CHECK (preferred_foot IN ('left','right','both','unknown'))`, `current_team_id BIGINT FK→teams.id`, `market_value_eur BIGINT`, `photo_ref VARCHAR(255)`, `is_active BOOLEAN DEFAULT TRUE`, `external_ids JSONB DEFAULT '{}'`, `created_at TIMESTAMPTZ DEFAULT NOW()`, `updated_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: `nationality_country_id → countries.id`, `current_team_id → teams.id`.
- **Unique**: none (player names collide; identity is canonical_id + provider mapping).
- **Indexes**: `(canonical_name)` for name search, `(current_team_id)` for squad lookup, GIN on `external_ids`.
- **Provider mapping**: yes — heavy use (player IDs vary across all providers).
- **Nullable vs required**: only `canonical_name`, `display_name` required; everything else nullable.
- **Migration risk**: low — additive, no rows on creation. First-row population happens in v0.5d when SportMonks/API-Football lineup data starts flowing.
- **Validation**: insert test row; verify FK from `fixture_lineup_players.player_id`.

### 8. `venues`

- **Purpose**: Stadium/venue identity. Replaces `teams.venue_name` free-text. Needed for FotMob-style venue card (capacity, surface, weather location).
- **Columns**: `id BIGSERIAL`, `canonical_name VARCHAR(200) NOT NULL`, `display_name VARCHAR(200) NOT NULL`, `country_id BIGINT NOT NULL FK→countries.id`, `city VARCHAR(100) NOT NULL`, `capacity INT`, `surface VARCHAR(20) CHECK (surface IN ('grass','artificial','hybrid','unknown'))`, `latitude DECIMAL(9,6)`, `longitude DECIMAL(9,6)` (composite needed for weather provider geo-lookup), `address VARCHAR(500)`, `opened_year INT`, `image_ref VARCHAR(255)`, `external_ids JSONB DEFAULT '{}'`, `created_at TIMESTAMPTZ DEFAULT NOW()`, `updated_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: `country_id → countries.id`.
- **Unique**: none (venue names collide globally — Stadium of Light exists in Sunderland AND Lisbon; geographic disambiguation by lat/lon is the answer).
- **Indexes**: `(country_id, city)`, GIN on `external_ids`.
- **Provider mapping**: yes.
- **Nullable vs required**: `canonical_name`, `display_name`, `country_id`, `city` required; everything else nullable.
- **Migration risk**: low — additive. Backfill from `teams.venue_name` in v0.6b is fuzzy and best-effort; manual override allowed.
- **Validation**: post-backfill, every team with `teams.venue_name IS NOT NULL` has a `venues` row OR an explicit "no match" log entry.

### 9. `referees`

- **Purpose**: Referee identity + career stats. Match-info strip in LiveScore/SofaScore/FotMob.
- **Columns**: `id BIGSERIAL`, `canonical_name VARCHAR(150) NOT NULL`, `display_name VARCHAR(150) NOT NULL`, `nationality_country_id BIGINT FK→countries.id`, `career_games_count INT`, `career_yellows_per_game DECIMAL(4,2)`, `career_reds_per_game DECIMAL(4,2)`, `career_penalties_per_game DECIMAL(4,2)`, `external_ids JSONB DEFAULT '{}'`, `created_at TIMESTAMPTZ DEFAULT NOW()`, `updated_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: `nationality_country_id → countries.id`.
- **Unique**: none (rare collisions but possible).
- **Indexes**: `(canonical_name)`, GIN on `external_ids`.
- **Provider mapping**: yes.
- **Nullable vs required**: only `canonical_name`, `display_name` required.
- **Migration risk**: very low — additive, no rows on creation.
- **Validation**: insert test row; FK from `fixtures.referee_id`.

### 10. `fixture_events`

- **Purpose**: Event timeline per fixture. Goals, OG, cards, subs, VAR — minute-ordered, append-only.
- **Columns**: `id BIGSERIAL`, `fixture_id BIGINT NOT NULL FK→fixtures.id ON DELETE CASCADE`, `minute INT NOT NULL`, `stoppage INT` (additional stoppage minutes), `event_type VARCHAR(30) NOT NULL CHECK (event_type IN ('GOAL','OWN_GOAL','PENALTY_GOAL','MISSED_PENALTY','YELLOW_CARD','RED_CARD','SECOND_YELLOW','SUBSTITUTION','VAR_GOAL_AWARDED','VAR_GOAL_CANCELLED','VAR_PENALTY_AWARDED','VAR_PENALTY_OVERTURNED','VAR_RED_CARD','PERIOD_START','PERIOD_END','MATCH_START','MATCH_END'))`, `team_id BIGINT FK→teams.id` (NULL for system events like PERIOD_START), `primary_player_id BIGINT FK→players.id` (scorer / booked / VAR subject; NULL for system events), `secondary_player_id BIGINT FK→players.id` (assist provider for goals; can be NULL), `player_in_id BIGINT FK→players.id` (sub on; required iff event_type='SUBSTITUTION'), `player_out_id BIGINT FK→players.id` (sub off; required iff event_type='SUBSTITUTION'), `description TEXT`, `video_clip_ref VARCHAR(255)`, `provider VARCHAR(50) NOT NULL`, `external_id VARCHAR(255)`, `created_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: cascading from `fixtures` (events deleted with fixture; safe because events are reproducible from `provider_payloads`).
- **Unique**: `(fixture_id, provider, external_id)` (idempotent ingest from same provider).
- **Indexes**: `(fixture_id, minute, stoppage)` for chronological retrieval, `(team_id)`, `(primary_player_id)`.
- **Provider mapping**: indirect — events themselves are not entities; their `external_id` namespace is per-provider per-fixture.
- **Nullable vs required**: `fixture_id`, `minute`, `event_type`, `provider` required; everything else nullable per event_type semantics.
- **Migration risk**: low — additive table, no rows on creation. Population starts in v0.5d via provider adapters.
- **Validation**: insert a test set covering all event_types; query `SELECT * FROM fixture_events WHERE fixture_id=? ORDER BY minute, stoppage` returns chronologically; CHECK constraint rejects `event_type='WIBBLE'`.

### 11. `fixture_lineups`

- **Purpose**: Lineup record per (fixture, team). Two states: PROJECTED (pre-kickoff) → CONFIRMED (at kickoff). One row per team per fixture (so 2 rows per fixture in normal case).
- **Columns**: `id BIGSERIAL`, `fixture_id BIGINT NOT NULL FK→fixtures.id ON DELETE CASCADE`, `team_id BIGINT NOT NULL FK→teams.id`, `formation_code VARCHAR(15)` (e.g. `'4-3-3'`, `'3-5-2'`), `state VARCHAR(20) NOT NULL CHECK (state IN ('PROJECTED','CONFIRMED'))`, `confirmed_at TIMESTAMPTZ`, `manager_name VARCHAR(150)`, `provider VARCHAR(50) NOT NULL`, `external_id VARCHAR(255)`, `created_at TIMESTAMPTZ DEFAULT NOW()`, `updated_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: `fixture_id → fixtures.id`, `team_id → teams.id`.
- **Unique**: `(fixture_id, team_id, state)` — one PROJECTED and one CONFIRMED per team per fixture (transition is INSERT, not UPDATE; preserves history).
- **Indexes**: `(fixture_id, team_id)`.
- **Provider mapping**: indirect (per-provider `external_id` for the lineup record).
- **Nullable vs required**: `fixture_id`, `team_id`, `state`, `provider` required.
- **Migration risk**: low — additive.
- **Validation**: a test fixture with PROJECTED → CONFIRMED transition produces 2 rows; query returns CONFIRMED via `ORDER BY state DESC LIMIT 1` (alphabetically PROJECTED < CONFIRMED — verify or use explicit `state='CONFIRMED'` filter).

### 12. `fixture_lineup_players`

- **Purpose**: Roster per lineup. Each starting XI player + bench player.
- **Columns**: `id BIGSERIAL`, `lineup_id BIGINT NOT NULL FK→fixture_lineups.id ON DELETE CASCADE`, `player_id BIGINT NOT NULL FK→players.id`, `position_code VARCHAR(10) NOT NULL CHECK (position_code IN ('GK','DEF','MID','FWD','UNK'))`, `shirt_number INT`, `is_starter BOOLEAN NOT NULL`, `is_captain BOOLEAN DEFAULT FALSE`, `grid_x SMALLINT CHECK (grid_x BETWEEN 0 AND 5)`, `grid_y SMALLINT CHECK (grid_y BETWEEN 0 AND 4)` (formation grid; null for bench), `provider_rating_value DECIMAL(3,1)` (e.g. 7.4), `provider_rating_source VARCHAR(50)` (e.g. `'opta'`, `'sportmonks'`, `'api_football'`), `minutes_played INT`, `created_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: `lineup_id → fixture_lineups.id`, `player_id → players.id`.
- **Unique**: `(lineup_id, player_id)` — one player can appear once per lineup.
- **Indexes**: `(lineup_id)`, `(player_id)`.
- **Provider mapping**: none directly (mapped through `lineup_id` and `player_id`).
- **Nullable vs required**: `lineup_id`, `player_id`, `position_code`, `is_starter` required.
- **Migration risk**: low.
- **Validation**: a 22-player roster (11 + 11) inserts cleanly; CHECK constraints reject `grid_x=6`.

### 13. `fixture_statistics`

- **Purpose**: Aggregated match statistics per (fixture, team). One row per team per fixture (so 2 rows per fixture). Updated in place during live; final state at match end. Replaces `fixtures.stats JSONB` (which is empty across all current rows).
- **Columns**: `id BIGSERIAL`, `fixture_id BIGINT NOT NULL FK→fixtures.id ON DELETE CASCADE`, `team_id BIGINT NOT NULL FK→teams.id`, `possession_pct DECIMAL(4,1)`, `shots_total INT`, `shots_on_target INT`, `shots_off_target INT`, `shots_blocked INT`, `shots_inside_box INT`, `shots_outside_box INT`, `corners INT`, `fouls INT`, `yellow_cards_count INT`, `red_cards_count INT`, `offsides INT`, `xg DECIMAL(4,2)`, `passes_total INT`, `passes_accurate INT`, `pass_accuracy_pct DECIMAL(4,1)`, `ball_in_play_seconds INT`, `tackles INT`, `interceptions INT`, `blocks INT`, `clearances INT`, `big_chances_created INT`, `big_chances_missed INT`, `provider VARCHAR(50) NOT NULL`, `as_of_minute INT` (NULL = final), `created_at TIMESTAMPTZ DEFAULT NOW()`, `updated_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: `fixture_id → fixtures.id`, `team_id → teams.id`.
- **Unique**: `(fixture_id, team_id, provider)` (one final-state row per provider per team per fixture; multi-provider rows allowed for diff/conflict).
- **Indexes**: `(fixture_id)`, `(team_id, fixture_id)`.
- **Provider mapping**: indirect.
- **Nullable vs required**: `fixture_id`, `team_id`, `provider` required; all stat columns nullable (provider variance — xG missing in some, possession sum should be ≈100±1).
- **Migration risk**: low — additive, doesn't touch `fixtures.stats JSONB` (which stays as a deprecated column for one version cycle).
- **Validation**: `(possession_pct[home] + possession_pct[away]) BETWEEN 99 AND 101` for any fixture; conflict log entry if outside band.

### 14. `fixture_commentary`

- **Purpose**: Live text commentary lines. Minute-ordered, append-only. Flashscore-style.
- **Columns**: `id BIGSERIAL`, `fixture_id BIGINT NOT NULL FK→fixtures.id ON DELETE CASCADE`, `minute INT NOT NULL`, `stoppage INT`, `comment_type VARCHAR(20) DEFAULT 'general' CHECK (comment_type IN ('general','important','goal','card','sub','var','kickoff','halftime','fulltime'))`, `text_en TEXT`, `text_sv TEXT`, `provider VARCHAR(50) NOT NULL`, `external_id VARCHAR(255)`, `is_translated BOOLEAN DEFAULT FALSE`, `created_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: `fixture_id → fixtures.id`.
- **Unique**: `(fixture_id, provider, external_id)` (idempotent ingest).
- **Indexes**: `(fixture_id, minute, stoppage)`.
- **Provider mapping**: indirect.
- **Nullable vs required**: `fixture_id`, `minute`, `provider` required; either `text_en` OR `text_sv` populated.
- **Migration risk**: low.
- **Validation**: insert a 10-line commentary set; chronological retrieval works; `is_translated=true` rows have both `text_en` and `text_sv`.

### 15. `fixture_broadcasts`

- **Purpose**: TV/streaming/radio broadcast info per (fixture, country). FotMob's strongest moat. Highest-value SE differentiator. One row per (fixture, country, channel) — same fixture has different broadcasts in SE vs UK vs DE.
- **Columns**: `id BIGSERIAL`, `fixture_id BIGINT NOT NULL FK→fixtures.id ON DELETE CASCADE`, `country_id BIGINT NOT NULL FK→countries.id`, `provider_type VARCHAR(20) NOT NULL CHECK (provider_type IN ('TV','STREAMING','RADIO'))`, `channel_name VARCHAR(150) NOT NULL` (e.g. `'Viaplay'`, `'TV4'`, `'C More Sport'`), `watch_url VARCHAR(1000)`, `affiliate_link_id BIGINT FK→affiliate_links.id` (NULL when no affiliate deal), `requires_subscription BOOLEAN DEFAULT TRUE`, `language_iso_2 VARCHAR(2)`, `logo_ref VARCHAR(255)`, `valid_from TIMESTAMPTZ`, `valid_until TIMESTAMPTZ`, `data_source VARCHAR(50) NOT NULL` (provider name OR `'manual_curation'`), `created_at TIMESTAMPTZ DEFAULT NOW()`, `updated_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: `fixture_id → fixtures.id`, `country_id → countries.id`, `affiliate_link_id → affiliate_links.id`.
- **Unique**: `(fixture_id, country_id, channel_name, provider_type)`.
- **Indexes**: `(fixture_id, country_id)` (per-fixture per-region lookup), `(country_id, valid_from)` (upcoming broadcasts in a region).
- **Provider mapping**: not via `provider_entity_mappings` (broadcast records are per-fixture-per-region, not entities); `data_source` column captures which provider supplied the row.
- **Nullable vs required**: `fixture_id`, `country_id`, `provider_type`, `channel_name`, `data_source` required.
- **Migration risk**: low — additive. Initial population may be `data_source='manual_curation'` for SE (Viaplay/TV4/C More) until SportMonks broadcast addon contracted.
- **Validation**: insert `(fixture, SE, TV, 'Viaplay')` and `(fixture, UK, TV, 'Sky Sports')` — two rows; query by `(fixture_id, country_id='SE')` returns SE row only.

### 16. `weather_snapshots`

- **Purpose**: Weather observation/forecast at venue at a given time. Linked to fixtures via venue + kickoff window. FotMob-style "10°C night" panel.
- **Columns**: `id BIGSERIAL`, `venue_id BIGINT NOT NULL FK→venues.id`, `fixture_id BIGINT FK→fixtures.id` (nullable — weather can be queried for venue without fixture context), `observed_at TIMESTAMPTZ NOT NULL`, `temperature_c DECIMAL(4,1)`, `conditions_code VARCHAR(20) CHECK (conditions_code IN ('clear','clouds','rain','snow','storm','fog','mist','haze','unknown'))`, `is_forecast BOOLEAN NOT NULL`, `wind_speed_mps DECIMAL(5,1)`, `wind_direction_deg INT CHECK (wind_direction_deg BETWEEN 0 AND 360)`, `humidity_pct INT CHECK (humidity_pct BETWEEN 0 AND 100)`, `precipitation_mm DECIMAL(5,1)`, `pressure_hpa INT`, `uv_index DECIMAL(3,1)`, `icon_ref VARCHAR(255)`, `provider VARCHAR(50) NOT NULL` (e.g. `'open_meteo'`), `created_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: `venue_id → venues.id`, `fixture_id → fixtures.id`.
- **Unique**: `(venue_id, observed_at, provider, is_forecast)` — one provider gives one observation/forecast per timestamp per venue.
- **Indexes**: `(fixture_id)`, `(venue_id, observed_at DESC)`.
- **Hypertable**: candidate for hypertable on `observed_at` IF write volume becomes high (Open-Meteo at 10k req/day is unlikely to exceed; defer until needed). v0.6d ships as a regular table.
- **Provider mapping**: provider is a column, not via mapping table.
- **Nullable vs required**: `venue_id`, `observed_at`, `is_forecast`, `provider` required.
- **Migration risk**: low — additive, regular table.
- **Validation**: insert a test snapshot for a venue + fixture pair; query by `fixture_id` returns the snapshot.

### 17. `odds_snapshots`

- **Purpose**: Time-series odds movement. Append-only. Replaces the overwrite-pattern of `odds`. Source for value-bet movement card, sparklines, in-play next-goal widget. **Designed as TimescaleDB hypertable** (partition key `taken_at`).
- **Columns**: `id BIGSERIAL`, `fixture_id BIGINT NOT NULL FK→fixtures.id ON DELETE CASCADE`, `bookmaker_id BIGINT NOT NULL FK→bookmakers.id`, `market_code VARCHAR(30) NOT NULL CHECK (market_code IN ('H2H','TOTALS','SPREADS','BTTS','CORRECT_SCORE','NEXT_GOAL','NEXT_CARD','FIRST_GOALSCORER','ASIAN_HANDICAP','DOUBLE_CHANCE','DRAW_NO_BET'))`, `taken_at TIMESTAMPTZ NOT NULL`, `is_in_play BOOLEAN DEFAULT FALSE`, `is_suspended BOOLEAN DEFAULT FALSE`, `market_line DECIMAL(5,2)` (e.g. 2.5 for totals, +1.5 for handicap), `region VARCHAR(5)`, `outcomes JSONB NOT NULL` (typed shape: `[{"selection_code": "HOME", "value_numeric": null, "price_decimal": 1.85}, ...]`), `provider VARCHAR(50) NOT NULL`, `external_id VARCHAR(255)`.
- **PK**: `(id, taken_at)` (composite required by TimescaleDB).
- **FKs**: `fixture_id → fixtures.id`, `bookmaker_id → bookmakers.id`.
- **Unique**: `(fixture_id, bookmaker_id, market_code, market_line, taken_at, provider)` — append-only with idempotent re-fetches at same `taken_at` collapsed.
- **Indexes**: `(fixture_id, market_code, taken_at DESC)` (movement query for one market over time), `(bookmaker_id, taken_at DESC)`, `(provider, taken_at DESC)`.
- **Hypertable**: `SELECT create_hypertable('odds_snapshots', 'taken_at', chunk_time_interval => INTERVAL '7 days');`.
- **Retention**: in-play snapshots → 30 days; pre-match snapshots → 365 days (for value-bet historical analysis).
- **Provider mapping**: provider is a column.
- **Nullable vs required**: `fixture_id`, `bookmaker_id`, `market_code`, `taken_at`, `outcomes`, `provider` required.
- **Migration risk**: medium — hypertable creation, JSONB schema discipline (outcomes shape must be enforced at app layer since CHECK on JSONB structure is awkward).
- **Validation**: insert 5 snapshots over time for same fixture+market; query last snapshot per `(fixture, market)` correctly returns latest; insert a malformed `outcomes` JSON → app-layer rejects.

### 18. `bookmakers`

- **Purpose**: Canonical bookmaker lookup. Replaces the duplicated string-bookmaker concept in `odds.bookmaker` and `affiliate_links.bookmaker`.
- **Columns**: `id BIGSERIAL`, `code VARCHAR(50) NOT NULL UNIQUE` (e.g. `'bet365'`, `'unibet'`), `display_name VARCHAR(100) NOT NULL`, `logo_ref VARCHAR(255)`, `license_country_id BIGINT FK→countries.id`, `is_active BOOLEAN DEFAULT TRUE`, `external_ids JSONB DEFAULT '{}'`, `created_at TIMESTAMPTZ DEFAULT NOW()`.
- **PK**: `id`.
- **FKs**: `license_country_id → countries.id`.
- **Unique**: `(code)`.
- **Indexes**: `(code)` via unique.
- **Provider mapping**: yes — odds providers report bookmakers via their own keys.
- **Nullable vs required**: `code`, `display_name` required.
- **Migration risk**: low — additive. Backfill 4 SE bookmakers from `affiliate_links` seed (bet365, unibet, betsson, leovegas).
- **Validation**: row count == 4 after seed; FK from `affiliate_links.bookmaker_id` resolves.

### 19. `fixture_momentum`

- **Purpose**: Time-series of attack-momentum signal per fixture. SofaScore Attack Momentum graph + FotMob equivalent. Either provider-supplied OR derived from `fixture_events` over rolling time windows. **Designed as TimescaleDB hypertable** (partition key `observed_at`).
- **Columns**: `id BIGSERIAL`, `fixture_id BIGINT NOT NULL FK→fixtures.id ON DELETE CASCADE`, `observed_at TIMESTAMPTZ NOT NULL`, `match_minute INT NOT NULL`, `match_stoppage INT DEFAULT 0`, `home_momentum_pct DECIMAL(5,2) NOT NULL CHECK (home_momentum_pct BETWEEN 0 AND 100)`, `away_momentum_pct DECIMAL(5,2) NOT NULL CHECK (away_momentum_pct BETWEEN 0 AND 100)`, `source VARCHAR(20) NOT NULL CHECK (source IN ('provider','derived'))`, `provider VARCHAR(50)` (NULL when source='derived'), `derivation_window_seconds INT` (NULL when source='provider'; e.g. 60 for 1-min rolling).
- **PK**: `(id, observed_at)`.
- **FKs**: `fixture_id → fixtures.id`.
- **Unique**: `(fixture_id, observed_at, source, provider)`.
- **Indexes**: `(fixture_id, match_minute, match_stoppage)`.
- **Hypertable**: `SELECT create_hypertable('fixture_momentum', 'observed_at', chunk_time_interval => INTERVAL '1 day');`.
- **Retention**: 90 days (live-window only; momentum history rarely queried post-match beyond highlights).
- **Provider mapping**: provider is a column when `source='provider'`.
- **Nullable vs required**: `fixture_id`, `observed_at`, `match_minute`, `home_momentum_pct`, `away_momentum_pct`, `source` required.
- **Migration risk**: medium — hypertable; CHECK constraint that home + away ≈ 100 is deferred to app layer (CHECK on cross-column sum is awkward in PG).
- **Validation**: insert 90 momentum samples (90 minutes × 1/min) for a fixture; query timeline for chart rendering returns chronological series.

### 20. `user_motm_votes`

- **Purpose**: User Man-of-the-Match votes per fixture. Community engagement. Distinct from `user_predictions` (which is H/D/A tipping). One vote per user per fixture, transactional.
- **Columns**: `id BIGSERIAL`, `user_id BIGINT NOT NULL FK→users.id`, `fixture_id BIGINT NOT NULL FK→fixtures.id`, `voted_player_id BIGINT NOT NULL FK→players.id`, `voted_at TIMESTAMPTZ DEFAULT NOW()`, `is_locked BOOLEAN DEFAULT FALSE` (locked after fulltime + 60min).
- **PK**: `id`.
- **FKs**: `user_id → users.id`, `fixture_id → fixtures.id`, `voted_player_id → players.id`.
- **Unique**: `(user_id, fixture_id)` — one vote per user per fixture.
- **Indexes**: `(fixture_id, voted_player_id)` (vote tally per fixture per player).
- **Provider mapping**: none (community data, not provider-supplied).
- **Nullable vs required**: all required.
- **Migration risk**: very low — additive.
- **Validation**: insert vote; tally query `SELECT voted_player_id, count(*) FROM user_motm_votes WHERE fixture_id=? GROUP BY 1 ORDER BY 2 DESC` returns ranked list.

---

## Existing Tables to Extend

Each extension is **additive only** — new nullable columns + new indexes + new FK constraints (validated against backfilled data). No column drops in v0.6a–f. Drops happen in v0.7 cleanup behind a deprecation gate.

### `leagues` (extend in v0.6a3)

Add: `sport_id BIGINT FK→sports.id`, `country_id BIGINT FK→countries.id` (replaces free-text `country`), `tier INT`, `slug VARCHAR(50)` (eventually unique after backfill), `external_ids JSONB DEFAULT '{}'`. Widen `type` enum (currently `'league' | 'cup'`) to include `'international'`, `'qualification'`, `'knockout'` so the table can carry CL/EL/UECL/World Cup correctly without a rename.

Keep deprecated: `api_football_id` (canonical mapping moves to `provider_entity_mappings`; column stays as cache), `country` (string; replaced by `country_id`).

**No rename in v0.6.** The table name stays `leagues`. The `competitions` rename target lives in §Proposed Canonical Tables #3 as a v0.7+ design reference; v0.6 fills its role by extending `leagues` in place. Rename is gated on API + frontend readiness in v0.7+.

### `teams` (extend in v0.6a3 → v0.6b)

v0.6a3 additive: `country_id BIGINT FK→countries.id`, `slug VARCHAR(100)`, `colors_primary VARCHAR(7)` (hex `#RRGGBB`), `colors_secondary VARCHAR(7)`, `external_ids JSONB DEFAULT '{}'`.

v0.6b additive: `primary_venue_id BIGINT FK→venues.id` (replaces free-text `venue_name` + `venue_capacity`).

Keep deprecated: `api_football_id`, `country` (string), `venue_name`, `venue_capacity`.

### `fixtures` (extend in v0.6a3 → v0.6b → v0.6c)

v0.6a3 additive: `season_id BIGINT FK→seasons.id` (alongside existing `season INT` for one cycle), `external_ids JSONB DEFAULT '{}'`, `live_minute INT`, `live_stoppage INT`, `attendance INT`, `postponed_from TIMESTAMPTZ`, **expand `MatchStatus` enum** to add `IN_PLAY`, `IN_PROGRESS_EXTRA_TIME`, `IN_PROGRESS_PENALTIES`, `SUSPENDED`, `AWARDED` (current values stay valid). Existing `LIVE`/`HALFTIME`/`FINISHED` map cleanly; the new values handle provider variance.

v0.6b additive: `venue_id BIGINT FK→venues.id`, `referee_id BIGINT FK→referees.id`.

v0.6c additive: deprecate `stats JSONB` (mark as not-populated; new `fixture_statistics` table is the truth). Column stays for one cycle.

Keep deprecated: `api_football_id`, `season INT`.

**Time-zone discipline**: the current `kickoff DateTime` is naive (no tz). This is a known-debt flagged in `project_scorelock.md`. **v0.6 does NOT touch `fixtures.kickoff` in any sub-batch.** No additive `kickoff_utc TIMESTAMPTZ` or `kickoff_tz VARCHAR` columns are introduced in v0.6a–f. Migration to a TZ-aware column is a v0.7+ project — requires application-layer dual-write coordination (write to both naive `kickoff` and a new TZ column for one cycle), backfill, then cutover. Out of scope for v0.6.

### `standings` (extend in v0.6a3)

Additive: `season_id BIGINT FK→seasons.id` (alongside existing `season INT`), `zone VARCHAR(20) CHECK (zone IN ('CL','EL','UECL','RELEGATION','PROMOTION','PLAYOFF','NONE'))` DEFAULT 'NONE', `home_played INT`, `home_won INT`, `home_drawn INT`, `home_lost INT`, `home_goals_for INT`, `home_goals_against INT`, `away_played INT`, `away_won INT`, `away_drawn INT`, `away_lost INT`, `away_goals_for INT`, `away_goals_against INT`, `provider VARCHAR(50)`.

### `odds` (extend in v0.6e)

Additive: `bookmaker_id BIGINT FK→bookmakers.id` (alongside existing string `bookmaker` for one cycle), `market_code VARCHAR(30)` (alongside string `market`), `is_in_play BOOLEAN DEFAULT FALSE`, `region VARCHAR(5)`.

This table becomes a **latest-snapshot cache** (UPSERT-target on `(fixture_id, bookmaker_id, market_code)`). The append-only time series lives in `odds_snapshots`. Reads that need movement use snapshots; reads that need "latest" use this table for fast lookup.

### `predictions` (extend in v0.6e)

Additive: `markets_json JSONB DEFAULT '{}'` (predictions for non-1X2 markets like BTTS, correct score, next goal — typed shape enforced at Pydantic layer), `kelly_fraction DECIMAL(5,4)` (already in Pydantic `ValueBetResponse`, missing as DB column).

### `articles` (extend in v0.6f)

Additive: `model_version VARCHAR(50)` (currently buried in `meta_data JSONB`), `team_associations BIGINT[]` (Postgres array of team_ids, for fast "articles about team X" query without an M:N table). Indexes: `(model_version)`, GIN on `team_associations`.

### `affiliate_links` (extend in v0.6e)

Additive: `bookmaker_id BIGINT FK→bookmakers.id` (replaces the duplicate-string `bookmaker` column for canonical FK; keep string column for one cycle).

---

## Provider Mapping Strategy

**Recommendation: HYBRID** — `provider_entity_mappings` table as truth + `external_ids JSONB DEFAULT '{}'` cache column on hot rows.

### How external IDs are stored

- **Truth source**: `provider_entity_mappings` table. One row per `(entity_type, provider, external_id)`. Indexed by `(entity_type, canonical_id)` for reverse lookup ("what providers know about this team?") and by `(entity_type, provider, external_id)` for forward lookup ("what canonical entity is this provider's external_id?").
- **Hot-path cache**: every entity table that gets queried in a tight loop carries `external_ids JSONB DEFAULT '{}'` — populated as `{"sportmonks": "12345", "api_football": "678", "football_data": "PL-12"}`. Avoids a join when serializing to API responses.
- **Cache invalidation**: on every INSERT/UPDATE to `provider_entity_mappings`, a trigger (or app-layer write) updates the corresponding `external_ids` JSONB on the canonical row. App-layer write is preferred — triggers are surprising in code review.

### JSONB-only vs mapping-table-only vs hybrid

| Approach | Pros | Cons | Verdict |
|---|---|---|---|
| **JSONB only** (`external_ids` on every canonical row) | Simple — one extra column. Read is single-row. | Reverse lookup ("what canonical_id has SportMonks ID 5247?") requires `WHERE external_ids @> '{"sportmonks":"5247"}'` — works with GIN index but is awkward, slower, and less introspectable. Audit trail (first_seen, last_seen, confidence) is not addressable. | Rejected. |
| **Mapping-table only** (`provider_entity_mappings`, no JSONB cache) | Clean reverse lookup. Audit trail. Per-provider query ergonomics. | Every API response that needs a provider's external_id (e.g. for affiliate link templating) requires a join. Hot-path latency penalty in match-detail rendering. | Rejected as primary-only. |
| **HYBRID** (table + JSONB cache) | Truth source is the table (consistent, audit-traceable). Hot reads use the JSONB cache (one fewer join). Cache rebuilds from the table on demand. | Two write-paths must stay in sync. Mitigated by app-layer write through a single helper. | **Recommended.** |

### Avoiding duplicate teams/players across providers

- **Canonical name + country + sport** is the natural identity for `teams`. Two providers reporting "Nottingham Forest" + GB + football → match to existing canonical_id, add per-provider mapping. Two providers reporting "Forest" + GB + football → name-similarity match (Levenshtein distance < threshold) with confidence < 1.00 → flag for admin review (write to `provider_entity_mappings` with `confidence=0.85` and `created_by='auto'`).
- **`canonical_name` + `date_of_birth` + `nationality`** is the natural identity for `players`. Date of birth is the disambiguator (two players named "James Rodríguez" exist; one is Colombian, born 1991; one is Mexican, born 1990).
- **Manual override**: admin endpoint `/admin/providers/mappings/resolve` accepts `(canonical_id, provider, external_id, confidence=1.00, created_by='admin')` for the cases where auto-match misses.

### Canonical identity rules

- Canonical IDs are **internal** `BIGSERIAL`. Providers never see them. The `id` column is never exposed in API responses to external consumers (frontend uses the same internal IDs because frontend is internal).
- Canonical names are **English by default**. Localized names live in `display_name_sv` columns where applicable. Canonical name changes require admin approval (logged).
- Canonical IDs are **append-only**. Soft-delete via `is_active=false`, never DELETE.

### Merge / conflict strategy

- **Provider priority**: registry rule order (defined in `backend/app/providers/registry.py`) wins by default for any given `(operation, scope)`.
- **Field-specific overrides**: a `field_priorities` config dict allows "trust SportMonks for xG, trust API-Football for final score" without touching call sites.
- **Conflict logging**: when two providers return divergent values for the same canonical entity/field within the same refresh window, write a `provider_conflicts` row (table introduced in v0.6a2 as part of the provider audit layer, designed in `docs/PROVIDER_ABSTRACTION_V0.4.md` § Provider Registry and Fallback Rules → "Conflict resolution"). Admin UI surfaces these for manual resolution.
- **Manual override authority**: admin can mark a field value as authoritative, suppressing further provider updates until cleared. State stored in `provider_conflicts.resolved_by_admin_id`.

### Raw payload retention

- Per § Time-Series Strategy below: live-window 30 days, pre/post 180 days, schema-rare indefinite, mappings never pruned.

### Replay-normalization implications

- Every normalized row carries `provider VARCHAR(50)` and (where relevant) `external_id VARCHAR(255)`. `provider_payloads.id` is the audit anchor.
- Replay-normalize CLI (planned for v0.5d per `docs/PROVIDER_ABSTRACTION_V0.4.md` § Replay/debug strategy): `python -m app.providers.normalization --from-payload <payload_id>` re-runs the normalizer against the stored payload. Idempotent — overwrites canonical row if output differs (logged as drift event).
- Schema-drift detection: when `ProviderPayloadError` fires during normalization, the offending payload is retained with a flag; daily report lists drift cases for engineer review.

---

## Time-Series Strategy

**Local stack already runs `timescale/timescaledb:latest-pg16`** per `docker-compose.yml`. The TimescaleDB extension is available and unused. **v0.6a does NOT require the extension** (provider_payloads is now a regular table). The first — and only — hypertables in the v0.6 plan are `odds_snapshots` and `fixture_momentum`, both created in v0.6e. The TimescaleDB extension creation on Railway-prod is therefore deferred from v0.6a to v0.6e.

### Hypertable decisions

| Table | Hypertable in v0.6? | Partition key | Chunk interval | Retention | Why |
|---|---|---|---|---|---|
| `odds_snapshots` | **Yes (v0.6e)** | `taken_at` | 7 days | in-play 30d / pre-match 365d | Append-only, one row per (fixture, bookmaker, market) per fetch interval. Movement queries are time-window scans (`WHERE fixture_id=? AND market_code='H2H' AND taken_at > now() - interval '24 hours'`). Hypertable benefits apply directly. |
| `fixture_momentum` | **Yes (v0.6e)** | `observed_at` | 1 day | 90 days | Append-only, one row per fixture per minute (~90 rows per fixture). Live-window read pattern matches hypertable strengths. |
| `provider_payloads` | **No (defer to v0.7+)** | — | — | scheduled DELETE retention task | Audit/debug storage. Read patterns are point lookups (replay by `id`, latest by entity), not time-window scans — hypertable benefits don't apply. Retention via Celery `prune_provider_payloads` task on `(fetched_at)` index. Reassess for hypertable promotion in v0.7+ if write volume crosses ~100M rows OR storage exceeds 50 GB. In-place conversion supported (`SELECT create_hypertable(..., migrate_data => true)`). |
| `fixture_statistics` | **No** | — | — | — | One row per (fixture, team, provider). Updated in place during live, frozen at fulltime. Relational — typical "latest stats for fixture X" query is a single-row UPSERT-target lookup, not a time-window scan. Progression-over-time is deferred to v0.7+ via a separate `fixture_statistics_snapshots` hypertable IF the UI needs it. |
| `weather_snapshots` | **No (defer to v0.7+)** | — | — | — | Read pattern is "weather for venue X at fixture Y kickoff" — a single-row lookup, not a time-window scan. Open-Meteo at 10k req/day stays well under hypertable break-even. v0.6d ships as a regular table. Promote to hypertable in a later version if volume + read pattern justify. |
| `fixture_events` | **No** | — | — | — | Read pattern is "all events for fixture X ordered by minute" — relational scan with 10–30 rows. No time-window queries. Hypertable would over-engineer. |
| `fixture_commentary` | **No** | — | — | — | Same as fixture_events — small per-fixture cardinality, no time-window read. |

### Why TimescaleDB matters here (and where it does not yet)

- `odds_snapshots` for 100 fixtures/day × 5 bookmakers × 5 markets × 5min pre-match polling = 3 600 rows/day. In-play polling at 60s × 90min × 100 fixtures × 5 bookmakers × 3 markets = 67 500 rows per matchday. Annualized: ~25M rows. Time-window movement queries (`taken_at > now() - 24h`) match hypertable chunk-pruning exactly. Hypertable in v0.6e.
- `fixture_momentum` is small per-fixture but persistent — 90 rows × 100 fixtures/day × 365 = 3.3M rows/year. Live-window chart reads benefit from hypertable retention auto-prune. Hypertable in v0.6e.
- `provider_payloads` could grow to ~1 GB/month at modest provider volume (5 providers × 1 fetch/min × 30 days × ~3 KB/payload), but the **dominant access patterns are point lookups** (replay by id, latest by entity). A regular table with `(fetched_at)` index + scheduled DELETE retention task handles this without hypertable complexity. Promotion path is preserved for v0.7+ if volume warrants it.

### Query patterns (for design validation)

- `provider_payloads`: `WHERE provider='sportmonks' AND operation='fixtures' ORDER BY fetched_at DESC LIMIT 1` (latest), `WHERE external_id='5247' ORDER BY fetched_at DESC` (entity history).
- `odds_snapshots`: `WHERE fixture_id=? AND market_code='H2H' AND taken_at > now() - interval '24 hours' ORDER BY taken_at` (movement), `WHERE fixture_id=? ORDER BY taken_at DESC LIMIT 1 PER (bookmaker_id, market_code)` (latest per market).
- `fixture_momentum`: `WHERE fixture_id=? ORDER BY observed_at` (full timeline for chart).

### Risk

- TimescaleDB extension on Railway-prod requires `CREATE EXTENSION` privilege. Verify the Railway DB user has this; if not, escalate to support **before v0.6e** (the first batch that needs it). Memory note in `project_scorelock.md` says local DB is `timescale/timescaledb:latest-pg16` but Railway DB type is plain Postgres — **needs verification before v0.6e**. By moving the extension prerequisite from v0.6a to v0.6e, we get four batches' worth of runway to resolve this without blocking v0.6a/b/c/d.
- Composite PK on hypertables (`(id, taken_at)` for odds_snapshots, `(id, observed_at)` for fixture_momentum) is required by TimescaleDB. App-layer queries that assume `id` alone is unique must use the composite or disambiguate by the partition column.

---

## Migration Plan

Six small additive batches. Every batch ships with: numbered Alembic revision, verified down-migration, seeded mock data, contract test, validation commands. No batch crosses two of (identity, write-path, read-path).

### v0.6a1 — Reference data (sports / countries / seasons)

- **Goal**: Stand up the static reference catalogues that everything else FKs into. Tables: `sports`, `countries`, `seasons`. **No `competitions` table** — that role is played by extending `leagues` in v0.6a3. **No FK changes to existing tables yet** — those land in v0.6a3.
- **Tables touched**: 3 new.
- **Backfill required**: yes — seed `sports` with one row (`'football'`), `countries` from ISO 3166-1 reference list (~250 rows), `seasons` from existing distinct `(league_id, season)` pairs in `fixtures` and `standings`. All mechanical.
- **Risk**: very low — pure additive lookup tables; no FK from any existing table.
- **Rollback strategy**: down-migration drops 3 tables. Backfilled reference data lost (acceptable — reproducible from ISO list + existing data).
- **Validation commands**:
  - `docker compose exec backend alembic upgrade head`
  - `docker exec scorelock-db psql -U scorelock -d scorelock -c "SELECT count(*) FROM sports"` → 1
  - `docker exec scorelock-db psql -U scorelock -d scorelock -c "SELECT count(*) FROM countries"` → ≥ 250
  - `docker exec scorelock-db psql -U scorelock -d scorelock -c "SELECT count(*) FROM seasons"` → matches distinct `(league_id, season)` from existing tables
  - `docker compose exec backend alembic downgrade -1` then `alembic upgrade head` → reversibility verified

### v0.6a2 — Provider audit + mapping (provider_payloads / provider_entity_mappings / provider_conflicts)

- **Goal**: Stand up the provider audit + identity-mapping foundation. Tables: `provider_payloads` (regular table, **not hypertable**), `provider_entity_mappings`, `provider_conflicts`. Backfill `provider_entity_mappings` from existing `api_football_id` columns on `leagues`, `teams`, `fixtures`. **No TimescaleDB extension required.** **No changes to existing tables** — `api_football_id` columns stay; mappings are added alongside.
- **Tables touched**: 3 new.
- **Backfill required**: yes — INSERT one row per `leagues.api_football_id` (`entity_type='competition'`, `provider='api_football'`), one row per `teams.api_football_id`, one row per `fixtures.api_football_id`. Idempotent (UNIQUE on `(entity_type, provider, external_id)`).
- **Risk**: low — additive; backfill is mechanical and reversible (DELETE WHERE provider='api_football' on rollback).
- **Rollback strategy**: down-migration drops 3 tables. Backfilled rows lost (reproducible from existing `api_football_id` columns).
- **Validation commands**:
  - `docker compose exec backend alembic upgrade head`
  - `docker exec scorelock-db psql -U scorelock -d scorelock -c "\dt provider*"` → expect 3 tables (`provider_payloads`, `provider_entity_mappings`, `provider_conflicts`)
  - `docker exec scorelock-db psql -U scorelock -d scorelock -c "SELECT count(*) FROM provider_entity_mappings WHERE entity_type='competition' AND provider='api_football'"` → equals `(SELECT count(*) FROM leagues WHERE api_football_id IS NOT NULL)`
  - Same check for `entity_type='team'` and `entity_type='fixture'`
  - `docker compose exec backend alembic downgrade -1` then `alembic upgrade head`

### v0.6a3 — Additive FK / JSONB extensions on existing tables

- **Goal**: Extend `leagues`, `teams`, `fixtures`, `standings` with new nullable FK columns (`sport_id`, `country_id`, `season_id`, etc.) + `external_ids JSONB DEFAULT '{}'` cache columns. Widen `leagues.type` enum to include `'international'`, `'qualification'`, `'knockout'`. Widen `MatchStatus` enum to include `IN_PLAY`, `IN_PROGRESS_EXTRA_TIME`, `IN_PROGRESS_PENALTIES`, `SUSPENDED`, `AWARDED`. Backfill `country_id` from `country` string (best-effort fuzzy ISO match), `season_id` from `(league_id, season)` pairs. **No `kickoff` timezone change.** **No `leagues → competitions` rename.** **No drops.**
- **Tables touched**: 4 extended (`leagues`, `teams`, `fixtures`, `standings`).
- **Backfill required**: yes — `country_id` (best-effort), `season_id` (mechanical from existing pairs), `external_ids` populated via `provider_entity_mappings` reverse-lookup.
- **Risk**: medium — touches live tables. New columns are nullable (no NOT NULL added). Best-effort backfill misses are logged, not failures. Enum widening is additive (existing values stay valid).
- **Rollback strategy**: down-migration drops new columns, narrows enums back to original values (only safe if no rows use the new enum values yet — assert pre-rollback). Existing rows untouched.
- **Validation commands**:
  - `docker compose exec backend alembic upgrade head`
  - `docker exec scorelock-db psql -U scorelock -d scorelock -c "\d+ leagues"` → expect new columns visible
  - `docker exec scorelock-db psql -U scorelock -d scorelock -c "SELECT count(*) FROM leagues WHERE country_id IS NULL AND country IS NOT NULL"` → backfill miss count, logged
  - `docker exec scorelock-db psql -U scorelock -d scorelock -c "SELECT count(*) FROM fixtures WHERE season_id IS NULL"` → 0 after backfill
  - `docker exec scorelock-db psql -U scorelock -d scorelock -c "SELECT enum_range(NULL::matchstatus)"` → returns 11 values (6 original + 5 new)
  - `docker compose exec backend alembic downgrade -1` then `alembic upgrade head`

### v0.6b — Players / venues / referees

- **Goal**: Add the entity catalogues for the three "person/place" types. `players`, `venues`, `referees`. Extend `teams` with `primary_venue_id`. Extend `fixtures` with `venue_id`, `referee_id`. Backfill `venues` from `teams.venue_name` (best-effort fuzzy match; misses logged).
- **Tables touched**: 3 new + 2 extended.
- **Backfill required**: yes — `venues` from `teams.venue_name` + `teams.venue_capacity`. Best-effort; manual override allowed afterwards.
- **Risk**: low. Backfill is fuzzy but failures are "no row" not "wrong row".
- **Rollback strategy**: down-migration drops tables + columns. Backfilled rows lost (acceptable — backfill is reproducible).
- **Validation commands**:
  - `alembic upgrade head`
  - `psql ... -c "SELECT count(*) FROM venues"` → expect ~ count of distinct `(venue_name, country)` from teams (best-effort)
  - `psql ... -c "SELECT count(*) FROM teams WHERE primary_venue_id IS NULL AND venue_name IS NOT NULL"` → backfill miss count, logged
  - `alembic downgrade -1` then `alembic upgrade head`

### v0.6c — Events / lineups / statistics / commentary / MoM votes

- **Goal**: Add the per-fixture metadata depth tables. `fixture_events`, `fixture_lineups`, `fixture_lineup_players`, `fixture_statistics`, `fixture_commentary`, `user_motm_votes`. Mark `fixtures.stats JSONB` as deprecated (column stays; comment added).
- **Tables touched**: 6 new + 1 deprecated column.
- **Backfill required**: no. New tables, empty on creation. Population in v0.5d when SportMonks/API-Football lineup + event data flows.
- **Risk**: low-medium. Largest schema batch, but every table is additive with FK to existing tables.
- **Rollback strategy**: down-migration drops 6 tables. No data loss (no rows yet).
- **Validation commands**:
  - `alembic upgrade head`
  - `psql ... -c "\dt fixture_*"` → expect 5 fixture_* tables
  - `psql ... -c "INSERT INTO fixture_events (fixture_id, minute, event_type, team_id, primary_player_id, provider) VALUES (1, 17, 'GOAL', 1, 1, 'manual')"` (with seeded test rows from v0.6b) → succeeds
  - CHECK constraint test: `INSERT ... event_type='WIBBLE'` → rejected
  - `alembic downgrade -1` then `alembic upgrade head`

### v0.6d — Broadcasts / weather

- **Goal**: Add the FotMob-style "where to watch" + venue-card weather tables. `fixture_broadcasts`, `weather_snapshots`. Extend `affiliate_links` (deferred to v0.6e but conceptually related).
- **Tables touched**: 2 new.
- **Backfill required**: no for `weather_snapshots`. For `fixture_broadcasts`, optional manual seed of SE broadcast data (Viaplay/TV4/C More) for upcoming Allsvenskan matches if launch-relevant — counts as data, not migration.
- **Risk**: low.
- **Rollback strategy**: down-migration drops 2 tables.
- **Validation commands**:
  - `alembic upgrade head`
  - `psql ... -c "INSERT INTO fixture_broadcasts (fixture_id, country_id, provider_type, channel_name, data_source) VALUES (1, (SELECT id FROM countries WHERE iso_2='SE'), 'STREAMING', 'Viaplay', 'manual_curation')"` → succeeds
  - `psql ... -c "INSERT INTO weather_snapshots (venue_id, observed_at, conditions_code, is_forecast, provider) VALUES (1, now(), 'clear', true, 'open_meteo')"` → succeeds
  - `alembic downgrade -1` then `alembic upgrade head`

### v0.6e — Odds snapshots / momentum / bookmakers (first hypertables; first TimescaleDB use)

- **Goal**: Add the time-series odds + momentum tables and the `bookmakers` lookup. **Install TimescaleDB extension on Railway-prod** (`CREATE EXTENSION IF NOT EXISTS timescaledb`) — this is the first batch that requires it. Extend `odds`, `affiliate_links` with `bookmaker_id` FK. Extend `predictions` with `markets_json` + `kelly_fraction`. Backfill `bookmakers` from `affiliate_links` seed (4 SE bookmakers). Both new hypertables (`odds_snapshots`, `fixture_momentum`) created here.
- **Tables touched**: 3 new + 3 extended.
- **Backfill required**: yes — `bookmakers` from `affiliate_links`. Update `affiliate_links.bookmaker_id` and `odds.bookmaker_id` from string-match.
- **Risk**: medium-high. First TimescaleDB use on Railway-prod (Open Question Q10 must be answered before this batch lands). Two hypertables created. odds_snapshots has the most complex unique constraint. Mitigation: pre-flight verify extension privilege; fallback plan is regular tables for both (sub-optimal but workable).
- **Rollback strategy**: down-migration drops 3 tables, drops new columns. String columns stay populated, so deprecation is reversible. Extension stays installed (idempotent — does not drop).
- **Validation commands**:
  - `alembic upgrade head`
  - `psql ... -c "SELECT extname FROM pg_extension WHERE extname='timescaledb'"` → returns one row
  - `psql ... -c "SELECT show_chunks('odds_snapshots')"` → returns one chunk after first insert
  - `psql ... -c "SELECT show_chunks('fixture_momentum')"` → same
  - `psql ... -c "SELECT count(*) FROM bookmakers"` → 4 (bet365, unibet, betsson, leovegas)
  - `psql ... -c "SELECT count(*) FROM affiliate_links WHERE bookmaker_id IS NULL"` → 0 after backfill
  - `alembic downgrade -1` then `alembic upgrade head`

### v0.6f — API read endpoints (no migration)

- **Goal**: Add the read APIs. **No migration in this version** — pure backend API expansion. New handlers in `backend/app/api/routes.py`. New Pydantic schemas in `backend/app/schemas/schemas.py`. New read helpers in `backend/app/services/db_service.py`. Extends the H2H endpoint with `limit` + `competition_filter` per `docs/COMPETITOR_SYNTHESIS_V0.3.md` § Match Detail Page Requirements. Articles extension from this design lands here too (`model_version`, `team_associations`).
- **Tables touched**: 1 extended (`articles`).
- **Backfill required**: yes — extract `model_version` from `articles.meta_data JSONB` to new column.
- **Risk**: low. Read-only handlers serving the new tables.
- **Rollback strategy**: revert handler additions; existing endpoints unaffected.
- **Validation commands**:
  - `make test`
  - `curl -s http://localhost:8000/api/v1/fixtures/1/events | python -m json.tool` → returns events array (or empty)
  - `curl -s http://localhost:8000/api/v1/fixtures/1/lineups | python -m json.tool`
  - `curl -s http://localhost:8000/api/v1/fixtures/1/statistics | python -m json.tool`
  - `curl -s http://localhost:8000/api/v1/fixtures/1/broadcasts?country=SE | python -m json.tool`
  - `curl -s http://localhost:8000/api/v1/fixtures/1/momentum | python -m json.tool`

---

## Backend API Implications

New endpoints planned in v0.6f (no implementation in this design doc). All read-only, all behind ScoreLock's existing auth (where applicable; match-detail data is publicly readable per current pattern).

| Endpoint | Data source tables | Cache strategy | Frontend consumer |
|---|---|---|---|
| `GET /api/v1/fixtures/{id}/events` | `fixture_events` (chronological) + `players` (join for name) + `teams` (join for crest) | Cache in Redis 30s for live fixtures, 1h for finished | Match-detail event timeline |
| `GET /api/v1/fixtures/{id}/lineups` | `fixture_lineups` + `fixture_lineup_players` + `players` | Cache 5min once `state='CONFIRMED'`; 30s while `state='PROJECTED'` | Pitch-view component |
| `GET /api/v1/fixtures/{id}/statistics` | `fixture_statistics` (one row per team) | Cache 30s for live, 1h for finished | Stats panel |
| `GET /api/v1/fixtures/{id}/commentary` | `fixture_commentary` (chronological, paginated by minute) | Cache 30s for live, 24h for finished | Commentary feed |
| `GET /api/v1/fixtures/{id}/broadcasts` | `fixture_broadcasts` filtered by `?country=SE` (default from `Accept-Language`) + `affiliate_links` join | Cache 1h | "Where to watch" card |
| `GET /api/v1/fixtures/{id}/odds/snapshots` | `odds_snapshots` filtered by `?market=H2H&since=...` | No cache (movement is the point); use TimescaleDB chunk pruning | Odds-movement sparkline, value-bet card |
| `GET /api/v1/fixtures/{id}/momentum` | `fixture_momentum` (chronological) | Cache 30s during live; 24h post-match | Momentum chart |
| `GET /api/v1/fixtures/{id}/intelligence` | Computed: combine `fixtures` + `predictions` + latest `articles` (preview type) + `fixture_statistics` for narrative | Cache 5min | AI intelligence card |
| `GET /api/v1/players/{id}` | `players` + recent `fixture_lineup_players` for form summary | Cache 1h | Player profile (deferred UI) |
| `GET /api/v1/teams/{id}/squad` | `players WHERE current_team_id=?` + most recent `fixture_lineup_players` rows | Cache 1h | Team squad page (deferred UI) |
| `GET /api/v1/fixtures/{id}/standings-projection` | `standings` + `fixtures` (compute "if HOME wins") | Cache 30s | Standings impact panel |
| `POST /api/v1/fixtures/{id}/motm-vote` | `user_motm_votes` (UPSERT on `(user_id, fixture_id)`) | n/a (write) | MoM poll widget |
| `GET /api/v1/fixtures/{id}/motm-tally` | `user_motm_votes` aggregated by `voted_player_id` + `players` join | Cache 10s | MoM poll widget |
| `GET /api/v1/h2h/{team1_id}/{team2_id}?limit=10&competition_id=...` | Existing `fixtures` query + new optional filters | Cache 1h | H2H tab |

---

## Frontend Product Implications

Mapping schema to v0.7 match-detail components (per `docs/COMPETITOR_SYNTHESIS_V0.3.md` § Match Detail Page Requirements). No frontend code in v0.5c — this is the scope handoff for v0.7.

| Component | Schema source | Notes |
|---|---|---|
| **Match header** | `fixtures` + `teams` + `competitions` (or `leagues`) + `seasons` | Add team color stripes from `teams.colors_primary/secondary` |
| **Live status** | `fixtures.live_minute`, `live_stoppage`, `status` | Hooks into existing `use-live-scores.ts`; backend WebSocket needs feeding (out of v0.5c scope) |
| **Event timeline** | `fixture_events` + `players` + `teams` | Icon set per event_type; VAR events get special treatment |
| **Lineup pitch** | `fixture_lineups.formation_code` + `fixture_lineup_players.{position_code,grid_x,grid_y,is_starter,is_captain}` | Pitch SVG positioning from `(grid_x, grid_y)` |
| **Stats panel** | `fixture_statistics` (two rows: home + away) | Dual-bar chart per stat |
| **Momentum graph** | `fixture_momentum` chronological series | Line/bar chart with `home_momentum_pct` / `away_momentum_pct` |
| **Odds / value widget** | `odds_snapshots` (latest per market) + `predictions` for value badge + `bookmakers` for logo | Sparkline from snapshot history |
| **Where-to-watch card** | `fixture_broadcasts WHERE country_id=user_country` + `affiliate_links` join | Affiliate CTA where `affiliate_link_id IS NOT NULL` |
| **Venue / weather / referee card** | `venues` + `weather_snapshots` (closest to kickoff) + `referees` | FotMob-style three-row card |
| **AI intelligence card** | `articles` (preview/report) + `predictions` + `fixture_statistics` | Inline article excerpt + value-bet badge |
| **User tipping** | Existing `user_predictions` | No schema change |
| **Man of the Match poll** | `user_motm_votes` (write) + tally endpoint (read) | Inline ranked list of voted players |
| **Commentary feed** | `fixture_commentary` chronological with locale fallback | `text_sv` if available, else `text_en` |

---

## Open Questions

Decisions that must be answered before v0.6a1 migration is written. Each blocks a specific batch.

1. **Rename `leagues` → `competitions`?** **Decided in this revision: NOT in v0.6.** v0.6a3 extends the existing `leagues` table in place (widened `type` enum, new `sport_id`/`country_id`/`tier`/`slug`/`external_ids` columns) so the table can carry CL/EL/UECL/World Cup correctly without a rename. The `competitions` table spec stays in §Proposed Canonical Tables #3 as a v0.7+ design reference. Open follow-up: when (which version after v0.7) to perform the rename, gated on API + frontend readiness.
2. **Paid sports-data provider** (carried from `docs/PROVIDER_ABSTRACTION_V0.4.md` § Open Questions #1): SportMonks vs API-Football Pro vs Stats Perform. Determines which provider's `external_ids` schema gets the most rows + which `provider_entity_mappings.provider` value dominates.
3. **Broadcast-data source** (carried from PROVIDER_ABSTRACTION § Open Questions #2): SportMonks broadcast addon vs Nordic-specialist vs manual curation. Determines whether `fixture_broadcasts.data_source` is dominated by `'manual_curation'` initially.
4. **Player ratings source**: SportMonks vs Opta via Stats Perform vs API-Football. Determines `fixture_lineup_players.provider_rating_source` rows. Proprietary rating systems are off-limits per v0.4 Hard Rule #7 — provider ratings only.
5. **xG availability**: Confirm provider tier supplies xG (per-match team-level + per-shot expected). SportMonks Advanced does; API-Football free tier does not. Affects `fixture_statistics.xg` populate strategy.
6. **In-play odds tier** (carried from PROVIDER_ABSTRACTION § Open Questions #3): The Odds API $99/mo (in-play) vs $30/mo (pre-match only). Blocks `odds_snapshots.is_in_play=true` rows + the FotMob-style next-goal widget.
7. **Allsvenskan + Superettan coverage**: Confirm the chosen paid provider includes these. SportMonks does; API-Football Pro coverage is variable. Strategic-moat decision per v0.3 synthesis.
8. **Legal/licensing for logos and bookmaker marks**: `competitions.logo_ref`, `teams.logo_ref`, `players.photo_ref`, `bookmakers.logo_ref`, `fixture_broadcasts.logo_ref` all reference media. Hosting providers' assets vs licensing rights is unsettled. Recommendation: store URL references only (don't proxy or mirror); fall back to text labels if licensing is unclear.
9. **Retention policy for raw payloads** (carried from PROVIDER_ABSTRACTION § Open Questions #5): 30d live / 180d non-live OK from a GDPR + cost standpoint? Affects `provider_payloads` retention policy.
10. **TimescaleDB extension on Railway-prod**: Verify `CREATE EXTENSION timescaledb` is permitted on the Railway-managed Postgres. **No longer blocks v0.6a** — by deferring `provider_payloads` from hypertable to regular table, the extension is only needed at v0.6e (odds_snapshots, fixture_momentum). Verify before v0.6e; if Railway disallows, fall back to regular tables for those two as well, with sub-optimal but workable retention via scheduled DELETE.
11. **Time-zone migration of `fixtures.kickoff`**: **Decided in this revision: deferred to v0.7+.** No `kickoff_utc` or `kickoff_tz` columns added in any v0.6 batch (a–f). The naive `DateTime` stays as-is through v0.6f. v0.7+ migration is a standalone project: introduce TZ-aware column alongside, application-layer dual-write for one cycle, backfill, then cutover. Out of v0.6 scope.
12. **Naming consistency**: User's required table list uses `fixture_events`, `provider_entity_mappings`. The v0.4 design doc uses `match_events`, `provider_entity_ids`. v0.5c adopts the user's names. Confirm to lock the convention.
13. **`fixtures.stats JSONB` deprecation timeline**: column stays through v0.6c and is dropped in v0.7 cleanup, OR drop earlier? Recommendation: defer to v0.7 (one cycle's grace).
14. **Auto-vs-trigger for `external_ids` JSONB cache sync**: app-layer write helper (recommended) vs Postgres trigger. Triggers are surprising in code review; recommendation stands.
15. **Mock-provider scope** (carried from PROVIDER_ABSTRACTION § Open Questions #8): Mock data fixtures for v0.6c lineup + event tests — clean scenarios only OR include broken/conflict scenarios for chaos testing? Affects test fixtures committed under `backend/tests/fixtures/providers/mock/`.

---

## Final Recommendation

**READY FOR v0.6 MIGRATION DESIGN.**

Three of the four Open Questions that previously gated v0.6a are now resolved within this document:

- Q1 (`leagues` → `competitions` rename) → **decided: NOT in v0.6**; extend `leagues` in place. Rename target preserved as v0.7+ design reference.
- Q10 (TimescaleDB extension privilege on Railway-prod) → **no longer blocks v0.6a**; only v0.6e needs the extension (odds_snapshots, fixture_momentum). Provider_payloads is a regular table.
- Q11 (timezone of `fixtures.kickoff`) → **decided: deferred to v0.7+**; no v0.6 column changes.
- Q12 (naming convention: `fixture_*` prefix + `provider_entity_mappings`) → still pending owner confirmation; this is the only remaining gate on v0.6a1.

The remaining Open Questions (Q2–Q9, Q13–Q15) gate later v0.6 batches but do not block v0.6a1, v0.6a2, v0.6a3.

This design is internally consistent with `docs/PROVIDER_ABSTRACTION_V0.4.md` (post-v0.5b state) and `docs/COMPETITOR_SYNTHESIS_V0.3.md`. Every proposed table maps to at least one P0/P1 feature from the competitor synthesis. **Every change in v0.6a–f is additive — zero destructive renames, zero column drops, zero timezone conversions, zero hypertable creations until v0.6e.** Provider mapping is hybrid (truth table + JSONB cache); time-series is hypertable only for high-volume append-only data with time-window read patterns (odds_snapshots, fixture_momentum) and only in v0.6e.

Ready for review. No code, no migrations, no schema execution from this version. v0.6a1 migration writing begins after Open Question Q12 (naming convention) is confirmed.

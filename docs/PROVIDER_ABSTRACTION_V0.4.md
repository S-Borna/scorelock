# ScoreLock Provider Abstraction v0.4

> Design document. No application code created, modified, or refactored in this version. Cites current repo state at commit `fffb3ba`.
> Purpose: define the contract, normalized schema, registry, and migration path for a provider-neutral backend before any paid-provider integration work begins. Per v0.3 Hard Rule #4, no billable provider integration starts until the abstraction skeleton lands in a subsequent version.

---

## Executive Summary

- Today the backend has three direct provider clients (`api_football.py`, `football_data.py`, `odds_api.py`). Every one of them is a singleton imported by name from `backend/app/services/tasks.py` and `backend/app/services/seed.py`. There is no interface, no registry, no contract — swapping a provider today means editing every caller.
- `football_data.py` already contains a normalizer — but it normalizes to **API-Football's response shape**, not to a neutral internal shape. Adding a third provider (SportMonks) under that model would require each provider to fake being API-Football. That is the #1 coupling risk and the primary thing v0.4 must design away.
- `football_data.py` uses a `+ 2_000_000` ID offset to avoid collision with API-Football IDs. Works for two providers, breaks with three. Must be replaced with a provider-keyed mapping table.
- `odds_api.py` identifies leagues via `api_football_id` lookup. The odds provider inherits API-Football's identity model. Same coupling.
- `core/quota_manager.py` already exists with `can_call()` / `record_call()` primitives (used by `football_data` and `odds_api`, **not** by `api_football` — inconsistent). It's the right foundation for a provider-wide quota governance layer.
- Normalized domain objects are the unit of abstraction. Providers input → normalize → store. Every internal caller reads normalized objects. Nothing downstream (tasks, routes, AI pipeline, frontend) ever touches raw provider payloads.
- Raw provider payloads are retained in a dedicated `provider_payloads` table (JSONB, timestamped) for replay, conflict debugging, and legal evidence. The mapping between canonical internal IDs and per-provider external IDs lives in a dedicated `provider_entity_ids` table — not in `external_ids JSONB` columns, because per-provider queries are needed at scale.
- Fallback is operation-scoped, not provider-scoped: SportMonks may be primary for lineups while API-Football is primary for Allsvenskan fixtures on the same day. The registry resolves by `(operation, league/entity)` tuple.
- The design explicitly accommodates four provider categories: `SportsDataProvider` (fixtures, teams, players, lineups, events, stats), `OddsProvider` (odds only), `BroadcastProvider` (TV / streaming per country), `WeatherProvider` (kickoff weather). Each has its own interface; none assume the existence of the others.
- No paid integration, no schema migration, no runtime change in v0.4. The document defines the contract; implementation is sequenced across v0.5a → v0.5e → v0.6.

## Current Provider State

Cited files (read in this version, not modified):

### `backend/app/services/api_football.py` (226 lines)

- **Current responsibility**: Full-featured REST client for api-sports.io. Endpoints wrapped: `/leagues`, `/fixtures` (by date / league / id / live), `/fixtures/statistics`, `/fixtures/headtohead`, `/teams`, `/teams` (by league+season), `/standings`, `/odds`, `/players/squads`, `/injuries`, `/predictions`. Module-level `LEAGUE_IDS` dict maps ScoreLock's internal league slugs to API-Football integer IDs (22 leagues across Phase 1–3). Module-level `PHASE_1_LEAGUES` list (8 entries). Singleton `api_football = APIFootballClient()` instantiated at import.
- **Coupling risk**: **Highest of the three.** (1) Module-level `LEAGUE_IDS` is imported directly by `tasks.py`, `seed.py`, `historical.py` — every caller knows the API-Football league catalogue. (2) The `api_football_id` concept bleeds into `football_data.py` and `odds_api.py` as the canonical identifier. (3) No quota manager integration — the free tier's 100/day limit is not enforced at the client level (only logged via response header). (4) Singleton at import time means no swap or mock without patching.
- **Reusable parts**: The `httpx.AsyncClient` pattern, `tenacity` retry decorator, structured logging of rate-limit headers. Endpoint coverage is broad and will remain useful as one provider among several.
- **Must not change yet**: Everything. The whole file stays as-is through v0.4 and is wrapped behind the abstraction in v0.5d.

### `backend/app/services/football_data.py` (322 lines)

- **Current responsibility**: REST client for football-data.org v4. Endpoints: `/competitions/{code}`, `/competitions/{code}/standings`, `/competitions/{code}/matches`, `/competitions/{code}/teams`, `/competitions/{code}/scorers`. Module-level `FD_COMPETITIONS` dict maps FD competition codes to FD internal IDs **and to API-Football IDs** (the second mapping leaks the coupling). `FD_UNSUPPORTED_LEAGUES` set explicitly names leagues not covered (`allsvenskan`, `europa_league`, `conference_league`). Two normalizer statics: `normalize_match_to_fixture()` converts FD match → API-Football-shaped dict, and `normalize_standing()` same for standings. Uses quota manager (`football_data`, `football_data_daily` buckets). Singleton `football_data`.
- **Coupling risk**: (1) Normalization targets API-Football's response shape, not a neutral internal shape — forces all non-API-Football providers to mimic API-Football. (2) ID offset `+ 2_000_000` (line 237, 259, 264, 294) is a band-aid for ID collision that only works with two providers. (3) Raises a custom `QuotaExhaustedError` defined in the same file — duplicated in `odds_api.py`.
- **Reusable parts**: The quota-aware `_get()` pattern. The concept of normalization (but the target shape must change).
- **Must not change yet**: Everything.

### `backend/app/services/odds_api.py` (288 lines)

- **Current responsibility**: REST client for the-odds-api.com v4. Endpoints: `/sports`, `/sports/{key}/odds`, `/sports/{key}/events/{id}/odds`. Module-level `ODDS_SPORT_KEYS` dict maps The Odds API's sport keys to ScoreLock's API-Football IDs (8 leagues). Market constants: `MARKET_H2H`, `MARKET_TOTALS`, `MARKET_SPREADS`. `extract_best_odds()` static scans bookmakers across an event for highest price per outcome (home / draw / away / over 2.5 / under 2.5, with bookmaker names). `match_event_to_fixture()` static uses fuzzy team-name matching (substring check, case-insensitive) to link an Odds API event to a DB fixture. Singleton `odds_api`.
- **Coupling risk**: (1) Identifies leagues by `api_football_id` — odds provider coupled to sports-data provider's identity. (2) Fuzzy name matching (`match_event_to_fixture`) will silently misattribute odds when two teams have overlapping names (e.g. Manchester United / Manchester City). This is latent data-integrity risk once we scale beyond PL. (3) `extract_best_odds` hardcodes the 2.5 over/under line — no support for 1.5, 3.5, BTTS, Asian handicap. (4) Second `QuotaExhaustedError` class definition — diverges from `football_data.py`'s.
- **Reusable parts**: Quota integration, best-odds extraction algorithm concept, decimal odds format.
- **Must not change yet**: Everything.

### `backend/app/services/tasks.py` (1174 lines)

- **Current responsibility**: Celery task definitions. 16 scheduled beat tasks plus ad-hoc tasks (from v0.2 intake). Provider singletons + module-level catalogues imported directly — re-verified in v0.4: `from app.services.api_football import LEAGUE_IDS, PHASE_1_LEAGUES` at line 81 (inside `fetch_daily_fixtures` defined at line 64) and again at line 573 (inside `update_standings` defined at line 560). `fetch_daily_fixtures`, `update_standings`, `run_daily_predictions` (line 369), `update_live_scores` all call provider clients directly, not through any abstraction. Known long functions: `fetch_odds_updates` ~135 LOC, `run_daily_predictions` ~113 LOC, `fetch_daily_fixtures` ~102 LOC, `update_live_scores` ~65 LOC.
- **Coupling risk**: Tasks are the primary consumer of the current coupled design. They import provider singletons directly; any provider swap requires editing every task.
- **Reusable parts**: Task structure, Celery beat schedule, quota logging.
- **Must not change yet**: Everything. Tasks get rewired to the registry in v0.5d.

### `backend/app/models/models.py` (438 lines)

- **Current responsibility**: SQLAlchemy 2.x ORM definitions. 13 tables verified in live DB per prior intake: `users, leagues, teams, fixtures, predictions, odds, standings, sentiment_scores, articles, affiliate_links, affiliate_clicks, prediction_views, user_predictions`. Enums include `MatchStatus`, `SubscriptionTier`, `ArticleType`. Columns named after API-Football concepts where relevant (e.g. `teams.api_football_id`).
- **Coupling risk**: Column naming (`api_football_id` on teams/leagues/fixtures) embeds provider identity directly in the canonical schema. Need to preserve these for backward compat but add neutral `external_ids` mapping as the go-forward path.
- **Reusable parts**: Enum definitions, relationship graph, index choices.
- **Must not change yet**: Everything. v0.5b/c add new tables; existing schema untouched in v0.4.

### `backend/app/api/routes.py` (1169 lines)

- **Current responsibility**: FastAPI route handlers. 37 endpoints (per v0.2 intake) across fixtures, predictions, value-bets, H2H, standings, sentiment, articles, affiliate, tipping, admin, stripe, websocket. `ADMIN_EMAILS` set at line 510; admin guards verified at lines 516/811 (`Depends(get_current_user)` + 403 on miss).
- **Coupling risk**: Routes serve responses shaped around the current schema. Adding new entities (players, lineups, events, statistics, broadcasts) will require new handlers but not rewrites of existing ones.
- **Reusable parts**: Auth guards, pagination patterns, Pydantic schema dependency.
- **Must not change yet**: Everything. New endpoints arrive in v0.6.

### `backend/app/core/config.py` (73 lines)

- **Current responsibility**: `pydantic-settings` `Settings` class grouping 30+ env vars: app/CORS/DB/Redis/Celery/Auth/External APIs (API-Football, football-data, Odds API)/Stripe/Anthropic/Sentry/Twitter/Discord/Telegram/OneSignal. `@lru_cache` on `get_settings()`.
- **Coupling risk**: (1) Three provider keys exist as first-class fields (`api_football_key`, `football_data_key`, `the_odds_api_key`) — adding SportMonks / broadcast provider / weather provider requires touching this file. Acceptable cost of explicit config. (2) `secret_key: str = "change-me"` default is a standing security concern (flagged in prior intake). Not fixed here (out of scope), tracked.
- **Reusable parts**: The `pydantic-settings` pattern is sound. Extend with new provider key fields as providers land in v0.5d.
- **Must not change yet**: Everything. New provider fields added in v0.5a when the first new provider onboards.

### `.env.example` (committed)

- **Current responsibility**: Template listing 36 env-var assignments — re-verified in v0.4 via `grep -cE "^[A-Z0-9_]+=" .env.example` = 36. Known gap: backend code references Twitter/Telegram/Discord/OneSignal + RAILWAY/CLOUDFLARE/SENTRY-extra vars via `config.py` — of those, Twitter/Telegram/Discord/OneSignal are absent from `.env.example`, while Cloudflare/Railway/Sentry-extras are present in `.env.example` but not in `config.py` (asymmetric drift, not fixed here).
- **Coupling risk**: Docs drift. Fixed by v0.5a extending `.env.example` alongside `config.py`.
- **Reusable parts**: Structure.
- **Must not change yet**: Everything.

## Design Goals

Explicit, testable goals for the abstraction:

1. **Provider-neutral backend.** No file outside `backend/app/providers/` imports from a concrete provider client. Tasks, routes, services, and the AI pipeline depend only on the abstract interfaces and normalized domain objects.
2. **Normalized internal schema.** Every provider response is transformed into one of the `Normalized*` domain objects defined below before leaving the provider layer. The canonical DB schema reflects those objects, not any provider's response shape.
3. **Raw payload retention.** Every provider response is persisted in `provider_payloads` (JSONB) before normalization. Normalization is a pure function of the raw payload, repeatable at any time.
4. **Operation-scoped fallback chain.** Fallback order is defined per `(operation, scope)` tuple — where scope may be `league_id`, `country`, or `global`. No global "Provider A → Provider B" list.
5. **Quota and rate-limit governance.** All providers share `core/quota_manager.py`. Per-provider per-window counters. Hard cap at 90% of published limit. When near cap, registry degrades to next provider rather than throttling in place.
6. **Stale data detection.** Every normalized row stamped with `fetched_at` and `provider`. Live-fixture refresh scans for stale records and triggers provider calls. Stale threshold is operation-specific (live scores: 15s; standings: 30min; fixtures window: 12h).
7. **Provider health monitoring.** Circuit breaker per `(provider, operation)`: N consecutive failures within M seconds → open circuit → skip to next provider → half-open retry after cooldown. State in Redis + exported Prometheus counter.
8. **Testable mock provider.** `MockSportsDataProvider` reads canned JSON fixtures. Full local stack runs without any paid keys. CI runs without paid keys. Mock provider is the default in `ENVIRONMENT=test`.
9. **No provider-specific logic in frontend.** The frontend calls ScoreLock's own API only. Provider choice, fallback behavior, quota state are never visible in the response shape. No provider names, no raw payloads, no provider-specific enum values ever cross the API boundary.
10. **No provider payload in AI prompts without normalization.** Claude prompts consume normalized domain objects only. Raw JSON never gets concatenated into an LLM prompt.

## Provider Interface Contract

Python-style pseudocode. Signatures, not implementations. Protocol-typed (PEP 544) so concrete clients are duck-typed, not subclassing.

### `SportsDataProvider`

```python
class SportsDataProvider(Protocol):
    name: str                       # "sportmonks" | "api_football" | "football_data" | "mock"
    supports: frozenset[Operation]  # subset of the full operation set; see registry

    async def fetch_fixtures(
        self,
        league_external_id: str,
        season: int,
        window: DateRange | None = None,
    ) -> list[NormalizedFixture]: ...
    # Raises: ProviderUnavailable, ProviderQuotaExhausted, ProviderAuthError, ProviderPayloadError

    async def fetch_fixture_detail(
        self,
        fixture_external_id: str,
    ) -> NormalizedFixture: ...
    # Includes embedded NormalizedVenue / NormalizedReferee where the provider supplies them.

    async def fetch_live_fixtures(
        self,
        scope: Scope | None = None,   # filter by league / country / global
    ) -> list[NormalizedFixture]: ...

    async def fetch_standings(
        self,
        league_external_id: str,
        season: int,
    ) -> list[NormalizedStanding]: ...

    async def fetch_teams(
        self,
        league_external_id: str,
        season: int,
    ) -> list[NormalizedTeam]: ...

    async def fetch_players(
        self,
        team_external_id: str,
    ) -> list[NormalizedPlayer]: ...

    async def fetch_lineup(
        self,
        fixture_external_id: str,
    ) -> NormalizedLineup: ...
    # Two states: projected (before kickoff) and confirmed (at kickoff).
    # The returned object carries `confirmed_at: datetime | None`.

    async def fetch_events(
        self,
        fixture_external_id: str,
    ) -> list[NormalizedMatchEvent]: ...

    async def fetch_statistics(
        self,
        fixture_external_id: str,
    ) -> NormalizedMatchStatistics: ...

    async def stream_live(
        self,
        scope: Scope | None = None,
    ) -> AsyncIterator[LiveEventEnvelope]: ...
    # Optional. Providers without push raise NotImplementedError; registry uses polling fallback.

    async def health(self) -> ProviderHealth: ...
    # Must never raise. Returns status, latency sample, last error, quota remaining.
```

**Error model (shared by all interfaces)**:
```python
class ProviderError(Exception): ...
class ProviderUnavailable(ProviderError): ...        # network, 5xx, timeout
class ProviderQuotaExhausted(ProviderError): ...     # 429, quota header depletion
class ProviderAuthError(ProviderError): ...          # 401, 403
class ProviderPayloadError(ProviderError): ...       # schema drift, normalization failed
class ProviderUnsupported(ProviderError): ...        # operation outside provider.supports
```

**Retry semantics**: `ProviderUnavailable` retried by the client wrapper with exponential backoff (0.5s → 8s, max 5 attempts, jittered). `ProviderQuotaExhausted` is **not** retried — it triggers registry fallback. `ProviderAuthError` and `ProviderPayloadError` are **not** retried — they surface immediately and open the circuit breaker.

**Cache semantics**: Provider-level caching is explicit. Read-only `GET` operations may be wrapped by a Redis read-through cache keyed by `(provider, operation, args_hash)`. TTLs are operation-specific (see Design Goals #6). Write/ingest paths never touch cache.

**Expected normalized output**: Every method returns a `Normalized*` object or list. See Normalized Domain Objects below.

### `OddsProvider`

```python
class OddsProvider(Protocol):
    name: str
    supports: frozenset[OddsMarket]   # H2H | TOTALS | SPREADS | BTTS | CORRECT_SCORE | NEXT_GOAL | ...

    async def fetch_odds(
        self,
        fixture_external_ids: list[str],
        markets: list[OddsMarket],
        regions: list[Region] | None = None,
    ) -> list[NormalizedOddsSnapshot]: ...

    async def fetch_in_play_odds(
        self,
        fixture_external_id: str,
        markets: list[OddsMarket],
    ) -> list[NormalizedOddsSnapshot]: ...
    # Providers without in-play raise ProviderUnsupported; registry does not poll.

    async def fetch_bookmakers(
        self,
        regions: list[Region] | None = None,
    ) -> list[NormalizedBookmaker]: ...

    async def health(self) -> ProviderHealth: ...
```

**Retry + cache**: Same error taxonomy. In-play odds are never cached (snapshots are themselves the cache).

### `BroadcastProvider`

```python
class BroadcastProvider(Protocol):
    name: str
    supported_countries: frozenset[CountryCode]

    async def fetch_broadcasts(
        self,
        fixture_external_id: str,
        countries: list[CountryCode] | None = None,
    ) -> list[NormalizedBroadcast]: ...
    # Returns one row per (country, channel|streaming) combination.

    async def health(self) -> ProviderHealth: ...
```

**Sources to consider at implementation time** (not decided in v0.4): SportMonks broadcast add-on, FotMob-equivalent via Stats Perform partnership, Screenhits (Nordic-specialist), or manual curation for Sweden (Viaplay / TV4 / C More).

### `WeatherProvider`

```python
class WeatherProvider(Protocol):
    name: str

    async def fetch_weather(
        self,
        venue: NormalizedVenue,
        at: datetime,
    ) -> NormalizedWeatherSnapshot: ...
    # `at` ≤ now: historical/observed. `at` > now: forecast.
    # Providers may return forecasts with degraded confidence; Normalized object carries `is_forecast` flag.

    async def health(self) -> ProviderHealth: ...
```

**Candidates**: OpenWeatherMap, Meteostat (historical), Open-Meteo (free, generous).

## Normalized Domain Objects

All `Normalized*` objects are Pydantic v2 models. Fields below are conceptual; final attribute names are decided at v0.5c schema time. Every object carries, in addition to the fields listed:

- `provider: str` — source provider at fetch time (does not survive merges).
- `fetched_at: datetime` — UTC timestamp of normalization.
- `external_ids: dict[str, str]` — per-provider IDs (populated on merge; see mapping table).

---

### `NormalizedSport`
- **Required**: `code` (e.g. `"football"`), `display_name`.
- **Optional**: `icon_ref`.
- **Mapping concern**: Every provider must map to ScoreLock's canonical sport code. Football-first; multi-sport deferred to PL3 per ROADMAP.

### `NormalizedCountry`
- **Required**: `iso_2` (ISO 3166-1 alpha-2), `iso_3`, `display_name`.
- **Optional**: `flag_ref`.
- **Mapping concern**: Providers disagree on naming ("England" vs "United Kingdom" vs "GB-ENG"). Normalize to FIFA-style entity codes where possible; fall back to ISO.

### `NormalizedCompetition`
- **Required**: `code` (ScoreLock slug), `display_name`, `country_iso_2`, `competition_type` (`league|cup|international`), `sport_code`.
- **Optional**: `logo_ref`, `tier` (e.g. `1` for top flight), `gender` (`m|w`), `age_group` (`senior|u21|u19`).
- **Mapping concern**: Tier + country pair is the natural identity; external IDs vary wildly. Expect to retain the current `leagues.api_football_id` column for backward compat and add neutral mapping via `provider_entity_ids`.

### `NormalizedSeason`
- **Required**: `competition_code`, `year_start` (int), `label` (e.g. `"2025/26"`), `start_date`, `end_date`.
- **Optional**: `is_current`.
- **Mapping concern**: Some providers label seasons by end year (2026), some by start (2025). Always store start year.

### `NormalizedTeam`
- **Required**: `canonical_name`, `short_name`, `country_iso_2`, `sport_code`.
- **Optional**: `logo_ref`, `colors` (primary / secondary hex), `founded_year`, `venue_external_id`, `market_value_eur`.
- **Mapping concern**: Name variants are the primary pain (Nottingham Forest / Nottm Forest / Forest). Canonical name is chosen at ingest and does not change without manual override. `provider_entity_ids` records every variant the provider returned.

### `NormalizedPlayer`
- **Required**: `canonical_name`, `nationality_iso_2`, `position_code` (`GK|DEF|MID|FWD`).
- **Optional**: `date_of_birth`, `height_cm`, `weight_kg`, `preferred_foot`, `market_value_eur`, `photo_ref`, `current_team_external_id`.
- **Mapping concern**: Many players move teams within a season. The current-team relationship is transient; the canonical identity is the player. Store team history separately (not in v0.4 scope).

### `NormalizedFixture`
- **Required**: `competition_code`, `season_year_start`, `round_label`, `round_number` (nullable), `home_team_external_id`, `away_team_external_id`, `kickoff_utc`, `status_code` (`SCHEDULED|IN_PLAY|HALF_TIME|FULL_TIME|POSTPONED|CANCELLED|SUSPENDED|AWARDED`), `home_score`, `away_score`.
- **Optional**: `home_score_halftime`, `away_score_halftime`, `venue_external_id`, `referee_external_id`, `live_minute`, `live_stoppage`, `attendance`, `postponed_from`.
- **Mapping concern**: Status vocabularies vary (see `football_data.py` line 220–230 `status_map`). Map to the canonical enum; retain raw provider status in the raw payload for debugging.

### `NormalizedLineup`
- **Required**: `fixture_external_id`, `team_external_id`, `formation_code` (e.g. `"4-3-3"`), `state` (`PROJECTED|CONFIRMED`).
- **Optional**: `confirmed_at`, `manager_name`.
- **Mapping concern**: Projected lineups are mutable until kickoff; `state` transitions track this. Confirmed lineup supersedes projected.

### `NormalizedLineupPlayer`
- **Required**: `lineup_external_id`, `player_external_id`, `position_code`, `shirt_number`, `is_starter`, `grid_x` (0–5), `grid_y` (0–3), `is_captain`.
- **Optional**: `provider_rating_value`, `provider_rating_source` (`"opta"` | `"sportmonks"` | `"api_football"`), `minutes_played`.
- **Mapping concern**: Grid positions are provider-normalized. If a provider only gives `position_code`, derive grid from formation template. Never invent a rating.

### `NormalizedMatchEvent`
- **Required**: `fixture_external_id`, `minute`, `stoppage` (nullable int), `event_type` (`GOAL|OWN_GOAL|PENALTY_GOAL|MISSED_PENALTY|YELLOW_CARD|RED_CARD|SECOND_YELLOW|SUBSTITUTION|VAR_GOAL_AWARDED|VAR_GOAL_CANCELLED|VAR_PENALTY_AWARDED|VAR_PENALTY_OVERTURNED|VAR_RED_CARD`), `team_external_id`.
- **Optional**: `player_in_external_id` (subs), `player_out_external_id` (subs), `primary_player_external_id` (scorer / booked player / VAR subject), `assist_player_external_id`, `description`, `video_clip_ref`.
- **Mapping concern**: SofaScore exposes VAR decisions; API-Football does not distinguish all VAR variants. Providers that don't model VAR return only `GOAL` / `OWN_GOAL` / etc.; the `VAR_*` events only populate when the provider supports them.

### `NormalizedMatchStatistics`
- **Required**: `fixture_external_id`, one sub-record per team with: `team_external_id`, `possession_pct`, `shots_total`, `shots_on_target`, `shots_off_target`, `corners`, `fouls`, `yellow_cards_count`, `red_cards_count`, `offsides`.
- **Optional per team**: `xg`, `passes_total`, `passes_accurate`, `pass_accuracy_pct`, `ball_in_play_seconds`, `tackles`, `blocks`, `clearances`, `big_chances_created`, `big_chances_missed`.
- **Mapping concern**: xG is not universal; when missing, `xg = None`. Possession should sum to 100 ± 1; provider drift beyond that threshold logs a conflict.

### `NormalizedStanding`
- **Required**: `competition_code`, `season_year_start`, `team_external_id`, `position`, `played`, `wins`, `draws`, `losses`, `goals_for`, `goals_against`, `goal_difference`, `points`.
- **Optional**: `form_string` (e.g. `"WWDLW"`), `home_played`, `home_wins`, etc. (home/away splits), `zone` (`CL|EL|UECL|RELEGATION|NONE`).
- **Mapping concern**: Some providers surface home/away splits separately; others return aggregated. Zone is derived from position + competition rules, not provider data.

### `NormalizedOddsSnapshot`
- **Required**: `fixture_external_id`, `bookmaker_external_id`, `market_code` (`H2H|TOTALS|SPREADS|BTTS|CORRECT_SCORE|NEXT_GOAL|...`), `taken_at`, `outcomes` (list of `{selection_code, value_numeric, price_decimal}`).
- **Optional**: `is_in_play`, `suspended`, `market_line` (e.g. `2.5` for totals), `region`.
- **Mapping concern**: Decimal odds only. American / fractional conversion happens at the provider edge. Outcomes are identified by `selection_code` (`HOME|DRAW|AWAY|OVER|UNDER|YES|NO|1-0|0-1|...`), not provider-specific labels.

### `NormalizedBroadcast`
- **Required**: `fixture_external_id`, `country_iso_2`, `provider_type` (`TV|STREAMING|RADIO`), `channel_name` (or streaming service name).
- **Optional**: `watch_url`, `affiliate_partner`, `requires_subscription`, `language_iso_2`, `logo_ref`.
- **Mapping concern**: Rights are region-specific. The same fixture has different broadcasts in SE vs UK vs DE. Store per (fixture, country).

### `NormalizedVenue`
- **Required**: `canonical_name`, `country_iso_2`, `city`.
- **Optional**: `capacity`, `surface` (`grass|artificial|hybrid`), `latitude`, `longitude`, `address`, `opened_year`.
- **Mapping concern**: Name-variant matching. "Stadium of Light" exists in Sunderland and Lisbon — geographic disambiguation required.

### `NormalizedReferee`
- **Required**: `canonical_name`, `nationality_iso_2`.
- **Optional**: `career_games_count`, `career_yellows_per_game`, `career_reds_per_game`, `career_penalties_per_game`.
- **Mapping concern**: Aggregated stats are provider-computed or derived; always label the source.

### `NormalizedWeatherSnapshot`
- **Required**: `venue_external_id`, `observed_at`, `temperature_c`, `conditions_code` (`clear|clouds|rain|snow|storm|fog`), `is_forecast`.
- **Optional**: `wind_speed_mps`, `wind_direction_deg`, `humidity_pct`, `precipitation_mm`, `pressure_hpa`, `uv_index`, `icon_ref`.
- **Mapping concern**: Historical providers (Meteostat) may lack some fields; forecast providers (Open-Meteo) have all. `is_forecast` drives UI copy ("Forecast: …" vs "Conditions: …").

## Provider Registry and Fallback Rules

Registry resolves an `(operation, scope)` tuple to a provider chain. Scope may be `league_code`, `country_iso_2`, or `global`.

**Operation enum** (authoritative list):

```python
class Operation(str, Enum):
    FIXTURES = "fixtures"
    LIVE_FIXTURES = "live_fixtures"
    STANDINGS = "standings"
    TEAMS = "teams"
    PLAYERS = "players"
    LINEUPS = "lineups"
    EVENTS = "events"
    STATISTICS = "statistics"
    ODDS = "odds"
    IN_PLAY_ODDS = "in_play_odds"
    BROADCASTS = "broadcasts"
    WEATHER = "weather"
```

**Resolution example** (illustrative, final values set at v0.5d):

```python
REGISTRY: dict[Operation, list[ProviderRule]] = {
    Operation.FIXTURES: [
        ProviderRule(provider="sportmonks", scope="global"),
        ProviderRule(provider="api_football", scope="global"),
        ProviderRule(provider="football_data", scope="league_in:[PL,PD,SA,BL1,FL1,CL]"),
    ],
    Operation.LIVE_FIXTURES: [
        ProviderRule(provider="sportmonks", scope="global", prefer_push=True),
        ProviderRule(provider="api_football", scope="global"),
    ],
    Operation.LINEUPS: [
        ProviderRule(provider="sportmonks", scope="global"),
        ProviderRule(provider="api_football", scope="global"),
    ],
    Operation.EVENTS: [
        ProviderRule(provider="sportmonks", scope="global"),
        ProviderRule(provider="api_football", scope="global"),
    ],
    Operation.STATISTICS: [
        ProviderRule(provider="sportmonks", scope="global"),
        ProviderRule(provider="api_football", scope="global"),
    ],
    Operation.STANDINGS: [
        ProviderRule(provider="sportmonks", scope="global"),
        ProviderRule(provider="football_data", scope="league_in:[PL,PD,SA,BL1,FL1,CL]"),
        ProviderRule(provider="api_football", scope="global"),
    ],
    Operation.ODDS: [
        ProviderRule(provider="the_odds_api", scope="global"),
    ],
    Operation.IN_PLAY_ODDS: [
        ProviderRule(provider="the_odds_api", scope="global", requires_tier="paid_inplay"),
    ],
    Operation.BROADCASTS: [
        ProviderRule(provider="<tbd>", scope="country_iso:SE"),
        ProviderRule(provider="sportmonks", scope="global"),  # if broadcast add-on present
    ],
    Operation.WEATHER: [
        ProviderRule(provider="open_meteo", scope="global"),
    ],
    Operation.TEAMS: [
        ProviderRule(provider="sportmonks", scope="global"),
        ProviderRule(provider="api_football", scope="global"),
        ProviderRule(provider="football_data", scope="league_in:[PL,PD,SA,BL1,FL1,CL]"),
    ],
    Operation.PLAYERS: [
        ProviderRule(provider="sportmonks", scope="global"),
        ProviderRule(provider="api_football", scope="global"),
    ],
}
```

**No-provider behavior**: If no rule matches scope (e.g. `Operation.LIVE_FIXTURES` for a league no registered provider covers), raise `ProviderUnsupported`. The caller (usually a Celery task) logs and skips. Does not crash the app.

**Conflict resolution**: If two providers return divergent values for the same canonical entity/field within the same refresh window:
1. Provider priority (order in the rule list) wins by default.
2. Divergence is logged to `provider_conflicts` (new table in v0.5b) with both values + timestamps.
3. Field-specific overrides allowed: e.g. "trust SportMonks for xG, trust API-Football for final score" — configured in a `FIELD_PRIORITIES` dict, not hardcoded per call site.
4. Manual override via admin endpoint: operator can mark a field value as authoritative, which suppresses further provider updates until cleared.

**Stale data handling**: Each normalized row carries `fetched_at` + `provider`. A Celery Beat task (`refresh_stale_*`) runs per operation class:
- Live fixtures: scan every 30s for `IN_PLAY` records with `fetched_at < now - 15s`, trigger refresh.
- Standings: scan every 10min for records with `fetched_at < now - 30min` in active leagues.
- Fixtures window: scan every 1h for records with `kickoff < now + 14d` and `fetched_at < now - 12h`.

**Circuit breaker**: Per `(provider, operation)` tuple, state in Redis key `cb:{provider}:{operation}`:
- Consecutive failure threshold: 5 failures within 60s → open.
- Open cooldown: 5 minutes.
- Half-open: allow one trial call; success closes the circuit, failure returns to open with extended cooldown (exponential, capped at 60 min).
- Open circuit → registry skips to next rule. No retry on the open provider within cooldown.
- Exported metric: `provider_circuit_state{provider,operation}` for Grafana/Prometheus.

## Raw Payload and External ID Strategy

### `provider_payloads` table (new in v0.5b)

Columns:
- `id` (bigserial, PK)
- `provider` (text, indexed)
- `operation` (text, indexed)
- `scope` (text, nullable, indexed) — e.g. league code or fixture external_id
- `external_id` (text, nullable) — primary external entity referenced
- `request_params` (JSONB) — HTTP query params or GraphQL variables
- `response_status` (int)
- `response_headers` (JSONB)
- `payload` (JSONB)
- `fetched_at` (timestamptz, indexed)
- `normalized_at` (timestamptz, nullable)
- `normalization_version` (int, nullable)

Primary-key composite index: `(provider, operation, fetched_at DESC)` for replay queries. Secondary index on `(external_id, fetched_at DESC)` for per-entity history.

### `provider_entity_ids` (mapping table, new in v0.5b)

Columns:
- `entity_type` (text) — `team|player|league|fixture|venue|referee|bookmaker`
- `canonical_id` (bigint) — FK to the canonical row in the relevant table
- `provider` (text)
- `external_id` (text)
- `first_seen_at`, `last_seen_at` (timestamptz)

Primary key: `(entity_type, provider, external_id)`.
Secondary index: `(entity_type, canonical_id)` for reverse lookup.

### `external_ids JSONB` on canonical rows vs separate table — decision

**Decision: separate `provider_entity_ids` table.**

Rationale:
- JSONB on every canonical row works for lookups "what's team X's SportMonks ID?" (easy) but fails for the reverse: "what team has SportMonks ID 5247?" That reverse is the ingest path's primary query. A JSONB GIN index works but is less efficient and less introspectable than a normal B-tree on `(provider, external_id)`.
- Audit trail: `first_seen_at`/`last_seen_at` per mapping is valuable during provider drift investigations.
- Decoupling: adding a new provider adds rows, not columns. JSONB path would require no schema change but would lose the per-provider query ergonomics.

Downside accepted: one additional join at read time in some queries. Mitigated by caching team/league/venue mappings in application memory (they're small and near-static).

### Payload retention policy

- Live match payloads (events, statistics, live fixtures): retained 30 days, then pruned.
- Pre/post-match payloads (lineups, confirmed fixtures): retained 180 days.
- Schema-rare payloads (teams, players, leagues, standings): retained indefinitely (small volume, high replay value).
- TimescaleDB retention policies applied on `fetched_at` partitions where the table is hypertabled.
- `provider_entity_ids` never pruned.

### Replay / debug strategy

- Re-running normalization against stored payloads: `python -m app.providers._normalize --from-payload <payload_id>` (to be implemented in v0.5a). Idempotent; overwrites canonical row if output differs.
- Cross-provider diff: given a fixture canonical_id, list all payloads across providers, print normalized diff. For debugging conflicts.
- Schema-drift detection: when `ProviderPayloadError` fires during normalization, the offending payload is retained with a flag; daily report lists new drift cases for review.

### Privacy / security concerns for payloads

- Provider response headers may contain cookies, session IDs, or quota tokens. Only whitelisted headers persisted to `response_headers` JSONB (provider-specific allowlist, defaults: `content-type`, `date`, `x-ratelimit-*`, `x-requests-*`). All other headers dropped at capture time.
- No user-identifying data is expected in provider payloads (they're sports-data endpoints), but payload bodies are scanned for obvious PII patterns at ingest (email, phone regex); hits log a warning and skip persistence.
- `provider_payloads` is not exposed via any public API endpoint. Admin-only access via `/admin/providers/payloads/{id}` behind the `ADMIN_EMAILS` allowlist (pattern already in place per `backend/app/api/routes.py:510`).
- Provider API keys never logged, never persisted. Request bodies persisted redacted.
- Retention-policy deletions are hard deletes (not soft) to minimize stale-data liability.

## Rate Limits, Quotas, Retries

### Redis counters

`core/quota_manager.py` already exists (verified in `football_data.py` and `odds_api.py` usage). Extended in v0.5a to include per-provider metadata:

```python
class QuotaBucket:
    provider: str
    window: str          # "per_minute" | "per_day" | "per_month"
    limit: int
    soft_cap_pct: int    # default 90
    cost_weight: dict[Operation, int]   # override per-op cost (default 1)
```

Redis keys: `quota:{provider}:{window}:{bucket_start_ts}`. Incremented atomically via `INCRBY`. Soft cap triggers registry-level degradation, not throttle.

### Per-provider limits (published tiers at time of writing)

| Provider | Free tier | Paid tier expected |
|---|---|---|
| API-Football | 100 req/day, 10 req/min | $19/mo Dev 7 500/day, 30/min · $29/mo Ultra 75 000/day, 450/min |
| football-data.org | 10 req/min, 10 comp | £14/mo Tier One 10/min 10 comps |
| SportMonks | 180 req/min (football) | Plan-dependent; Advanced targets 3 000/min |
| The Odds API | 500 req/mo | $30 30k/mo · $99 1M/mo with in-play |
| Open-Meteo | 10 000 req/day | Free tier sufficient |

Values confirmed at v0.5a when the provider key is actually provisioned. The quota manager consumes these from config, not from hardcoded constants.

### Per-operation cost weight

Not every operation is a single HTTP call. Default weight = 1. Overrides:

| Operation | Default weight | Rationale |
|---|---|---|
| FIXTURES (bulk) | 1 | One call per league/season |
| LIVE_FIXTURES | 1 | One call, can return many fixtures |
| LINEUPS | 1 per fixture | Called per fixture |
| EVENTS | 1 per fixture | Called per fixture |
| STATISTICS | 1 per fixture | Called per fixture |
| IN_PLAY_ODDS | 2 | Higher cost, stricter budget |
| STREAM_LIVE | 0 | WebSocket/SSE — not counted per message |

### Backoff

- Exponential, jittered: base 0.5s, factor 2, max 8s, max attempts 5. Aligns with existing `@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))` in current clients; v0.5a upgrades these to a shared retry policy in `providers/_retry.py`.
- Non-retryable errors (`ProviderAuthError`, `ProviderPayloadError`, `ProviderQuotaExhausted`) bypass retry.

### Fail-open vs fail-closed

**Per operation class**:
- **Read-heavy discovery operations** (fixtures, standings, teams, players): fail-open. Missing data is degraded UX; crashing is worse. Return whatever was last persisted and log the miss.
- **Write/ingest tasks** (Celery sync tasks): fail-closed. A failed sync task must raise so Celery retries it and so failures are visible in monitoring.
- **Live operations** (live_fixtures, in_play_odds): fail-open. Return last known snapshot; UI shows a `last updated` timestamp.
- **Critical path operations** (not currently any — future billing/transactional): fail-closed.

### Observability metrics

Prometheus counters/histograms (to be added in v0.5a):

- `provider_requests_total{provider,operation,status}` — counter.
- `provider_request_duration_seconds{provider,operation}` — histogram.
- `provider_quota_remaining{provider,window}` — gauge.
- `provider_circuit_state{provider,operation}` — gauge (0=closed, 1=half_open, 2=open).
- `provider_fallback_total{from_provider,to_provider,operation,reason}` — counter.
- `provider_normalization_errors_total{provider,operation,error_type}` — counter.
- `provider_conflicts_total{field,winner,loser}` — counter.

### Admin / provider health surface

New admin endpoints in v0.6 (out of v0.4 scope, design only):

- `GET /admin/providers/health` — per-provider state, latency, last error, quota remaining.
- `GET /admin/providers/quota` — quota buckets with forecast to exhaustion.
- `GET /admin/providers/conflicts` — recent field conflicts for review.
- `POST /admin/providers/{name}/circuit/reset` — manual circuit close.
- `POST /admin/providers/payloads/{id}/replay-normalize` — re-normalize a single payload.

All behind existing `ADMIN_EMAILS` allowlist (`backend/app/api/routes.py:510`).

## Migration Strategy

Sequenced after v0.4 (design). Each version is small, shippable, and reversible.

### v0.5a — Abstraction skeleton, no runtime behavior change

- **Goal**: Create `backend/app/providers/` with `base.py` (Protocol definitions, error classes), `_registry.py` (empty registry + `get_provider(op, scope)` helper), `_normalize.py` (stub), `_retry.py` (shared `tenacity`-based retry policy), `_rate_limit.py` (thin wrapper around existing `core/quota_manager.py`). No concrete providers wired yet. Zero runtime change.
- **Files likely touched**: new files under `backend/app/providers/`. No `config.py` change in v0.5a. The abstraction skeleton must be importable but unused by runtime code.
- **Migration required**: no.
- **Risk**: low — imports only, no callers yet.
- **Validation commands**: `docker exec scorelock-api python -c "from app.providers.base import SportsDataProvider, OddsProvider, BroadcastProvider, WeatherProvider; print('OK')"`; `make dev-install && make lint && make test`.

### v0.5b — Raw payload + mapping tables

- **Goal**: Alembic migration introducing `provider_payloads`, `provider_entity_ids`, `provider_conflicts` tables. No writers yet. Down-migration verified.
- **Files likely touched**: `backend/migrations/versions/<n>_add_provider_tables.py` (new), `backend/app/models/models.py` (extended with new models).
- **Migration required**: yes.
- **Risk**: low-medium — additive schema, no data change to existing tables.
- **Validation commands**: `docker compose exec backend alembic upgrade head`; `docker exec scorelock-db psql -U scorelock -d scorelock -c "\dt provider*"` expects 3 tables; `docker compose exec backend alembic downgrade -1` then `alembic upgrade head` to verify reversibility.

### v0.5c — Metadata schema

- **Goal**: Alembic migrations for `players`, `lineups`, `lineup_players`, `match_events`, `match_statistics`, `venues`, `referees`, `broadcasts`, `weather_snapshots`, plus `external_ids` pointer columns where canonical rows benefit from fast JSON checks. Seeded mock data for local dev.
- **Files likely touched**: `backend/migrations/versions/<n>_add_match_detail_metadata.py` (new), `backend/app/models/models.py` (extended).
- **Migration required**: yes — largest schema change in project history.
- **Risk**: medium — rolls up to v0.5b. Migration rehearsed locally + on a DB dump before any remote apply.
- **Validation commands**: same shape as v0.5b. Plus a new `seeds/` loader script that inserts deterministic mock rows for test.

### v0.5d — Wrap existing providers behind interfaces

- **Goal**: Existing `backend/app/services/{api_football,football_data,odds_api}.py` become thin call sites; the real logic moves to `backend/app/providers/api_football.py` / `football_data.py` / `the_odds_api.py` implementing the interfaces. Registry populated. Normalizers rewritten to produce `Normalized*` objects (not API-Football-shaped dicts). Tasks in `backend/app/services/tasks.py` rewired to call via the registry.
- **Files likely touched**: `backend/app/providers/*.py` (new + moved logic), `backend/app/services/{api_football,football_data,odds_api}.py` (slim re-export or deletion), `backend/app/services/tasks.py` (call sites rewritten).
- **Migration required**: no (schema unchanged; this version writes to new tables via the abstraction).
- **Risk**: medium-high — it's the switch. Coverage: run all existing tasks locally against mock provider; then against real provider keys in a dev project; diff old vs new DB state.
- **Validation commands**: `make test`; full Celery beat run in dev with `ENVIRONMENT=test` forcing mock provider; `docker compose logs celery-worker` free of `ERROR`.

### v0.5e — Mock provider and tests

- **Goal**: `MockSportsDataProvider`, `MockOddsProvider`, `MockBroadcastProvider`, `MockWeatherProvider` implementations backed by canned JSON fixtures at `backend/tests/fixtures/providers/<name>/*.json`. CI runs full test suite against mocks (no paid keys required). Contract tests verify each real provider adapter produces `Normalized*` objects shape-matching the Pydantic models.
- **Files likely touched**: `backend/app/providers/mock*.py` (new), `backend/tests/fixtures/providers/` (new directory), `backend/tests/test_providers/*.py` (new tests).
- **Migration required**: no.
- **Risk**: low.
- **Validation commands**: `make test` (passes with 0 real keys set); `docker compose run --rm backend pytest backend/tests/test_providers -v`.

### v0.6 — Match detail API expansion

- **Goal**: Per the v0.3 roadmap. New read-only endpoints for lineups, events, statistics, broadcasts, weather, standings-projection. All served from the tables added in v0.5c, populated via providers registered in v0.5d.
- **Files likely touched**: `backend/app/api/routes.py` (new handlers), `backend/app/schemas/schemas.py` (new Pydantic response models), `backend/app/services/db_service.py` (read helpers).
- **Migration required**: no.
- **Risk**: low — additive.
- **Validation commands**: `curl -s http://localhost:8000/api/v1/fixtures/1/events | python -m json.tool`; `make test`.

## Testing Strategy

### Unit tests

- **Per normalizer**: given a canned provider payload (fixture file), the normalizer emits a `Normalized*` object matching a golden expectation. One test per provider per operation per edge case.
- **Per Protocol compliance**: every concrete provider class is instance-checked against its Protocol at import time (`assert isinstance(SportMonksProvider(), SportsDataProvider)`). Guards against missing methods.
- **Per error path**: each error class raised from a provider translates to the correct `ProviderError` subclass; unit tests simulate 401/403/429/5xx/timeout/schema-drift.

### Contract tests

- **Schema drift detection**: `backend/tests/contracts/test_provider_payloads.py` loads live response samples (captured manually and committed to `tests/fixtures/providers/<name>/`) and asserts the normalizer handles them cleanly. New payload shapes trigger a failing contract test, forcing normalizer + fixture updates together.
- **Contract tests do not call live APIs in CI.** They replay captured payloads.

### Mock provider fixtures

- Canonical fixtures live at `backend/tests/fixtures/providers/<name>/<operation>/<scenario>.json`. Example scenarios: `fixtures_day_with_live`, `fixture_detail_postponed`, `lineup_projected`, `lineup_confirmed_with_injury`, `events_var_overturned_goal`, `standings_with_relegation_zone`, `odds_h2h_closed_market`.
- Mocks read these files. Deterministic — same input always yields same output.
- The same fixtures are used by both unit tests and contract tests.

### Integration tests

- **Celery task round-trip**: given a mock provider, a beat task runs and writes to DB. Assertions verify canonical tables and `provider_payloads` are both updated with correct shape and FKs.
- **API round-trip**: a fixture with lineups + events + stats is seeded via mock provider; API endpoints return the expected JSON.
- Integration tests run in CI against the existing Postgres + Redis services already defined in `.github/workflows/ci.yml`.

### CI behavior without paid keys

- `ENVIRONMENT=test` forces mock providers across the board.
- CI's `.github/workflows/ci.yml` does not set `API_FOOTBALL_KEY`, `SPORTMONKS_KEY`, etc. — it already sets them to `""`. The abstraction must treat missing/empty keys as "provider disabled" rather than "provider authentication failed".
- `make test` locally follows the same convention: no keys required.

### Local behavior without paid keys

- `docker compose up -d` with an empty `.env` (no provider keys) must bring up the full stack. Mock providers serve all data. Frontend renders fully.
- A `make seed-mock` target (new in v0.5e) loads a comprehensive mock dataset covering one full matchday across all Phase 1 leagues.

### Provider drift detection

- Daily Celery task (`detect_provider_drift`) samples live API calls (1 call per provider per operation per day), compares response shape to the last committed fixture. Diff > threshold → admin alert. Non-blocking.
- Fixture refresh workflow: drift alert → engineer captures the new payload → commits it to `tests/fixtures/providers/...` → updates normalizer if needed → fixture and normalizer land in the same PR.

## Non-Negotiables

1. **Frontend never calls a provider directly.** All external sports data flows through ScoreLock's backend API. The frontend has no provider keys, no provider-specific branches, no provider names in responses.
2. **No paid provider before abstraction skeleton.** v0.5a must land before any SportMonks / API-Football Pro / The Odds API in-play / SportsData.io / Opta contract is signed or key is provisioned.
3. **No provider payload in AI prompts without normalization.** Claude prompts consume `Normalized*` objects. Raw JSON payloads do not get concatenated into prompts. If an AI feature needs a new field, the field is added to the Normalized object first.
4. **No scraping as production dependency.** SofaScore's and FotMob's unofficial endpoints are off-limits. Competitive-intelligence only. All production providers have a stated ToS and a licensed commercial relationship.
5. **No schema migration without rollback plan.** Every Alembic revision from v0.5b onward ships with a tested downgrade. Migrations are rehearsed against a DB dump before any remote apply.
6. **No changing existing provider behavior in v0.4.** This version is strictly documentation. No edits to `backend/app/services/{api_football,football_data,odds_api}.py`, no edits to `backend/app/services/tasks.py`, no edits to `backend/app/core/config.py`, no new dependencies.

## Open Questions

Decisions that require the project owner before paid provider integration or v0.5d begins. v0.5a can start without these decisions.

1. **Primary paid sports-data provider**: SportMonks (recommended in v0.3 for football depth + Allsvenskan) vs API-Football Pro (cheaper, current integration path, weaker metadata) vs SportsData.io (broader multi-sport but weaker football in EU) vs Stats Perform / Opta (enterprise-tier, requires commercial discussion). Impacts onboarding timeline (1 week for API-Football Pro upgrade, 1–3 weeks for SportMonks, quarter+ for enterprise).
2. **Broadcast data source**: SportMonks broadcast add-on, dedicated Nordic provider (e.g. Screenhits), Stats Perform partnership, or manual curation for Sweden only at launch. Blocks FotMob-style "Where to watch" card in match-detail.
3. **Odds tier**: The Odds API $99/mo (in-play included, 1M req/mo) vs $30/mo (30k req/mo, pre-match only). Blocks next-goal / in-play markets.
4. **Initial league package**: v0.3 default was Big-5 + CL/EL/UECL + Allsvenskan. Confirm whether Allsvenskan is a launch requirement (moats) or post-launch (simplicity). Superettan: include or defer?
5. **Raw payload retention period**: Proposal is 30d live, 180d non-live. Confirm acceptable under GDPR and storage-cost appetite.
6. **Raw payload storage location**: Postgres JSONB (current proposal) vs S3/object storage (cheaper at scale, harder to query, requires new infra). Tied to retention and volume.
7. **Provider conflict policy**: Default is provider priority + field overrides. Any operations where conflicts should instead escalate to manual review rather than silently pick a winner (e.g. final score on finished matches)?
8. **Mock-provider scope**: Should mocks include deliberately broken scenarios (schema drift, HTTP 500s, quota exhaustion) for chaos testing, or stay clean?
9. **Provider sandbox / staging**: Do we target two Railway environments (dev pointing to free/mock providers, prod pointing to paid) or one environment with paid keys ungated from day one?
10. **VAR event modeling**: The proposed enum splits VAR into five variants (goal awarded / cancelled / penalty awarded / overturned / red card). Confirm this is the product-level granularity we want to display, or collapse to a single `VAR_DECISION` with a nested sub-type.

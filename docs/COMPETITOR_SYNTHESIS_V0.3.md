# ScoreLock Competitor Synthesis v0.3

> Source: local capture under `competitor-ref/` (4 competitors, same match: Sunderland 0–4 Nottingham Forest, Premier League Round 34, 2026-04-24, Stadium of Light, ref: Darren England).
> Inventory confirmed via case-insensitive `find` from repo root. All four competitor folders use PascalCase (`Flashscore/`, `Fotmob/`, `Livescore/`, `Sofascore/`), screenshots live under `Screenshots/`, HAR files under `HAR/`.
> Observations below rely on README statements, screenshot review, and structural HAR inspection (unique hosts + entry counts). No proprietary code, CSS, assets, icons, branding, or tokens extracted or reused.

---

## Executive Summary

- ScoreLock must stop positioning as a "livescores + predictions" dashboard. The category it sits in is **Live Sports Intelligence** — a match-centric, metadata-rich, AI-augmented product. Flashscore/LiveScore/SofaScore/FotMob already own "livescores"; ScoreLock has to win on depth, narrative, and intelligence.
- The match-detail page is the product. All four competitors pour their differentiation into it; everything else (home, league list, standings) is table stakes.
- The minimum metadata floor is already well above what ScoreLock currently models: lineups, formations, substitutions, cards, commentary, xG, possession, shots, player ratings, VAR events, momentum graphs.
- FotMob has the most sophisticated feature set (TV/broadcast provider, pitch surface, weather, capacity, Play-by-Play video frames, Man-of-the-Match poll, live next-goal odds). It is the competitive ceiling for ScoreLock's MVP and is the most relevant comp for the Swedish audience.
- SofaScore is the metadata-depth reference: it runs its own data pipeline (single primary host `www.sofascore.com`), and its match-detail view surfaces VAR decisions (goals cancelled) and an Attack Momentum graph — both premium signals none of the other three expose visually.
- LiveScore is the clean-layout reference, but has the heaviest commercial surface (20 hosts in the capture, most are ad exchanges and odds servers) — ScoreLock should borrow clarity, not monetisation density.
- Flashscore is the market anchor on breadth and audio — `api.lsaudio.eu` in the HAR confirms audio commentary as a distinct product surface. ScoreLock will not match Flashscore's ligabredd; it must not try.
- Real-time architecture is mandatory. FotMob embeds live Stats Perform / Opta-sourced video frames (`secure.static.visualisation.performgroup.com`) and surfaces an 84:31 minute timer — ScoreLock's current WebSocket endpoint is defined but not fed (per prior intake).
- "Where to watch" (TV/broadcast + streaming provider surfaced next to the score) is a legitimate strategic differentiator for Sweden and Europe. FotMob is the only one that does it at this level.
- All four rely on premium data providers upstream (visible in hosts: `performgroup.com`, `sports-cube.com`). A paid-provider strategy for ScoreLock is now non-optional if the product is to compete on this surface.
- ScoreLock's current schema (`backend/app/models/models.py`) has no tables for players, lineups, events, or match statistics. Every single competitor-grade feature above requires schema work before UI work.
- Hard conclusion: freeze all UI redesign until the metadata model is in place. Redesign without data underneath is cosmetic.

## Capture Inventory

| Competitor | Match/page captured | Screenshots | HAR files | README present | Major gaps |
|---|---|---|---|---|---|
| Flashscore | Sunderland vs Nottingham Forest — match detail (`https://www.flashscore.com/match/football/nottingham-UsushcZr/sunderland-WSzc94ws/?mid=0AH7bYWj`) | 18 | 1 (`flashscore_sunderland_nottingham_match_detail.har`, ~9.5 MB, 356 entries, 11 unique hosts) | Yes | Only one match captured; no home/league/standings snapshots; tabs reviewed per README: Summary, Stats, Lineups, Player stats, Commentary, Odds, H2H, Standings, News |
| FotMob | Sunderland vs Nottingham Forest — match detail (`https://www.fotmob.com/sv/matches/sunderland-vs-nottm-forest/2vtwiu#4813712`) | 20 | 1 (`Fotmob_sunderland_nottingham_match_detail.har`, ~18.3 MB, 513 entries, 33 unique hosts) | Yes | Only one match; heavy ad-tech footprint in HAR; Swedish locale only; no home-feed or league-page captures |
| LiveScore | Sunderland vs Nottingham Forest — match detail (`https://www.livescore.com/en/football/england/premier-league/sunderland-vs-nottingham-forest/1529138/`) | 11 | 1 (`livescore_sunderland_nottingham_match_detail.har`, ~38.9 MB, 467 entries, 20 unique hosts) | Yes | Thinnest screenshot set; commentary / player ratings / momentum not visible in captured frames; SofaScore-level metadata not on LiveScore by design |
| SofaScore | Sunderland vs Nottingham Forest — match detail (URL placeholder `<URL>` in README, actual domain visible in HAR: `www.sofascore.com`) | 24 | 1 (`Sofascore_sunderland_nottingham_match_detail.har`, ~12.5 MB, 206 entries, 13 unique hosts) | Yes (README is template-scaffold with `<Match>`/`<URL>` placeholders still unfilled) | README incomplete; needs human fill of source URL; screenshot coverage is the most thorough of the four |

**Cross-cutting gaps (applies to all four captures):**
- Only match-detail captured. No home feed, no league page, no standings page, no search flow, no signup/favourite flow.
- Only one match per competitor. No pre-match / live / post-match contrast within the same product.
- Only desktop. No mobile captures — FotMob in particular is mobile-first and its mobile product is what dominates App Store rankings.
- Only Swedish locale for FotMob, mixed for others. No side-by-side locale comparison.
- No video/audio capture (FotMob Play-by-Play frames visible but not saved as media).

## Competitor Positioning

### Flashscore

**Strengths**
- 20-year breadth. Meta-description claim: 1000+ leagues, 200+ countries. Ownership: Livesport s.r.o. (Prague).
- Event timeline is complete: goals (with own-goal tag `(Own goal)`), yellow cards, substitutions, commentary lines, all minute-timestamped.
- Audio commentary surface (HAR host `api.lsaudio.eu`) — a product dimension none of the other three show in the capture.
- Structural stack: own CDN `static.flashscore.com` + internal content CDN `content.livesportmedia.eu` + data service `2.ds.lsapp.eu` + OTT image CDN `livesport-ott-images.ssl.cdn.cra.cz`. Self-hosted infrastructure.
- Market-compliant: Swedish `Stödlinjen` ad panel rendered next to match (legal responsible-gambling placement).

**Weaknesses**
- Visual density is brutal. Left sidebar + match tabs + nested sub-tabs + ad rails compete for attention; match context is secondary to list navigation.
- No player ratings, no xG in visible frames, no momentum graph.
- Zero editorial / AI-generated content. Redirects to `flashscore.mobi` for mobile (separate codebase).
- Mid-match screenshot shows static ad blocks occupying ~25% of horizontal real estate at desktop width.

**Metadata observed** (from README + screenshot of Round 34 match)
- Score, status ("Match Finished"), league + round, date/time, teams + crests.
- Event timeline: goals (scorer, minute, `(Own goal)` tag), yellow cards, substitutions (`↓` `↑` with player names + minute), commentary lines.
- Stats/Lineups/Player stats/Commentary/Odds/H2H/Standings/News tabs exist.
- `Unofficial audio commentary` indicator near score — dedicated audio stream surfaced.
- Ad panel with `Stödlinjen` (Swedish gambling help line) — regional compliance.

**Monetisation observed**
- Dominant surface: programmatic display ads via Google Syndication (`pagead2.googlesyndication.com`).
- Regional betting ads with jurisdictional compliance copy.
- No user sign-up paywall in captured view; core product is ad-supported.

**What ScoreLock should copy conceptually**
- The full event-timeline depth. Minute-by-minute goals + cards + subs + commentary lines is the floor, not the ceiling.
- The "Unofficial audio commentary" treatment as a pattern: optional audio channel per match, not a core requirement, but a premium surface when available.
- The compliance-aware ad slot pattern for Swedish market (Stödlinjen footer/sidebar placement).

**What ScoreLock should avoid**
- Three levels of tab nesting. This is Flashscore's legacy debt, not a feature.
- Ad density at desktop ≥1280px — Flashscore reserves ~25% horizontal real estate for ads and it visibly degrades the match experience.
- A separate mobile codebase (`flashscore.mobi`). ScoreLock's Next.js + responsive is correct here.
- Competing on ligabredd. 1000+ leagues is not a fight ScoreLock can win or should want.

### LiveScore

**Strengths**
- Cleanest top-of-page hierarchy of the four. Header, sport-switcher, hero-card match, tabs — flat and scannable.
- Data pipeline lives on dedicated hosts (`prod-cdn-media-api.livescore.com` + `prod-cdn-public-api.livescore.com`) plus what looks like third-party data via `api-cdn.sports-cube.com`. Clean separation of concerns.
- Odds aggregation on `v1.oddsserve.com` — dedicated live-odds provider, indicating they treat odds as a first-class product surface, not a plug-in.
- "Who will win?" community poll sponsored by bet365 is a conversion vehicle, not just telemetry — clear monetisation design.

**Weaknesses**
- Heaviest ad/tracking surface of the four: 20 hosts in the capture, dominated by ad exchanges (`ads.pubmatic.com`, `ad.doubleclick.net`, `c.bannerflow.net`, `securepubads.g.doubleclick.net`, `ut.pubmatic.com`) and consent management (`cdn-ukwest.onetrust.com`, `geolocation.onetrust.com`).
- HAR payload 38.9 MB for a single match page — roughly 4× Flashscore, despite fewer visible features. That weight is mostly ads.
- H2H is thinner than Flashscore (README confirms this).
- No xG, no player ratings, no Attack Momentum, no Play-by-Play video — visible in captured frames.
- Disney+ embedded promo mid-match-content on desktop is aggressive cross-promotion.

**Metadata observed**
- Score, minute (`62'`), teams + crests, competition (Premier League, England).
- Match Info strip: date (24 Apr 2026), referee (Darren England, England), stadium (Stadium Of Light).
- Tabs: Info, Summary, Stats, Line-ups, Odds, Table, H2H.
- H2H breakdown per team (All / Sunderland / Nottingham Forest tabs per README).
- Historical H2H with competition + season per row.
- Left sidebar: team favourites, top competitions, region navigation.

**Monetisation observed**
- Programmatic display at scale (pubmatic, doubleclick, bannerflow).
- Direct sponsorship integration (bet365 within the match poll).
- Disney+ inline banner.
- Footer SEO links into betting and casino verticals by region (UK/BR/US/ZA/CA).

**What ScoreLock should copy conceptually**
- Flat tab hierarchy. Info/Summary/Stats/Line-ups/Odds/Table/H2H — seven tabs, one level deep. This is the right shape.
- Match Info strip (date · referee · stadium) as a secondary header right under the score.
- Community poll as a conversion surface when a sponsor is available.
- Clean separation between a public data API (`prod-cdn-public-api.livescore.com`) and a media API (`prod-cdn-media-api.livescore.com`) — architectural pattern worth reusing behind ScoreLock's provider abstraction.

**What ScoreLock should avoid**
- Any ad exchange integration this heavy. It kills LCP and user trust.
- Inline promo for non-football brands (Disney+) on a football match page.
- Competing on generic H2H when SofaScore/FotMob already have better versions.

### SofaScore

**Strengths**
- Metadata depth is the best of the four. Visible in screenshots: Attack Momentum bar graph over time, event timeline with VAR-cancelled goals (`Goal cancelled`), player names clickable, live odds "Match goals" line markets (Under/Over).
- Runs its own data pipeline — the HAR shows `www.sofascore.com` as the primary data host (13 unique hosts total, by far the leanest third-party footprint of the four). They are a data company that happens to have a UI.
- Multi-sport primary nav in the same product (Football, Tennis, Basketball, Baseball, Volleyball, Handball, Table Tennis, MotoGP, Darts, American Football) without fragmenting the UX.
- Live / Upcoming toggle at fixture list level — correct primitive.

**Weaknesses**
- Very dense. Non-trivial learning curve for casual users.
- Heavy reliance on their own ratings ecosystem (SofaScore ratings is the product moat); not trivially replicable.
- No TV/broadcast data visible.
- Commentary depth not visible in captured frames.

**Metadata observed**
- Score, live status (`Live`), teams + crests, competition.
- Event timeline with VAR decisions (`Goal cancelled`), goals, substitutions (`↓`/`↑`), yellow cards, "Additional time" markers.
- "Match goals" line market inline in the match detail (Under/Over with odds).
- Attack Momentum graph — vertical bars over time indicating which team is pressing.
- Tabs: Details, Odds, Lineups, Statistics, Commentary, Standings.
- Full multi-sport side navigation.

**Monetisation observed**
- Comparatively restrained ad surface (13 hosts total; Criteo, Liveramp, Google adjacents).
- No aggressive banner advertising in the main match view.
- Monetisation likely sits on premium data licensing + own ratings API rather than display ads — consistent with their lean ad host count.

**What ScoreLock should copy conceptually**
- Attack Momentum graph. This is high-signal, not decorative. Implementable as a time-series derived from shot / xG / possession events. Strong differentiator.
- VAR-decision visibility in the timeline (goal cancelled, penalty awarded/overturned). Flashscore/LiveScore miss this.
- "Match goals Under/Over" inline within the match view, not buried in an Odds tab.
- Self-hosted data pipeline philosophy: the architecture should make provider swaps invisible to the UI.

**What ScoreLock should avoid**
- Proprietary rating systems — do not copy SofaScore's player rating algorithm or branding. Use provider-supplied ratings (Opta / Stats Perform / SportMonks) via the abstraction layer.
- Multi-sport expansion before football depth is achieved.
- Density on the primary match view. SofaScore gets away with it; ScoreLock with less brand equity cannot.

### FotMob

**Strengths**
- The most sophisticated match page of the four. Visible in the captured screenshot on Swedish locale:
  - Header tabs: Fakta, Rapport, Lag, Tabell, Statistik, Mot varandra.
  - Match info strip: date, stadium, referee, TV provider (`Viaplay SE…`).
  - Right rail card set: **Play-by-Play video frame** (live short clip, caption "Passning W. Isidor"), **bet365 next-goal odds widget** (Vem gör nästa mål? 1.40 / X 1.44 / 2 6.00), **venue details** (Stadium of Light, Sunderland England, Kapacitet 49 000, Yta Gräs, Väder 10°C), **other live Premier League matches**.
  - Main content: **"Man of the Match" poll** with FotMob-rated players (Morgan Gibbs-White, Igor Jesus, Chris Wood, Nikola Milenkovic).
  - Live commentary snippet inline.
  - Secondary rail: Momentum + Top statistik.
- Swedish-first localization natively supported.
- Backed by Stats Perform / Opta (HAR host `secure.static.visualisation.performgroup.com`) — premium upstream data.
- Clear product-led monetisation: affiliate/watch CTA (Viaplay) + bet365 odds widget, not ad-exchange spam.

**Weaknesses**
- Heaviest ad-tech / RTB bidding footprint of the four (33 hosts: `rubiconproject`, `sparteo`, `pubmatic`, `openx`, `adsrvr.org`, `casalemedia`, `3lift`, `vrtcal`, `inmobi`, `smaato`, etc). The match page loads a full RTB auction per impression.
- HAR payload 18.3 MB, 513 network entries — long LCP likely.
- "Man of the Match" and FotMob ratings create a data moat that ScoreLock cannot replicate without building its own rating system or licensing Opta ratings.

**Metadata observed**
- Score, live minute (`84:31`), teams + crests, competition (Premier League, Round 34).
- Full match info strip: date, stadium, referee, TV provider (Viaplay SE).
- Goal list with scorers and minutes (`Hume 17' OG`, `Wood 31'`, `Gibbs-White 34'`, `Igor Jesus 37'`).
- Stadium card: capacity (49 000), pitch surface (Gräs), weather (10°C with night icon).
- Live Play-by-Play video frame.
- Next-goal market odds (bet365 widget).
- Man-of-the-Match poll with named candidates.
- Other live matches in same competition (side-by-side context).
- Swedish locale throughout.

**Monetisation observed**
- Full RTB ad auction stack (see hosts above).
- Affiliate/watch CTA to TV provider.
- Sponsored odds widget (bet365 — probably a commercial integration with a rev-share rather than display).

**What ScoreLock should copy conceptually**
- "Where to watch" card (TV provider + affiliate link) next to the score. Highest-signal product primitive FotMob has, and none of the others do.
- Venue card (capacity, surface, weather) — cheap to implement, high perceived quality.
- Next-goal micro-market (live in-play odds on a single market) as a lightweight in-play product; premium providers expose this.
- Inline "Man of the Match" poll pattern — engagement + community signal (ScoreLock can run this without proprietary ratings: just user votes).
- Play-by-Play short video frame as a secondary rail — optional, provider-dependent.
- Swedish-first localization (ScoreLock already has i18n scaffolding in `frontend/src/lib/i18n.ts`).

**What ScoreLock should avoid**
- The full RTB ad stack. ScoreLock's affiliate-first revenue model explicitly trades ad volume for affiliate quality. Don't reintroduce ad-tech bloat.
- Proprietary rating systems. Use provider ratings via abstraction.
- Feature density in the main column — FotMob gets away with it because the right rail absorbs most of the visual load; ScoreLock needs the same two-column discipline.

## Cross-Competitor Metadata Taxonomy

Column key: ✅ directly observed in the capture; ⚠ observed partially or via README only; ❌ not observed.

| Category | Field / entity | Flashscore | LiveScore | SofaScore | FotMob | ScoreLock priority | Backend implication | Frontend implication |
|---|---|---|---|---|---|---|---|---|
| Sport | sport | ✅ (football focus, others in footer) | ✅ (top nav 5 sports) | ✅ (top nav 11 sports) | ✅ (football-only capture) | P0 | Schema: `sports` lookup, not a string column; needed for multi-sport later | Sport-aware routing + icon pack |
| Geo | country | ✅ | ✅ | ✅ | ✅ | P0 | `countries` lookup, FK from `leagues` + `teams` | Country flag rendering, country-scoped nav |
| Competition | competition | ✅ | ✅ | ✅ | ✅ | P0 | Already partial in `backend/app/models/models.py` (`leagues`); needs `api_ids JSONB` for cross-provider ID mapping | League header + logo |
| Season | season | ✅ | ✅ | ✅ | ✅ | P0 | Column exists on fixtures/standings; needs `seasons` lookup for cleaner FKs | Season filter on standings/stats |
| Round | round | ✅ | ✅ | ✅ | ✅ (Omgång 34) | P0 | Column exists; normalize to numeric + display label | Round-page routing (already `/rounds/[league]/[round]`) |
| Fixture | fixture | ✅ | ✅ | ✅ | ✅ | P0 | Table exists; needs `external_ids JSONB` + `kickoff_tz` | Match-detail skeleton exists |
| Team | team | ✅ | ✅ | ✅ | ✅ | P0 | Table exists; needs `colors`, `short_name_locale`, `external_ids JSONB` | Tricot colors for inline renders |
| Player | player | ✅ (Player stats tab) | ✅ (Line-ups) | ✅ (clickable names) | ✅ (MoM poll) | P0 | **Does not exist in schema.** New `players` table required | No player profile pages exist |
| Lineup | lineup (projected + confirmed) | ✅ | ✅ | ✅ | ✅ | P0 | **Does not exist.** New `lineups` + `lineup_players` tables | Pitch view component, bench list |
| Formation | formation code | ✅ | ✅ | ✅ | ✅ | P0 | New column on `lineups.formation_code` | Formation visual (e.g. 4-3-3 on a grid) |
| Goal | goal (scorer + assist + minute + type) | ✅ (OG tagged) | ✅ | ✅ | ✅ (OG tagged) | P0 | New `match_events` table with `event_type='GOAL'` | Timeline rendering |
| Assist | assist (player_id) | ✅ | ⚠ | ✅ | ⚠ | P0 | Column on `match_events` | Timeline rendering |
| Own goal | own_goal flag | ✅ | ⚠ | ✅ | ✅ | P0 | Flag on `match_events` | Timeline icon variant |
| Yellow card | yellow_card | ✅ | ✅ | ✅ | ⚠ | P0 | `match_events` row | Timeline icon |
| Red card | red_card | ⚠ | ⚠ | ✅ | ⚠ | P0 | `match_events` row | Timeline icon |
| Substitution | substitution (in, out, minute) | ✅ | ✅ | ✅ | ⚠ | P0 | `match_events` row with `player_in_id` + `player_out_id` | Timeline dual-player row |
| VAR | VAR decision (goal cancelled, penalty) | ❌ | ❌ | ✅ | ⚠ | P1 | `match_events` with `event_type='VAR_*'`; provider-dependent | Timeline special icon + tooltip |
| Live timer | live_minute | ✅ (`62'`) | ✅ (`62'`) | ✅ | ✅ (`84:31`) | P0 | Push field on fixture update, client-side tick between pushes | Live clock component exists (`use-live-scores.ts`); not fed by server |
| Live status | status enum (SCHEDULED, IN_PLAY, HALF_TIME, FULL_TIME, CANCELLED, etc.) | ✅ | ✅ | ✅ | ✅ | P0 | Enum exists on fixtures; needs full provider-mapped coverage | Status-driven UI mode |
| xG | expected goals | ⚠ (README claims) | ❌ | ✅ | ✅ | P0 | New `match_statistics` table, provider-dependent | Stat panel + Attack Momentum input |
| Possession | possession % | ⚠ | ⚠ | ✅ | ✅ | P0 | `match_statistics` | Bar rendering |
| Shots | shots total | ⚠ | ⚠ | ✅ | ✅ | P0 | `match_statistics` | Stat panel |
| Shots on target | shots_on_target | ⚠ | ⚠ | ✅ | ✅ | P0 | `match_statistics` | Stat panel |
| Corners | corners | ❌ | ⚠ | ✅ | ✅ | P1 | `match_statistics` | Stat panel |
| Fouls | fouls | ❌ | ⚠ | ✅ | ✅ | P1 | `match_statistics` | Stat panel |
| Odds | odds (H2H, totals, BTTS) | ✅ | ✅ | ✅ (inline line) | ✅ (next goal) | P0 | `odds` table exists; needs market taxonomy + `odds_snapshots` hypertable for movement | Odds tab + inline markets |
| Bookmaker | bookmaker | ✅ | ✅ | ✅ | ✅ (bet365) | P0 | `bookmakers` lookup; FK from `odds` | Bookmaker logo handling (license-aware) |
| Odds movement | odds_delta over time | ⚠ | ⚠ | ⚠ | ⚠ | P1 | TimescaleDB hypertable `odds_snapshots` (engine already available in local `docker-compose.yml`) | Sparkline in value-bet card |
| TV channel | tv_channel_per_region | ❌ | ❌ | ❌ | ✅ (Viaplay SE) | P0 | New `broadcasts` table keyed by fixture + country | "Where to watch" card |
| Streaming provider | streaming_provider | ❌ | ❌ | ❌ | ✅ | P0 | Same as above with `provider_type='STREAMING'` | Same card |
| Referee | referee | ⚠ | ✅ | ✅ | ✅ | P0 | New `referees` table + FK on fixtures | Match info strip |
| Venue | venue (name + city + country) | ✅ | ✅ | ✅ | ✅ | P0 | New `venues` table + FK on fixtures | Venue card |
| Capacity | venue capacity | ⚠ | ❌ | ❌ | ✅ (49 000) | P1 | Column on `venues` | Venue card |
| Pitch surface | surface | ❌ | ❌ | ❌ | ✅ (Gräs) | P2 | Column on `venues` | Venue card |
| Weather | weather at kickoff | ❌ | ❌ | ❌ | ✅ (10°C) | P1 | New `weather_snapshots` table or embed in fixture; provider or external weather API | Venue card |
| H2H | head-to-head last N | ✅ | ✅ | ✅ | ✅ | P0 | Derivable from existing `fixtures` table with a new query endpoint | H2H tab (exists as endpoint, needs UI polish) |
| Standings | league standings with form | ✅ | ✅ | ✅ | ✅ | P0 | Table exists; form column and zone colouring needed | `/standings` exists, needs zone coloring (partial) |
| News | related news articles | ✅ (News tab) | ⚠ | ❌ | ✅ (Rapport tab) | P1 | `articles` table exists; association via `fixture_id` | Article rail on match page |
| Social feed | embedded tweets / comments | ❌ | ❌ | ❌ | ❌ | P2 | Out of scope v0.4–v1.0; consider later | Deferred |
| Player ratings | per-player rating | ❌ | ❌ | ✅ (proprietary) | ✅ (proprietary) | P1 | Provider-supplied column on `match_lineup_players`; do not self-rate | Player chip rating badge |
| Momentum graph | attack momentum over time | ❌ | ❌ | ✅ | ✅ | P1 | Derived from event stream over time windows | Line/bar chart |
| Commentary | live text commentary | ✅ | ⚠ | ⚠ | ✅ (snippet) | P0 | New `match_commentary` table, minute-ordered | Commentary feed |
| Audio commentary | optional audio stream | ✅ (host `api.lsaudio.eu`) | ❌ | ❌ | ❌ | P2 | Provider-dependent URL field on fixture | Audio player (deferred) |
| Play-by-Play video | live short video clips | ❌ | ❌ | ❌ | ✅ | P2 | Provider-dependent URL list on fixture | Video component (deferred) |
| Man of the Match poll | community MoM vote | ❌ | ❌ | ❌ | ✅ | P1 | Extend `user_predictions` concept to `motm_votes`; simple lookup per fixture | Inline poll |
| Next-goal odds | live in-play single-market odds | ❌ | ❌ | ⚠ | ✅ | P1 | Odds-provider in-play tier required ($99+/mo on The Odds API) | Right-rail widget |
| User predictions / tipping | user tip per fixture | ❌ | ✅ (Who will win poll) | ❌ | ❌ | P0 — already exists | `user_predictions` table exists | `tip-form.tsx` exists |

## Match Detail Page Requirements

Forward spec for ScoreLock's match-detail page, per section. Current support column reflects the state of `backend/app/api/routes.py`, `backend/app/models/models.py`, and `frontend/src/app/matches/[id]/page.tsx` as of commit `00ae224`.

### 1. Header

- **Purpose**: Identify the match in one glance — teams, crests, competition, round, kickoff, status, score.
- **Data required**: team name, team crest, team tricot colours, competition name + logo, round number, kickoff datetime (local + UTC), current status, score, halftime score.
- **Current ScoreLock support**: partial. `fixtures` has teams, kickoff, status, score. Missing: team colours, halftime score display, round label normalization.
- **Backend work**: add `teams.colors JSONB`; add `fixtures.home_goals_ht` / `away_goals_ht` surfacing (fields already exist per earlier inspection).
- **Frontend work**: upgrade header component to show colour-coded divider + round label + halftime score subscript.
- **Provider requirement**: basic — all providers supply this.

### 2. Live status

- **Purpose**: Live minute, live status, live score ticker.
- **Data required**: live_minute (int + stoppage), status enum, score, goalscorer notifications.
- **Current ScoreLock support**: partial. `use-live-scores.ts` in `frontend/src/lib/` implements a WebSocket hook but the backend endpoint `/api/v1/ws/live` is not fed by any Celery task (documented in prior intake).
- **Backend work**: wire a `live_ingest` path (provider push feed → Redis pub/sub → existing WebSocket endpoint). Schema: new `match_events` rows stream through.
- **Frontend work**: connect existing hook to actual event stream; add stoppage-time rendering; add score-pop animation on goal event (CSS hook exists in `frontend/src/app/globals.css` per prior audit).
- **Provider requirement**: provider with push (SportMonks Live add-on, API-Football Pro polling at 15s).

### 3. AI match intelligence

- **Purpose**: ScoreLock's differentiation. AI-written pre-match preview, in-play momentum narrative, post-match report, inline insight badges ("Sunderland press-resistant in last 4"), value-bet callout with reasoning.
- **Data required**: match context (form, H2H, injuries, suspensions, line-ups, odds), ML prediction output, Claude-generated narrative, value-bet edge + Kelly stake.
- **Current ScoreLock support**: partial. `backend/app/services/content_generator.py` exists and supports 5 article types. ML prediction exists (`backend/app/ml/predictor.py`, model `v20260210-0320`). But: articles not generated automatically per fixture yet on live data, Anthropic SDK is 0.43.0 (outdated), content tasks idle due to missing input data.
- **Backend work**: upgrade Anthropic SDK; trigger pre-match article 2h before kickoff; post-match article 2h after final whistle; in-play insight computation hook (lightweight rule engine → LLM post-process).
- **Frontend work**: inline article card on match detail + in-play "AI insight" badge component.
- **Provider requirement**: Anthropic (already present); premium sports provider to feed rich enough context.

### 4. Event timeline

- **Purpose**: Chronological list of goals, cards, subs, VAR incidents, penalties.
- **Data required**: `match_events` rows: minute, stoppage, event_type, player(s), description.
- **Current ScoreLock support**: **none**. No events table, no events endpoint, no timeline component.
- **Backend work**: new `match_events` table + Alembic migration; provider ingestion task; `GET /api/v1/fixtures/{id}/events` endpoint.
- **Frontend work**: new timeline component with event icons (goal, OG, yellow, red, sub, VAR, penalty).
- **Provider requirement**: SportMonks, API-Football, Stats Perform via FotMob partnership all provide this.

### 5. Statistics

- **Purpose**: Per-team possession, shots, shots on target, xG, corners, fouls, passes.
- **Data required**: `match_statistics` rows per fixture per team.
- **Current ScoreLock support**: **none**. `fixtures.stats JSONB` column exists but is not populated per inspection of live DB.
- **Backend work**: either formalize `fixtures.stats` schema with a typed Pydantic shape, or introduce a dedicated `match_statistics` table (recommended for time-series and provider mapping). Sync task.
- **Frontend work**: dual-bar stat panel component.
- **Provider requirement**: premium tier. SportMonks / API-Football Pro.

### 6. Lineups / formations

- **Purpose**: Projected lineup (pre-match) → confirmed lineup (kickoff) → in-match subs applied.
- **Data required**: `lineups` (fixture_id, team_id, formation_code, confirmed_at), `lineup_players` (lineup_id, player_id, position, grid_x, grid_y, is_starter, is_captain).
- **Current ScoreLock support**: **none**.
- **Backend work**: new `players`, `lineups`, `lineup_players` tables + migration; provider ingestion task firing 2h pre-kick and on every lineup update.
- **Frontend work**: pitch-view component with player chips, formation label, bench list.
- **Provider requirement**: premium tier.

### 7. Odds / value layer

- **Purpose**: Pre-match odds (H2H, totals, BTTS), live in-play odds ticker, next-goal micro-market, value-bet badge when ScoreLock model edge > threshold.
- **Data required**: `odds` + new `odds_snapshots` hypertable for movement; ML prediction vs best-odds comparison.
- **Current ScoreLock support**: partial. `odds` table exists and is empty. `value-bets` endpoint exists. No in-play odds, no movement tracking.
- **Backend work**: The Odds API integration upgrade to in-play plan; `odds_snapshots` TimescaleDB hypertable; value-bet detector with snapshot comparison.
- **Frontend work**: inline market within match view (SofaScore style) + right-rail next-goal widget (FotMob style) + value-bet badge on any market with edge > 3%.
- **Provider requirement**: The Odds API $99+/mo or SportMonks Live Odds add-on.

### 8. H2H

- **Purpose**: Last N meetings between the two teams across all competitions.
- **Data required**: existing `fixtures` table with same home/away team pair query.
- **Current ScoreLock support**: partial. Endpoint `/h2h/{t1}/{t2}` exists in `backend/app/api/routes.py`. No dedicated UI component on match detail page per current frontend.
- **Backend work**: expand to accept `limit` + `competition_filter`.
- **Frontend work**: H2H tab on match detail.
- **Provider requirement**: none (derivable from own data).

### 9. Standings impact

- **Purpose**: "If this match ends X, team A moves from 5th to 3rd" — live standings projection.
- **Data required**: current `standings` + fixture potential outcomes.
- **Current ScoreLock support**: **none** (projection) / partial (raw standings).
- **Backend work**: new endpoint `/fixtures/{id}/standings-projection` that computes all 3 outcomes against the league table.
- **Frontend work**: compact panel on match detail.
- **Provider requirement**: none.

### 10. News / social context

- **Purpose**: Related AI articles + relevant news feed.
- **Data required**: `articles` with `fixture_id` / team association.
- **Current ScoreLock support**: partial. `articles` table exists, 0 rows in live DB.
- **Backend work**: activate content-generator tasks on fresh data. 5 dead RSS feeds should be removed (per prior intake) — kept as open backlog, no change in this document.
- **Frontend work**: related-articles rail.
- **Provider requirement**: Anthropic (already configured).

### 11. Where to watch

- **Purpose**: TV provider + streaming provider surfaced with affiliate/watch CTA. Sweden-primary, Europe broader.
- **Data required**: new `broadcasts` table with `fixture_id`, `country`, `provider_name`, `provider_type` (TV/STREAMING), `watch_url`, `affiliate_partner`.
- **Current ScoreLock support**: **none**.
- **Backend work**: new `broadcasts` table; provider or manual upload initially (provider: FotMob's upstream is Stats Perform for this; SportMonks exposes it in paid tier).
- **Frontend work**: venue-adjacent "Where to watch" card (FotMob pattern) with affiliate CTA where applicable.
- **Provider requirement**: SportMonks paid tier or manual curation for Swedish market (Viaplay / TV4 / C More).

### 12. User prediction / tipping

- **Purpose**: User enters their H/D/A + optional correct score before kickoff; compared against AI post-match.
- **Data required**: existing `user_predictions` table.
- **Current ScoreLock support**: already implemented. `frontend/src/components/tip-form.tsx`, `frontend/src/components/match-tip-section.tsx` (now uses corrected `getAccessToken` per v0.2 commit `00ae224`), backend `user_predictions` table, `/api/v1/tips` endpoint.
- **Backend work**: none for MVP. Later: weekly scoring + streak bonuses (already partial in `backend/app/services/tasks.py score_user_predictions`).
- **Frontend work**: none for MVP.
- **Provider requirement**: none.

## Data Provider Requirements

Based on the four competitor captures — the minimum bar to compete on match-detail.

### Must-have (P0)

- **Live event latency ≤ 10s** from world to API. Non-negotiable; LiveScore / SofaScore / FotMob all operate in this band.
- **Lineups** — projected + confirmed, with formation codes and grid positions. Match-detail without lineups is unviable in 2026.
- **Event stream** — goals (with own-goal flag), cards (yellow/red), substitutions, stoppage. Minute + stoppage precision.
- **Match statistics** — possession, shots, shots on target at minimum. xG strongly preferred as SofaScore and FotMob both show it.
- **Live odds** — H2H, totals, BTTS for pre-match; in-play for next-goal / next-card micro-markets.
- **Allsvenskan + Superettan coverage** — the strategic moat. Must be present in provider's tier.
- **European competition coverage** — PL, La Liga, Serie A, Bundesliga, Ligue 1, CL, EL, UECL.
- **Referee + venue metadata** — LiveScore, SofaScore, and FotMob all display this as a match-info strip.
- **Provider ID stability + mapping** — stable external_ids per entity, so ScoreLock's internal identity model is not coupled to any one provider.

### Should-have (P1)

- **xG and player ratings** — SofaScore and FotMob differentiate on this. ScoreLock should consume, not compute, provider ratings.
- **VAR decisions** — SofaScore surfaces these; differentiator.
- **Momentum / pressure data** — either provider-supplied or derived from the event stream on our side.
- **TV / broadcast data per region** — FotMob-only in this capture. Huge Nordic value.
- **Weather at kickoff** — FotMob-only. Low cost to surface.
- **Venue capacity + pitch surface** — FotMob-only.
- **Social / news feed integration** — Flashscore has a News tab; low priority vs our own AI content.
- **Push / WebSocket / SSE feed** — strongly preferred over polling for live match view; SportMonks has it as an add-on.

### Later (P2)

- **Audio commentary stream** — Flashscore-exclusive in this capture. Useful optionality when provider supplies.
- **Play-by-Play short video frames** — FotMob exclusive; Stats Perform / Opta-dependent.
- **Embedded social feed (tweets, comments)** — risk/value ratio is poor pre-scale.
- **Man-of-the-Match poll** with proprietary ratings — poll we can do ourselves; proprietary rating we should not.

## Current ScoreLock Gap Analysis

Against the benchmark above, comparing to repo state at commit `00ae224`:

### Already exists
- Match-detail route scaffold: `frontend/src/app/matches/[id]/page.tsx`.
- Live-score client hook: `frontend/src/lib/use-live-scores.ts`.
- Existing WebSocket endpoint: `backend/app/api/websocket.py` (defined, not fed).
- Tipping: `frontend/src/components/tip-form.tsx` + `frontend/src/components/match-tip-section.tsx` + `user_predictions` in `backend/app/models/models.py`.
- Odds schema: `odds` table in `backend/app/models/models.py` (empty in prod).
- Value-bets endpoint: `backend/app/api/routes.py`.
- Predictions: `backend/app/ml/predictor.py`, model artifact `backend/app/ml/trained_models/`.
- Article pipeline: `backend/app/services/content_generator.py` + `articles` table via migration `backend/migrations/versions/1f5b8ca20887_add_articles_table.py`.
- Multi-provider clients (current, free-tier-constrained): `backend/app/services/football_data.py`, `backend/app/services/api_football.py`, `backend/app/services/odds_api.py`.
- i18n scaffold: `frontend/src/lib/i18n.ts`, `frontend/src/components/locale-provider.tsx`, `frontend/src/components/language-toggle.tsx`.
- Admin auth + allowlist: verified in `backend/app/api/routes.py:510–523` (`ADMIN_EMAILS`, `Depends(get_current_user)`, 403 on miss).
- Auth token normalization: landed in v0.2 via `frontend/src/lib/auth-token.ts` + callers.

### Partial
- Standings (`backend/app/models/models.py` + `frontend/src/app/standings/page.tsx`): exists, needs zone colouring + form strings — some already in place per prior audit.
- Articles pipeline: code exists, zero rows in DB because upstream data is thin (no kickoff-adjacent rich context yet).
- Live WebSocket: endpoint defined, frontend consumer exists, **no publisher** on the backend — dead channel.
- ML model: tracked in `backend/app/ml/trained_models/metadata.json` as version `v20260210-0320`; trained pre-25/26 season; generating predictions against unseen distribution.
- Provider clients: exist, but coupled directly to services (no abstraction layer yet).
- Content-generator: present but Anthropic SDK is 0.43.0 — upgrade required before content tasks are trusted.
- Sentry: half-removed (backend SDK still pinned in `backend/requirements.txt`; frontend `sentry-provider.tsx` is a passthrough shell).

### Missing
- `players` table — required for lineups, MoM polls, player-level events.
- `lineups` + `lineup_players` tables — required for pitch view.
- `match_events` table — required for event timeline and for deriving momentum.
- `match_statistics` table — required for stat panel (possession, shots, xG).
- `venues` table (currently stored as free-text `fixtures.venue_name` per models — needs promotion).
- `referees` table.
- `broadcasts` table — "Where to watch" card.
- `weather_snapshots` or weather column on fixtures.
- `odds_snapshots` hypertable (TimescaleDB is already running locally per `docker-compose.yml`, unused).
- `match_commentary` table.
- `provider_payloads` JSONB raw-store table (for replay + debugging across providers).
- Provider abstraction layer at the code level (`backend/app/providers/` does not exist; current provider calls live directly in `backend/app/services/`).
- Cross-provider ID-mapping columns (`fixtures.external_ids`, `teams.external_ids`, `players.external_ids` — last one doubly missing).

### Must remove / deprioritize
- **Sentry half-state**: either re-enable end-to-end or finish the removal. The 9-LOC passthrough `frontend/src/components/sentry-provider.tsx` is cruft.
- **RSS-based news rewrite path** reliance: 5 of 9 feeds return 4xx per prior runs. Do not invest more in RSS until dedicated provider news feeds are evaluated.
- **Building our own player rating system**. License / ingest provider ratings, do not invent a new one.
- **Building a deep Flashscore-like multi-sport nav**. Football-only for v0.4–v1.0.
- **Ad-exchange integrations**. Inconsistent with the affiliate-first revenue model.
- **Separate mobile codebase / `.mobi` subdomain**. Responsive Next.js is sufficient.

## Recommended Product Direction

**Position ScoreLock as: "Live Sports Intelligence Platform"**, not a livescore, not a dashboard.

- **Why not generic livescore.** Flashscore / LiveScore own that category. They have a decade-plus of SEO, app distribution, provider contracts, and ad economics. Attacking their head-on surface is a losing framing. ScoreLock has to redefine the surface so the comparison stops being 1000+ leagues vs 8.
- **Why match-detail is the core.** All four competitors invest their depth in the match page. Match-detail is where users spend time, where affiliate conversion happens, where AI content lands, and where data depth is visible. Home feeds and league lists are discovery surfaces — they route users to the match page. ScoreLock's v0.4–v1.0 work must make the match-detail page unignorable.
- **Why AI must sit on top of normalized metadata.** Claude-generated text without real lineups, events, xG, and odds movement is generic filler. The quality of AI output is bounded by the quality of the structured metadata underneath. This is why the schema work (players, lineups, events, stats, broadcasts) precedes any AI-content expansion.
- **Why provider abstraction is mandatory.** Each competitor uses premium data (`performgroup.com` visible in FotMob HAR; `sports-cube.com` in LiveScore HAR; SofaScore owns its pipeline). ScoreLock will run multiple providers simultaneously — SportMonks primary, API-Football fallback, The Odds API for odds, football-data.org for dev/demo. The application must not know which provider served a given field. That is the job of the abstraction layer proposed in the v0.3 intake.
- **Why TV/broadcast data is a strategic feature.** Only FotMob has it. It is high-signal for users ("can I watch this?"), high-monetisation for us (affiliate CTA directly on the match view), and under-served in the Swedish market specifically (Viaplay, TV4, C More fragmentation). It is a cheap-to-implement, high-perception feature that directly outflanks Flashscore and LiveScore.

## v0.4 Implementation Roadmap Proposal

No implementation in this document. Sequenced versions follow. Each version is small, shippable, and unlocks the next.

### v0.4 — Provider abstraction design (design doc only; no code)

- **Goal**: Produce `docs/PROVIDER_ABSTRACTION_V0.4.md` containing the `SportsDataProvider` interface contract, `provider_payloads` raw-store policy, registry + fallback rules, and a migration plan from current direct service calls to the abstraction. Zero runtime change.
- **Files likely touched**: `docs/PROVIDER_ABSTRACTION_V0.4.md` (new). Nothing else.
- **Migration required**: no.
- **Risk**: low — design-only.
- **Validation commands**: `test -f docs/PROVIDER_ABSTRACTION_V0.4.md && echo OK`; `git status --short`.

### v0.5 — Add metadata schema

- **Goal**: Alembic migrations for `players`, `lineups`, `lineup_players`, `match_events`, `match_statistics`, `venues`, `referees`, `broadcasts`, `provider_payloads`, and `external_ids JSONB` additions to `fixtures`/`teams`. No provider wiring yet. No endpoint changes. Seeds with mock data for local dev.
- **Files likely touched**: `backend/migrations/versions/<n>_add_match_detail_metadata.py` (new), `backend/app/models/models.py` (extended).
- **Migration required**: yes.
- **Risk**: medium — largest schema change in project history.
- **Validation commands**: `docker compose exec backend alembic upgrade head`; `docker exec scorelock-db psql -U scorelock -d scorelock -c "\dt"` expected to show new tables; `make test` after `make dev-install`.

### v0.6 — Match detail API expansion

- **Goal**: New read-only endpoints: `GET /fixtures/{id}/lineup`, `/events`, `/statistics`, `/broadcasts`, `/standings-projection`. All served from the new tables, populated initially from seeded mock data.
- **Files likely touched**: `backend/app/api/routes.py` (new handlers), `backend/app/schemas/schemas.py` (new Pydantic models), possibly `backend/app/services/db_service.py`.
- **Migration required**: no.
- **Risk**: low — additive endpoints.
- **Validation commands**: `curl -s http://localhost:8000/api/v1/fixtures/1/events | python -m json.tool`; `make test`.

### v0.7 — Match detail frontend rebuild

- **Goal**: Rewrite `frontend/src/app/matches/[id]/page.tsx` into the 12-section structure above, consuming v0.6 endpoints. Lineup pitch view, event timeline, stats panel, "Where to watch" card, AI intelligence rail, odds tab. No proprietary assets. No monetisation density.
- **Files likely touched**: `frontend/src/app/matches/[id]/page.tsx`, new components under `frontend/src/components/match-detail/`, `frontend/src/lib/types.ts` (new types).
- **Migration required**: no.
- **Risk**: medium — most user-visible change of all versions.
- **Validation commands**: `docker build --target builder -t scorelock-frontend-builder -f frontend/Dockerfile .`; `docker run --rm scorelock-frontend-builder sh -lc "npm run lint && npm run type-check && npm run build"`; manual QA against a seeded fixture.

### v0.8 — Realtime / live event pipeline

- **Goal**: Stand up a `live_ingest` path. First iteration: poll provider every 15s during `IN_PLAY` fixtures, write to `match_events` + `match_statistics`, publish to existing `/api/v1/ws/live` via Redis pub/sub. Frontend's `use-live-scores.ts` starts receiving real events. Push-based provider integration deferred to a sub-version of v0.8 once SportMonks Live Feed is contracted.
- **Files likely touched**: `backend/app/services/tasks.py` (new `refresh_live_fixtures`), `backend/app/api/websocket.py` (wire to Redis channel), `backend/app/core/celery_app.py` (beat entry), possibly new `backend/app/providers/live.py`.
- **Migration required**: no.
- **Risk**: medium — introduces real-time stateful behaviour.
- **Validation commands**: open `/matches/{id}` for a live fixture; observe score / minute ticking from WebSocket in browser DevTools; `docker compose logs celery-worker` showing task success.

### v0.9 — Odds + value movement

- **Goal**: `odds_snapshots` TimescaleDB hypertable; odds polling every 5 min pre-match, every 60s in-play; value-bet detector recomputes on each snapshot; frontend surfaces odds-movement sparkline + next-goal widget per FotMob pattern.
- **Files likely touched**: `backend/migrations/versions/<n>_add_odds_snapshots.py` (new hypertable), `backend/app/services/tasks.py`, `backend/app/api/routes.py` (movement endpoint), `frontend/src/components/match-detail/odds-panel.tsx` (new).
- **Migration required**: yes (TimescaleDB hypertable).
- **Risk**: medium — hypertable behaviour, odds provider rate limits.
- **Validation commands**: `docker compose exec backend alembic upgrade head`; SQL spot-check `SELECT count(*) FROM odds_snapshots WHERE fixture_id = …`; curl movement endpoint.

### v1.0 — Premium demo release

- **Goal**: Public demo at `scorelock.saidborna.com` with: 5 Big-5 leagues + CL/EL/UECL + Allsvenskan (pending Allsvenskan provider coverage), full match-detail at FotMob-level depth, live updates, AI content, TV/broadcast card, value bets with movement, tipping live, Swedish-first with EN toggle, Lighthouse ≥90 on match detail.
- **Files likely touched**: deployment configs (`railway*.json`), `infra/smoke-test.sh`, final README + overview updates.
- **Migration required**: no new migrations; redeploy existing.
- **Risk**: medium — integration risk aggregates across all prior versions.
- **Validation commands**: `infra/smoke-test.sh https://scorelock.saidborna.com` (expect 15/15 green); Lighthouse CLI against `/` and `/matches/{live-fixture-id}`.

## Hard Rules Going Forward

Non-negotiables for the ScoreLock project from v0.4 onward:

1. **No competitor code copying.** Screenshots are for UX reference only. CSS, class names, icon sets, asset URLs, bundle contents from HAR files are off-limits. If it was loaded from `static.flashscore.com`, `prod-cdn-media-api.livescore.com`, `www.sofascore.com`, or `pub.fotmob.com` in our captures, it stays there.
2. **No scraping as a production dependency.** SofaScore's or FotMob's unofficial endpoints are off-limits for production. Competitive intelligence only. All production data must come from licensed providers with a stated ToS.
3. **No UI redesign before metadata model.** v0.5 (schema) blocks v0.7 (UI rebuild). Redesigning a match page without lineups, events, and stats is theatre.
4. **No paid provider integration before provider abstraction.** The abstraction layer (v0.4 design, implementation in a sub-version of v0.5) must land before any SportMonks / API-Football Pro / The Odds API billable work begins. Otherwise we re-couple to a single provider and repeat the football-data.org dependency we're currently in.
5. **No AI insights without normalized event/stat data.** Claude narrative on top of missing lineups = filler. The AI layer feeds from normalized tables, not directly from provider payloads.
6. **No new schema without migration and test plan.** Every new table in v0.5+ ships with an Alembic migration, seeded mock fixtures, and integration tests against the seed. No ad-hoc SQL, no `metadata.create_all()` fallback.
7. **No proprietary rating systems.** Provider ratings (Opta / Stats Perform / SportMonks) only. ScoreLock does not invent a new player-rating scale.
8. **No ad-exchange integrations.** Monetisation stays on affiliate + sponsored widget + subscription. The RTB bidder stack observed on FotMob / LiveScore is not a model we adopt.
9. **No separate mobile codebase.** Responsive Next.js remains the single surface.
10. **No football-data.org free tier as a product assumption beyond v0.4.** It stays as a dev/demo fallback; production depends on paid providers.

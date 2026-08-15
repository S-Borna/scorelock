# ⚽ ScoreLock Football Analytics

**Live:** [scorelock.saidborna.com](https://scorelock.saidborna.com)

AI-driven football analytics SaaS platform delivering match predictions, sentiment analysis, and value bet identification.

## Vision

The most accessible analytics tool for football enthusiasts and semi-professional bettors in the Nordics and Europe.

**Positioning:** Data-driven decision support with ML models — NOT betting advice.

---

## Covered Leagues & Tournaments

### Phase 1 — Launch (Month 1–3)

- 🇬🇧 Premier League
- 🇪🇸 La Liga
- 🇮🇹 Serie A
- 🇩🇪 Bundesliga
- 🇸🇪 Allsvenskan
- 🏆 Champions League / Europa League / Conference League

### Phase 2 — Expansion (Month 4–6)

- 🏆 Euro Qualifiers / Euros
- 🏆 World Cup Qualifiers / World Cup
- 🏆 Copa América
- 🏆 Africa Cup of Nations
- 🏆 Nations League + all qualifier rounds

### Phase 3 — Full Coverage (Month 7+)

- 🇫🇷 Ligue 1, 🇵🇹 Primeira Liga, 🇳🇱 Eredivisie, 🇹🇷 Süper Lig
- More leagues based on user demand

---

## Core Features

| Feature | Description |
|---------|-------------|
| **Match Prediction Engine** | ML model (XGBoost) predicting 1X2, over/under with calibrated probabilities |
| **Value Bet Finder** | Compares model predictions against bookmaker odds to identify value |
| **Sentiment Dashboard** | LLM-driven news/social media sentiment per team and match |
| **Live Dashboard** | Real-time xG timeline, momentum indicator, odds movement |
| **H2H Analyzer** | Deep head-to-head analysis with form curves and tactical data |
| **Allsvenskan Special** | Deeper Swedish football data than any competitor |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python 3.12) |
| **Database** | PostgreSQL 16 + TimescaleDB |
| **Cache** | Redis 7 |
| **Task Queue** | Celery + Redis (12 scheduled tasks) |
| **ML** | scikit-learn, XGBoost |
| **AI Content** | Anthropic Claude (5 article types, Swedish) |
| **Frontend** | Next.js 16 + TypeScript + Tailwind CSS |
| **Realtime** | WebSockets via FastAPI |
| **Infrastructure** | Docker, GitHub Actions, Railway + Cloudflare |
| **Monitoring** | Prometheus + Grafana |
| **Payments** | Stripe |

---

## Revenue Model

| Plan | Price | Includes |
|------|-------|----------|
| **Free** | 0 SEK | 3 match analyses/week, basic tables |
| **Pro** | 149 SEK/month | Unlimited analyses, Value Bet Finder, 5 leagues |
| **Elite** | 299 SEK/month | All leagues, API access, live dashboard, 5yr history |

Plus affiliate revenue from betting site referrals (~$5–15/user/month).

---

## Quick Start

```bash
# Clone
git clone https://github.com/S-Borna/scorelock.git
cd scorelock

# Start everything
docker compose up -d

# Backend API: http://localhost:8000
# Frontend:   http://localhost:3000
# Grafana:    http://localhost:3001
# Redis UI:   http://localhost:8001
```

---

## Project Structure

```
scorelock/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routes
│   │   ├── core/           # Config, security, dependencies
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic & external API clients
│   │   └── ml/             # ML models, training, prediction
│   ├── migrations/         # Alembic database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Next.js app (Phase 2)
├── infra/
│   ├── prometheus.yml
│   └── grafana/
├── .github/workflows/      # CI/CD pipelines
├── docker-compose.yml
├── .env.example
└── Makefile
```

---

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the definitive product roadmap. 8 milestones to launch:

- **M1** ✅ Data pipeline: multi-source APIs (football-data.org + The Odds API + API-Football)
- **M2** ✅ ML predictions: daily predictions, value bets, accuracy tracking
- **M3** ✅ AI Content Engine: match previews, reports, round summaries på svenska
- **M4** ✅ Frontend: article-first design, 14 routes, Swedish, SEO, loading states
- **M5** ✅ Affiliate integration: Bet365, Unibet, Betsson, LeoVegas — CTA, click tracking, disclaimer
- **M6** ✅ Tipping League: AI vs You, leaderboards, social sharing
- **M7** ✅ Deploy + Launch: Railway (allt), Cloudflare, Sentry, GDPR, smoke tests, backups
- **M8** — Distribution: Twitter bot, push notifications, Reddit, Discord, Telegram

**Progress: 67/67 tasks (100% dev)**
> M7 kräver manuell provisioning (Railway, Vercel, Cloudflare, Stripe) — alla configs och scripts finns.

---

## Changelog

### Session 5 — 2026-02-11

**M7 — Deploy + Launch (11/11 ✅)**

- Railway deploy configs: `railway.json` (API med auto `alembic upgrade head`), `railway-worker.json` (Celery worker), `railway-beat.json` (Celery beat), `railway-frontend.json` (Next.js standalone)
- CI/CD pipeline: GitHub Actions → Railway deploy (4 services), smoke test, Sentry release
- Enhanced `/health` endpoint: DB connectivity check (`SELECT 1`), Redis ping, degraded status support
- Sentry error monitoring: backend via `sentry-sdk[fastapi]` (traces, PII-off), frontend via `@sentry/react` (client-only)
  - Anmärkning: `@sentry/nextjs` v8 är inkompatibel med Next.js 16 Turbopack (60s build timeout) — bytt till `@sentry/react`
- Database backup script: `infra/backup-db.sh` (lokal Docker + `--railway` prod-läge), auto-cleanup behåller 10 senaste
- Smoke test script: `infra/smoke-test.sh` testor 15 endpoints, färgkodad output, greppbar exit code
- GDPR-compliance:
  - Cookie consent banner (localStorage, accept/decline, länk till /privacy)
  - Integritetspolicy (`/privacy`) — 9 sektioner, svenska, IMY-hänvisning
  - Användarvillkor (`/terms`) — 12 sektioner, svenska, Spelinspektionen, ansvarsfullt spelande
- Environment variables: komplett `.env.example` + `DEPLOYMENT.toml` med alla prod-secrets
- Makefile: `backup`, `backup-prod`, `smoke-test`, `smoke-test-local` targets
- Bugfix: `prediction-bar.tsx` null-safety för `expected_goals`/`value_edge` (mock data returnerade fixtures istället för predictions)
- Build verifierad: 18 rutter, 0 errors

### Session 4 — 2026-02-11

**M1 — Data Pipeline (10/10 ✅)**

- Integrerat football-data.org som primär datakälla (fixtures + standings)
- Integrerat The Odds API för realtidsodds från 40+ bookmakers
- Smart quota budget system med Redis-counters per API (hard stop vid 90%)
- Uppdaterat Celery Beat: football-data.org primär, API-Football enbart live
- Synk av standings, upcoming fixtures (14 dagar), och odds automatiserad

**M2 — ML Predictions (10/10 ✅)**

- Dagliga prediktioner för upcoming fixtures via `run_daily_predictions`
- Value bet detection med best-odds från 40+ bookmakers + Kelly Criterion
- Accuracy tracking endpoint (`/predictions/accuracy`) med per-liga breakdown
- Auto-retrain quality gate: söndags-task sparar enbart bättre modell
- 5 nya RSS-källor (SVT Sport, Fotbollskanalen, Aftonbladet, UEFA, Transfermarkt)

**M3 — AI Content Engine (9/9 ✅)**

- `articles`-tabell + Alembic-migration (`1f5b8ca20887`)
- `content_generator.py` (738 rader) — Claude-driven, 5 artikeltyper:
  - Match Preview (förhandsanalys med form, H2H, odds, prognos)
  - Match Report (matchreferat med mål, nyckelmoment, tabellpåverkan)
  - Round Summary (omgångens berättelse, hjälte/besvikelse, 800-1200 ord)
  - Value Bet Alert (dagens value bets med motivering)
  - News Rewrite (engelska nyheter → original svensk text)
- 5 nya Celery tasks + Beat-schema (12 totalt)
- Article API endpoints: `GET /articles`, `GET /articles/{slug}` med filter
- Estimerad Anthropic-kostnad: ~$21/månad (~$250/år)

**M4 — Frontend (14/14 ✅)** ⚠️ *MVP-scaffold — designen är funktionell men generisk. Kräver 100x visuell förbättring innan launch (planeras i PL1).*

- Uppgraderat Next.js 14 → 16.1.6 (säkerhetsfix), Turbopack, 0 vulnerabilities
- Mock-data fallback: frontend fungerar utan Docker (offline dev mode)
- Komplett svensk frontend med 14 rutter:
  - `/` — Startsida = artikel-feed (ArticleCard-grid, upcoming matches)
  - `/articles/[slug]` — Artikelsida med ReactMarkdown, SEO, relaterade artiklar
  - `/matches` — Matchlista (kommande + avslutade)
  - `/matches/[id]` — Matchdetalj (prediktion, odds, artiklar, sentiment-sidebar)
  - `/predictions` — Dagens prediktioner
  - `/value-bets` — Value bets med edge + Kelly + ansvarsfull-spelning-varning
  - `/standings` — Ligatabeller med form-indikator
  - `/rounds/[league]/[round]` — Omgångssida med AI-sammanfattning
  - `/sentiment` — Sentimentanalys per lag (score + buzz)
  - `/login`, `/signup` — Auth-flöde på svenska
- SEO: `sitemap.xml`, `robots.txt`, per-sida `<title>` + OG-tags
- Loading states: Skeleton-komponenter per rutt
- Error handling: 404-sida + global-error på svenska
- Komponenter: ArticleCard, MatchCard, PredictionBar, Skeleton
- Build verifierad: 14 rutter, 0 errors
**M5 — Affiliate Integration (6/6 ✅)**
- `affiliate_links` + `affiliate_clicks`-tabeller + Alembic-migration (`3a7c2e1f5d89`)
- 4 svenska bookmakers seedade: Bet365, Unibet, Betsson, LeoVegas (placeholder-URLs)
- 3 backend-endpoints: `GET /affiliate/links`, `POST /affiliate/click`, `GET /admin/affiliate/stats`
- GDPR-compliant klick-tracking: SHA256 IP-hash, user agent, fixture, user (optional)
- `AffiliateCTA`-komponent med 3 varianter: banner, inline, card
- Value bets-sidan: inline CTA per value bet + banner CTA
- Artikelsidor: card CTA för VALUE_BET_ALERT + MATCH_PREVIEW-artiklar
- Matchdetalj: banner CTA + compact disclaimer i sidebar
- `GamblingDisclaimer`-komponent: Stödlinjen (020-819 100), Spelpaus.se, 18+
- Alla affiliate-länkar med `rel="noopener noreferrer nofollow sponsored"` (SEO+legal)
- Admin-endpoint för klickstatistik per bookmaker (total, idag, vecka, månad)
**M6 — Tipping League (7/7 ✅)**
- `user_predictions`-tabell + Alembic-migration (`5b8d3a2f7e91`) med UniqueConstraint(user_id, fixture_id)
- TipForm-komponent: H/D/A-knappar + valfritt exakt resultat, validerar att match ej börjat
- MatchTipSection: auth-wrapper, integrerad i matchdetalj-sidebar
- Poängsystem: 3p exakt resultat, 1p rätt utgång, 0p fel — Celery-task var 15:e minut (14:00–23:00)
- Leaderboard-sida (`/leaderboard`): topplista med poäng, tips, träffsäkerhet, medaljer (🥇🥈🥉)
- "AI vs You"-sida (`/leaderboard/ai-vs-me`): vinster/förluster/lika, detaljerad statistik, jämförelse
- Veckans tippare: 👑-widget på startsidan + leaderboard (namn, poäng, accuracy)
- ShareCard-komponent: 3 varianter (ai-win, leaderboard, streak), Web Share API + clipboard fallback
- Mock data: 8 leaderboard-entries (svenska användarnamn) + weekly top tipper för offline dev
- Build verifierad: 16 rutter, 0 errors

### Session 1–3 — 2026-02-09–10

**M0 — Infrastruktur & Grundplatta**

- Docker Compose med 5 containers (api, db, redis, worker, beat)
- PostgreSQL 16 + TimescaleDB, Alembic-migrationer
- FastAPI backend med 22 endpoints, JWT auth, rate limiting
- 8 ligor + ~300 teams seedade
- XGBoost ML-modell tränad (v20260210-0320, 6 802 samples, 20 features)
- Feature engineering (20-dim vektor), predictor service med Kelly Criterion
- RSS news fetcher (4 engelska källor), sentiment analysis via Claude
- Stripe-integration, WebSocket live updates, CI/CD pipelines
- Next.js frontend scaffold (8 sidor), unit tests (22/22 pass)

---

## License

Proprietary — All rights reserved.

# ScoreLock — Definitive Product Roadmap

> **Version**: 2.0 — Merged from Blueprint, Roadmap v1 & v2
> **Created**: 2026-02-11
> **Owner**: Said Borna (mrebadi)
> **Timeline**: 8 veckor till launch + 4 månader post-launch growth
> **Status**: Active — uppdateras varje session
> **Gäller**: Detta är det ENDA planeringsdokumentet. Alla andra versioner är överflödiga.

---

## 🏁 Progress Tracker

> Uppdateras varje session. ✅ = klar, 🔄 = pågående, ❌ = ej påbörjad.

| Milstolpe | Status | Progress | Nästa steg |
|-----------|--------|----------|------------|
| **M1 — Data Pipeline** | ✅ Komplett | 10/10 tasks | — |
| **M2 — ML Predictions** | ✅ Komplett | 10/10 tasks | — |
| **M3 — AI Content Engine** | ✅ Komplett | 9/9 tasks | — |
| **M4 — Frontend** | ✅ Komplett | 14/14 tasks | — |
| **M5 — Affiliate** | ✅ Komplett | 6/6 tasks | — |
| **M6 — Tipping League** | ❌ Ej påbörjad | 0/7 tasks | Första prio nu! |
| **M7 — Deploy + Launch** | ❌ Ej påbörjad | 0/11 tasks | Väntar på M1–M6 |
| **M8 — Distribution** | ❌ Ej påbörjad | 0/8 tasks | Väntar på M7 |
| **PL1 — Polish** | ❌ Post-launch | — | — |
| **PL2 — Expansion** | ❌ Post-launch | — | — |
| **PL3 — Multi-Sport** | ❌ Post-launch | — | — |
| | | **49/67 tasks** | **~73% total progress** |

---

## 1. Vad ScoreLock Är

ScoreLock är **inte** ett predictions-dashboard. Det är en **AI-driven sportsmedia-
plattform** som gör livescores intelligenta med kontext, berättelse, value och prognos.

### Produktidentitet

De flesta betting-verktyg visar en tabell:

```
Arsenal vs Chelsea  |  H: 52%  D: 24%  A: 24%  |  Value: Home @ 1.95
```

ScoreLock ger istället:

> **Arsenal vs Chelsea — Söndagens stormatch**
>
> Arsenal har vunnit fyra raka hemma och släppt in bara två mål.
> Chelsea saknar Palmer och Caicedo. Historiskt har Arsenal tagit
> 7 av 9 poäng i de senaste hemmadrabbningarna. Med odds 1.95 på
> hemmaseger — där vår modell ger 52% sannolikhet mot bookmakers
> implicita 51% — finns det ett litet edge, men formkurvan talar
> ännu starkare för Arsenal.
>
> **ScoreLocks prognos: Arsenal 2–1 Chelsea**
> [Se bästa oddsen hos Unibet →](#affiliate-link)

**Siffror + kontext + berättelse + affiliate-länk.** Varje artikel är en SEO-sida
som drar organisk trafik.

### Konkurrenternas Svagheter → Vår Edge

| Konkurrent | Vad de har | Vad de saknar | ScoreLock-edge |
|------------|-----------|---------------|----------------|
| Flashscore | Livescores, bred täckning | Noll kontext, noll content | AI-artiklar + value analysis |
| FotMob | Vacker UI, djup statistik | Ingen betting-insight, ingen content | ML-prediktion + odds-analys |
| SofaScore | Bra data, xG | Ingen betting, ingen sentiment | Value bets + sentiment + artiklar |
| Understat | Avancerad xG | Ingen live, ingen mobil, ingen content | Allt ovan + live + mobile |
| BetExplorer | Odds-historik | Ingen analys, ingen content | ML-overlay + AI-analys |
| Bettingsidor | Odds | Partiska — de tjänar på att du förlorar | Oberoende, data-driven analys |
| Tipsbladet/Stryktipset | Manuella tips | Långsamt, ytligt, begränsat | AI = snabbare, djupare, 100% auto |

**ScoreLock har ALLT konkurrenterna har (livescores, standings, odds, xG) PLUS allt
de saknar (AI-content, value detection, sentiment analysis, affiliate-neutral analys).**

### Målgrupp

| Segment | De vill ha | Via ScoreLock |
|---------|-----------|---------------|
| Fotbollsfans | Matchreferat, omgångskoll | AI-skrivna artiklar på svenska, gratis |
| Fantasy-managers | Form, H2H, skadeinfo | Predictions + sentiment + data |
| Semi-professionella bettare | Kalibrerade sannolikheter + value | Value Bet Finder + Kelly Criterion |
| Casual-läsare | Underhållande content | SEO-indexerade artiklar i deras feed |

---

## 2. Intäktsmodell: Affiliate First, Premium Later

### Primär: Affiliate (gratis för användaren)

**ALLT content är gratis.** Affiliate betalar — inte användaren.

| Intäktskälla | Per-event | Beskrivning |
|-------------|-----------|-------------|
| CPA (Cost Per Acquisition) | $50–200 | Ny kund registrerar sig hos bettingbolag via vår länk |
| Revenue Share | 20–35% | Löpande andel av kundens förluster hos bettingbolaget |
| Odds-jämförelselänkar | $0.50–2.00/klick | Klick på "Bästa odds hos..." |

**Räkneexempel** vid 10 000 månatliga besökare:
5% klickar affiliate-länk = 500 klick → 10% registrerar = 50 kunder →
50 × $100 CPA = **$5 000/mån** + löpande rev share.

### Sekundär: Premium-tier (framtida)

Stripe-integration redan byggd. Aktiveras när det finns användare som vill betala
för extra funktioner.

| Plan | Pris | Inkluderar |
|------|------|------------|
| **Free** | 0 SEK | Allt content, alla artiklar, basic predictions |
| **Pro** | 149 SEK/mån | Tipping league, advanced filters, notification alerts |
| **Elite** | 299 SEK/mån | API-access, live dashboard, 5-årig historik, prioriterad support |

### Break-Even

| Modell | Break-even |
|--------|-----------|
| Affiliate CPA ($100/konvertering) | 1 konvertering/mån täcker drift |
| Premium-prenumeration | 3–5 betalande användare |
| **Driftskostnad** | **$46–100/mån** (se kostnadssektion) |

---

## 3. Nuläge — Exakt vad som är byggt (2026-02-11)

### ✅ Fungerar (byggt Session 1–3)

| Komponent | Status | Session | Detalj |
|-----------|--------|---------|--------|
| Docker infrastructure | ✅ Running | S1 | 5 containers: api, db, redis, worker, beat — alla healthy |
| PostgreSQL 16 + TimescaleDB | ✅ Running | S1 | 9 tabeller, Alembic-migrerade |
| Historisk data | ✅ Loaded | S2 | 7 638 fixtures, ~300 teams, 8 ligor (2022–2024) |
| FastAPI backend | ✅ Running | S1 | 22 endpoints, CORS, health check |
| JWT authentication | ✅ Working | S1 | Register, login, bcrypt, 30-min tokens |
| Rate limiting | ✅ Active | S3 | Redis sliding window: anon=20, free=30, pro=120, elite=300 req/min |
| XGBoost ML-modell | ✅ Trained | S2 | v20260210-0320, 6 802 samples, 20 features, accuracy 48.6% |
| Feature engineering | ✅ Complete | S2 | 20-dim vektor: form, H2H, season stats, rest days, home/away |
| Predictor service | ✅ Working | S2 | Singleton, predict + value bets + Kelly Criterion |
| Celery + Beat | ✅ Running | S1 | 7 schemalagda tasks (fixad kvothantering S3) |
| RSS News Fetcher (4 EN) | ✅ Working | S3 | BBC, Guardian, ESPN, Sky Sports — testad, 15 artiklar/team |
| Sentiment analysis | ✅ Working | S3 | Anthropic Claude + news_fetcher, strukturerad JSON-output |
| Stripe integration | ✅ Coded | S3 | Checkout, portal, webhook — behöver price IDs + prod URL |
| WebSocket live updates | ✅ Coded | S3 | Redis pub/sub → WS broadcast, behöver resilience |
| CI/CD pipelines | ✅ Configured | S3 | GitHub Actions: lint, test, Docker build, Railway deploy |
| Frontend scaffold | ✅ Created | S3 | Next.js 14 + TypeScript + Tailwind, 8 pages — ej npm installed |
| Admin trigger endpoint | ✅ Working | S3 | POST /admin/trigger/{task} med auth + whitelist |
| Unit tests | ✅ Passing | S1–3 | 22/22 pass |
| **Totalt byggt** | | **S1–S3** | **~18 komponenter, 26+ filer, 3 sessioner** |

### ❌ Saknas — nödvändigt för launch

| Gap | Blockerar |
|-----|-----------|
| **Affiliate-integration** | Noll intäkter |
| **Tipping League** | Retention + viralt / social loop |
| Production deployment | Ingen publik site |
| Distribution | Inga användare |
| GDPR-compliance | Cookie consent, privacy policy |

---

## 4. Datakällor — Fler API:er, Sluta Vara API-Football-beroende

### Nuvarande: Bara API-Football (100 req/dag) — RISKABELT

### Plan: 3 sport-API:er + 1 odds-API + 9 RSS-sources

| Källa | Gratis tier | Vad den ger | Prioritet |
|-------|------------|-------------|-----------|
| **API-Football** (har redan) | 100 req/dag | Fixtures, live scores, odds | Primär |
| **football-data.org** (NYTT) | 10 req/min = 14 400/dag | PL, La Liga, Serie A, BL, Ligue 1, CL | Komplement — löser kvotaproblemet |
| **TheSportsDB** (NYTT) | Obegränsat | Team-metadata, logos, stadiums | Komplement |
| **The Odds API** (NYTT) | 500 req/mån | Realtidsodds från 40+ bookmakers | Value bet-data |

| RSS-källa | Språk | Status |
|-----------|-------|--------|
| BBC Sport Football | EN | ✅ Implementerad |
| The Guardian Football | EN | ✅ Implementerad |
| ESPN Football | EN | ✅ Implementerad |
| Sky Sports Football | EN | ✅ Implementerad |
| **SVT Sport** | SV | ❌ Att bygga |
| **Fotbollskanalen** | SV | ❌ Att bygga |
| **Aftonbladet Sport** | SV | ❌ Att bygga |
| **Transfermarkt News** | EN/DE | ❌ Att bygga |
| **UEFA** | EN | ❌ Att bygga |

### API-kvotastrategi (100 req/dag API-Football + 14 400 football-data.org)

| Operation | Källa | Dagliga calls | Prioritet |
|-----------|-------|---------------|-----------|
| Fixtures sync | football-data.org | ~50 | 1 — Kritisk |
| Standings sync | football-data.org | ~20 | 2 — Hög |
| Odds sync | The Odds API | ~15/mån | 3 — Hög |
| Live scores (matchdagar) | API-Football | ~30 | 4 — Matchdagar |
| Team metadata | TheSportsDB | On-demand | 5 — Låg |
| **API-Football reserv** | API-Football | **70 kvar** | Buffer |

**Regel**: football-data.org för daglig data. API-Football ENBART för live scores
och som fallback. Aldrig bränn hela kvoten på scheduled tasks igen.

---

## 5. Content Engine — Det som gör oss unika

### Content-typer

| Typ | Frekvens | Trigger | Auto-grad |
|-----|----------|---------|-----------|
| **Match Preview** | Per match (~380/säsong) | Dagen före match | 100% auto |
| **Match Report** | Per match (~380/säsong) | 2h efter match | 100% auto |
| **Round Summary** | Per omgång (~38/säsong) | Efter omgångens sista match | 100% auto |
| **Value Bet Alert** | Dagligen | 06:00 UTC varje matchdag | 100% auto |
| **News Rewrite** | Löpande | Vid ny RSS-artikel | 90% auto |
| **Transfer News** | Löpande | Via Transfermarkt RSS | 90% auto |
| **Djupanalys** | Veckovis | Manuell vinkel | 50% auto |

### Automatisk Content Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                    CONTENT GENERATION FLOW                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Dag före match:                                                 │
│    1. Hämta form, H2H, standings, odds, skador via API           │
│    2. Hämta nyheter via RSS (alla 9 feeds)                       │
│    3. Claude API → Match Preview (svenska, 400-600 ord)          │
│    4. Spara i articles-tabell → publicera på frontend             │
│                                                                  │
│  Matchdag:                                                       │
│    5. Value Bet Alert — dagens top 3 value bets i artikelform    │
│                                                                  │
│  Efter match:                                                    │
│    6. Hämta resultat, statistik, events                          │
│    7. Claude API → Match Report (300-500 ord)                    │
│                                                                  │
│  Efter omgång:                                                   │
│    8. Claude API → Round Summary (800-1200 ord)                  │
│       - Omgångens hjälte, besvikelse, tabellanalys               │
│       - Förhandsblick nästa omgång                                │
│                                                                  │
│  Löpande:                                                        │
│    9. RSS → Claude → News Rewrite (engelsk → svensk)             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Artikelvolym per säsong (alla 8 ligor)

| Typ | Per liga | × 8 ligor | Per säsong |
|-----|---------|-----------|------------|
| Match Previews | ~190 | ×8 | ~1 520 |
| Match Reports | ~190 | ×8 | ~1 520 |
| Round Summaries | ~38 | ×8 | ~304 |
| Value Bet Alerts | ~190 | — | ~190 |
| News Rewrites | ~50 | — | ~300 |
| **TOTALT** | | | **~3 834 unika URL:er/säsong** |

**3 800+ SEO-indexerbara sidor per säsong = massiv organisk trafik.**

---

## 6. Milstolpar — 8 veckor till launch

### M1 — DATA FLÖDAR (3 dagar)
>
> *Databasen har aktuell, automatiskt uppdaterad data från flera API:er.*

| # | Task | Definition of Done | Beroende | Status |
|---|------|-------------------|----------|--------|
| 1.0 | ~~Historisk data (3 säsonger, 8 ligor)~~ | ~~7 638 fixtures i DB~~ | — | ✅ Klar (Session 2) |
| 1.0b | ~~Ligor + teams seedade~~ | ~~8 ligor, ~300 teams~~ | — | ✅ Klar (Session 1) |
| 1.0c | ~~API-Football klient~~ | ~~`api_football.py` fungerar~~ | — | ✅ Klar (Session 1) |
| 1.1 | ~~Integrera football-data.org API-klient~~ | ~~`football_data.py` i services, hämtar fixtures + standings~~ | — | ✅ Klar (Session 4) |
| 1.2 | ~~Registrera konto + API-nyckel The Odds API~~ | ~~`odds_api.py` klient, nyckel i `.env`~~ | — | ✅ Klar (Session 4) |
| 1.3 | ~~Synka standings (alla 8 ligor)~~ | ~~football-data.org primary, API-Football fallback~~ | 1.1 | ✅ Klar (Session 4) |
| 1.4 | ~~Synka upcoming fixtures (14 dagar framåt)~~ | ~~football-data.org 14d + API-Football för unsupported~~ | 1.1 | ✅ Klar (Session 4) |
| 1.5 | ~~Synka odds via The Odds API~~ | ~~40+ bookmakers, h2h + totals, best-odds tracking~~ | 1.2 + 1.4 | ✅ Klar (Session 4) |
| 1.6 | ~~Uppdatera Celery Beat~~ | ~~football-data.org primary, API-Football bara live, odds 2x/dag~~ | 1.1 | ✅ Klar (Session 4) |
| 1.7 | ~~Smart quota budget system~~ | ~~Redis-counter per API, hard stop vid 90%, admin endpoint~~ | — | ✅ Klar (Session 4) |

**Historisk data**: ✅ Redan laddad (7 638 fixtures, 2022–2024). Ingen backfill behövs.

**Exit Criteria**: Standings, fixtures, och odds finns i DB. Celery Beat synkar automatiskt.

---

### M2 — ML PREDIKTIONER LEVERERAR (3 dagar)
>
> *Dagliga prediktioner + value bets + accuracy tracking.*

| # | Task | Definition of Done | Beroende | Status |
|---|------|-------------------|----------|--------|
| 2.0 | ~~XGBoost modell tränad~~ | ~~v20260210-0320, 6 802 samples, Brier 0.24~~ | — | ✅ Klar (Session 2) |
| 2.0b | ~~Feature engineering (20 features)~~ | ~~Form, H2H, season, rest, home/away~~ | — | ✅ Klar (Session 2) |
| 2.0c | ~~Predictor service (singleton)~~ | ~~`predictor.py` med predict + value bets~~ | — | ✅ Klar (Session 2) |
| 2.0d | ~~RSS News Fetcher (4 EN-källor)~~ | ~~BBC, Guardian, ESPN, Sky Sports~~ | — | ✅ Klar (Session 3) |
| 2.0e | ~~Sentiment Analyzer (Claude)~~ | ~~`sentiment.py` med structured JSON output~~ | — | ✅ Klar (Session 3) |
| 2.1 | ~~Generera predictions för upcoming fixtures~~ | ~~`run_daily_predictions` task kör 2x/dag, fyller predictions-tabellen~~ | M1.4 | ✅ Klar (Session 4) |
| 2.2 | ~~Value bet detection med The Odds API-data~~ | ~~Best-odds across 40+ bookmakers, edge + Kelly~~ | M1.5 + 2.1 | ✅ Klar (Session 4) |
| 2.3 | ~~Accuracy tracking endpoint~~ | ~~`/predictions/accuracy` med per-liga, per-modell, value bet stats~~ | 2.1 | ✅ Klar (Session 4) |
| 2.4 | ~~Verifiera weekly auto-retrain~~ | ~~Söndags-task jämför ny vs gammal modell, sparar bara om bättre~~ | — | ✅ Klar (Session 4) |
| 2.5 | ~~Sentiment analysis med svenska RSS~~ | ~~SVT Sport, Fotbollskanalen, Aftonbladet + UEFA, Transfermarkt~~ | — | ✅ Klar (Session 4) |

**ML-modell**: ✅ Redan tränad (v20260210-0320, 6 802 samples, 20 features, Brier 0.24).
**Feature engineering**: ✅ Redan komplett (20-dim vektor).
**RSS-aggregator**: ✅ Redan fungerar (4 engelska källor) — behöver utökas med 5 till.

**Exit Criteria**: `/api/v1/predictions/today` returnerar prediktioner. `/api/v1/value-bets` returnerar value bets med odds från 40+ bookmakers.

---

### M3 — AI CONTENT ENGINE (7 dagar) ⭐ USP:EN
>
> *Plattformen genererar original-artiklar på svenska. Utan detta är vi bara siffror.*

| # | Task | Definition of Done | Beroende | Status |
|---|------|-------------------|----------|--------|
| 3.1 | ~~`articles`-tabell + Alembic-migration~~ | ~~Kolumner: type, league_id, fixture_id, slug, title, body, summary, tags, language, published_at, auto_generated~~ | — | ✅ Klar (Session 4) |
| 3.2 | ~~Article Generator service (`content_generator.py`)~~ | ~~Claude API-integration med prompt-templates per artikeltyp, 738 rader~~ | — | ✅ Klar (Session 4) |
| 3.3 | ~~**Match Preview Generator**~~ | ~~AI skriver förhandsanalys: form, H2H, skador, tabell, prognos med motivering (400-600 ord, svenska)~~ | M2 + 3.2 | ✅ Klar (Session 4) |
| 3.4 | ~~**Match Report Generator**~~ | ~~AI skriver matchreferat: mål, nyckelmoment, tabellpåverkan (300-500 ord, svenska)~~ | M1 + 3.2 | ✅ Klar (Session 4) |
| 3.5 | ~~**Round Summary Generator**~~ | ~~Omgångens berättelse: hjälte, besvikelse, tabellanalys, förhandsblick (800-1200 ord, svenska)~~ | M1 + 3.2 | ✅ Klar (Session 4) |
| 3.6 | ~~**Value Bet Article Generator**~~ | ~~AI analyserar dagens value bets: odds, fair prob, edge, motivering + disclaimer (300-400 ord)~~ | M2 + 3.2 | ✅ Klar (Session 4) |
| 3.7 | ~~**News Rewriter**~~ | ~~Engelska RSS-artiklar omskrivs till original svensk text (ej översättning — omskrivning)~~ | 3.2 | ✅ Klar (Session 4) |
| 3.8 | ~~Celery tasks för content-generation~~ | ~~5 tasks + Beat-schema: previews (dag före), reports (2h efter), roundups (söndag), value bets (dagligen), news rewrites (var 4h)~~ | 3.3–3.7 | ✅ Klar (Session 4) |
| 3.9 | ~~Article API endpoints~~ | ~~`GET /articles`, `GET /articles/{slug}`, filter: `?type=&league_id=&round=&language=`~~ | 3.1 | ✅ Klar (Session 4) |

**Automatiskt schema:**

```
Dagen före match  →  Match Preview publiceras
06:00 matchdag    →  Value Bet Alert publiceras
2h efter match    →  Match Report publiceras
Efter sista match →  Round Summary publiceras
Löpande           →  News Rewrites vid nya RSS-artiklar
```

**Exit Criteria**: Artiklar genereras automatiskt och är läsbara på svenska. Minst 5 artiklar av varje typ genererade och verifierade.

---

### M4 — FRONTEND LEVER (7 dagar)
>
> *Användare ser artiklar, prediktioner och data — inte bara siffror.*

| # | Task | Definition of Done | Beroende | Status |
|---|------|-------------------|----------|--------|
| 4.1 | ~~`npm install` + dev server fungerar~~ | ~~Next.js 16.1.6, Turbopack, `localhost:3000` — 0 vulnerabilities~~ | — | ✅ Klar (Session 4) |
| 4.2 | ~~**Startsida = artikel-feed**~~ | ~~ArticleCard-grid (featured first), upcoming matches, feature cards — allt på svenska~~ | M3 | ✅ Klar (Session 4) |
| 4.3 | ~~**Artikelsida** `/articles/[slug]`~~ | ~~ReactMarkdown body, SEO metadata, relaterade artiklar, fixture-länk, value bet CTA~~ | M3 | ✅ Klar (Session 4) |
| 4.4 | ~~**Matchlista** `/matches`~~ | ~~Kommande + avslutade med svenska etiketter~~ | M2 | ✅ Klar (Session 4) |
| 4.5 | ~~**Matchdetalj** `/matches/[id]`~~ | ~~Prediktion, odds, relaterade artiklar, sentiment-sidebar, svenska~~ | M2 + M3 | ✅ Klar (Session 4) |
| 4.6 | ~~**Value Bets** `/value-bets`~~ | ~~Edge %, Kelly, modell-sannolikhet, ansvarsfull-spelning-varning~~ | M2 | ✅ Klar (Session 4) |
| 4.7 | ~~**Standings** `/standings`~~ | ~~Ligatabell per liga, form-indikator, svenska kolumnnamn~~ | M1 | ✅ Klar (Session 4) |
| 4.8 | ~~**Omgångssida** `/rounds/[league]/[round]`~~ | ~~Alla matcher + AI round summary-artikel, breadcrumbs~~ | M3 | ✅ Klar (Session 4) |
| 4.9 | ~~**Sentiment-dashboard** `/sentiment`~~ | ~~Per-team sentiment + buzz per liga, bar-visualisering, AI-summaries~~ | M2.5 | ✅ Klar (Session 4) |
| 4.10 | ~~Responsiv design~~ | ~~Mobile hamburger-meny, grid-breakpoints, mobile-first~~ | 4.2–4.9 | ✅ Klar (Session 4) |
| 4.11 | ~~SEO~~ | ~~Unika `<title>`, `<meta>`, OG-tags, `sitemap.xml`, `robots.txt` per sida~~ | 4.3 | ✅ Klar (Session 4) |
| 4.12 | ~~Auth-flöde~~ | ~~Login + signup på svenska, validation, auto-login efter registrering~~ | — | ✅ Klar (Session 4) |
| 4.13 | ~~Loading + error states~~ | ~~Skeleton loaders per rutt, 404-sida, global-error, empty states~~ | 4.2–4.9 | ✅ Klar (Session 4) |
| 4.14 | ~~Branding~~ | ~~OG-bild, meta-tags, favicon, `lang="sv"`, professionellt intryck~~ | — | ✅ Klar (Session 4) |

**Exit Criteria**: En icke-teknisk person kan öppna sajten, läsa artiklar, se prediktioner
och standings, och förstå vad ScoreLock är — på mobil och desktop.

---

### M5 — AFFILIATE-INTEGRATION (3 dagar)
>
> *Varje value bet och odds-jämförelse genererar intäkter.*

| # | Task | Definition of Done | Beroende | Status |
|---|------|-------------------|----------|--------|
| 5.1 | ~~Ansök till affiliate-program~~ | ~~Bet365, Unibet, Betsson, LeoVegas — seedade med placeholder-URLs~~ | — | ✅ Klar (Session 4) |
| 5.2 | ~~Affiliate-länk-system i backend~~ | ~~`affiliate_links` + `affiliate_clicks` tabeller, 3 API-endpoints, Alembic-migration~~ | 5.1 | ✅ Klar (Session 4) |
| 5.3 | ~~"Bästa odds hos X" på value bets-sidan~~ | ~~AffiliateCTA inline per value bet + banner, klick-tracking~~ | 5.2 + M4.6 | ✅ Klar (Session 4) |
| 5.4 | ~~Affiliate-länkar i artiklar~~ | ~~AffiliateCTA card-variant i VALUE_BET_ALERT + MATCH_PREVIEW-artiklar~~ | 5.2 + M4.3 | ✅ Klar (Session 4) |
| 5.5 | ~~Klick-tracking~~ | ~~POST /affiliate/click med IP-hash (SHA256), user agent, fixture, user — GDPR-compliant~~ | 5.2 | ✅ Klar (Session 4) |
| 5.6 | ~~Disclaimer~~ | ~~GamblingDisclaimer-komponent med Stödlinjen + Spelpaus.se + 18+, på value bets, artiklar, matchsidor~~ | 5.3 | ✅ Klar (Session 4) |

**Exit Criteria**: Affiliate-länkar syns i value bets och artiklar. Klick loggas.
Spelansvarsdisclaimer visas.

---

### M6 — TIPPING LEAGUE (5 dagar)
>
> *Användare tävlar mot varandra och mot AI:n. Retention + viralt.*

| # | Task | Definition of Done | Beroende | Status |
|---|------|-------------------|----------|--------|
| 6.1 | `user_predictions`-tabell | User kan tippa H/D/A + exakt resultat per match | M4 | ❌ |
| 6.2 | Tipping UI | Klick på match → välj prognos → sparas via API | 6.1 | ❌ |
| 6.3 | Poängsystem | 3p rätt resultat, 1p rätt utgång, streak-bonus | 6.1 | ❌ |
| 6.4 | Leaderboard `/leaderboard` | Topplista: poäng, streak, accuracy % | 6.3 | ❌ |
| 6.5 | "AI vs You" | Visa hur användaren står sig mot ML-modellen | 6.4 + M2 | ❌ |
| 6.6 | Veckans tippare | Highlight på startsidan | 6.4 | ❌ |
| 6.7 | Sociala delnings-cards | Delningsbara bilder: "Jag slog AI:n 7 av 10!" | 6.5 | ❌ |

**Exit Criteria**: Användare kan tippa, se leaderboard, jämföra sig med AI.
Delningsfunktion fungerar.

---

### M7 — DEPLOY + LAUNCH (5 dagar)
>
> *scorelock.saidborna.com är live.*

| # | Task | Definition of Done | Beroende | Status |
|---|------|-------------------|----------|--------|
| 7.1 | Railway deploy: backend + worker + beat | FastAPI + Celery live, health check OK | M1–M6 | ❌ |
| 7.2 | Railway: PostgreSQL + Redis | Managed services provisioned, migrerade | 7.1 | ❌ |
| 7.3 | Frontend deploy (Vercel eller Cloudflare Pages) | Next.js SSR live, API proxy konfigurerad | 7.1 | ❌ |
| 7.4 | Custom domain `scorelock.saidborna.com` | DNS via Cloudflare, HTTPS enforced, SSL Full (Strict) | 7.1 | ❌ |
| 7.5 | Stripe webhook i produktion | Live URL i Stripe dashboard, events verifierade | 7.4 | ❌ |
| 7.6 | Environment variables i prod | Alla secrets i Railway dashboard, `.env` ej deployed | 7.1 | ❌ |
| 7.7 | Error monitoring (Sentry) | Fångar obehandlade exceptions, skickar alerts | 7.1 | ❌ |
| 7.8 | Monitoring (Prometheus + Grafana) | Request latency, error rate, API-kvota, prediction accuracy | 7.1 | ❌ |
| 7.9 | Database backup | Railway auto-backup + manuell pg_dump varje vecka | 7.2 | ❌ |
| 7.10 | Production smoke test | Hela flödet end-to-end: browse → läsa artikel → se prediction → tippa match | 7.1–7.9 | ❌ |
| 7.11 | GDPR-compliance | Cookie consent banner, privacy policy, terms of service, "reklamlänk"-märkning | 7.3 | ❌ |

**Exit Criteria**: `scorelock.saidborna.com` laddar, visar riktiga artiklar och data,
tar emot användare. CD fungerar. Errors fångas. GDPR OK.

---

### M8 — DISTRIBUTION & SOFT LAUNCH (löpande från vecka 7)
>
> *Användare hittar ScoreLock.*

| # | Task | Definition of Done | Beroende | Status |
|---|------|-------------------|----------|--------|
| 8.1 | Twitter/X bot | Automatiska match-previews + value bet alerts 2h före avspark | M3 + M7 | ❌ |
| 8.2 | Reddit-strategi | Dela analyser i r/premierleague, r/soccer, r/soccerbetting, r/Allsvenskan | M7 | ❌ |
| 8.3 | Discord-community | Egen server med channels per liga, bot som postar predictions | M7 | ❌ |
| 8.4 | Telegram-kanal | Bot som postar value bet alerts dagligen | M3 + M7 | ❌ |
| 8.5 | Push-notiser (OneSignal) | "Value bet alert: Arsenal ML @2.10" → browser + mobile push | M7 | ❌ |
| 8.6 | Soft launch (50 beta-användare) | Rekrytera via Reddit, Discord, LinkedIn | 8.1–8.5 | ❌ |
| 8.7 | Public launch | Product Hunt + content marketing + social | 8.6 | ❌ |
| 8.8 | Delningsbara prediction cards | Grafiska bilder med prognos, genererade per match | M4 | ❌ |

**Exit Criteria**: Minst 3 distributionskanaler aktiva. 50+ beta-användare. Trafik
börjar komma organiskt.

---

## 7. Tidslinje

```
Vecka 1      Vecka 2      Vecka 3       Vecka 4      Vecka 5     Vecka 6     Vecka 7-8
  │            │             │             │            │           │            │
  ▼            ▼             ▼             ▼            ▼           ▼            ▼
┌─────┐   ┌─────┐   ┌───────────┐   ┌─────────┐  ┌─────┐   ┌─────┐   ┌──────────┐
│ M1  │──▶│ M2  │──▶│    M3     │──▶│   M4    │─▶│ M5  │──▶│ M6  │──▶│  M7+M8   │
│Data │   │ ML  │   │ CONTENT ⭐ │   │FRONTEND │  │Affil│   │Tipp │   │ LAUNCH   │
│3 d  │   │3 d  │   │   7 d     │   │  7 d    │  │3 d  │   │5 d  │   │  5+∞ d   │
└─────┘   └─────┘   └───────────┘   └─────────┘  └─────┘   └─────┘   └──────────┘
                           │
                    UTAN DETTA ÄR VI
                    BARA YTTERLIGARE
                    ETT ODDS-VERKTYG
```

---

## 8. Post-Launch Roadmap (Månad 3–6)

### PL1 — Polish & Quality (vecka 9–12)

| Task | DoD | Status |
|------|-----|--------|
| E2E-tester (Playwright) | 10+ kritiska user flows testade | ❌ |
| Integration tests för Celery tasks | Mockade API-svar | ❌ |
| Performance: LCP <2s, API p95 <200ms | Lighthouse 90+ | ❌ |
| Accessibility (WCAG 2.1 AA) | Tangentbordsnavigation, skärmläsare, kontrast | ❌ |
| Security hardening | CSP headers, dependency audit, CSRF | ❌ |
| WebSocket resilience | Auto-reconnect, heartbeat, graceful degradation | ❌ |
| ML model monitoring | Accuracy-trend, auto-retrain om accuracy <45% | ❌ |

### PL2 — Expansion (vecka 13–20)

| Task | DoD | Status |
|------|-----|--------|
| **Ligue 1 + Eredivisie + Primeira Liga** | 3 nya ligor med historik + predictions | ❌ |
| **Tournament: CL/EL/ECL gruppspel + slutspel** | Tabelläge, matcher, predictions | ❌ |
| **Allsvenskan deep dive** | Extra detaljerade artiklar, spelarscout, säsongsanalys | ❌ |
| i18n: Svenska + Engelska | Språkväljare, allt content på båda språk | ❌ |
| Email-notifikationer | Matchday alerts, prediction results, value bet alerts | ❌ |
| Admin dashboard | User management, revenue tracking, content stats, API usage | ❌ |
| PWA | Installable, offline support för lästa artiklar | ❌ |

### PL3 — Multi-Sport (månad 6+)

| Sport | API | Motivation |
|-------|-----|------------|
| **NHL** | NHL API (gratis, obegränsat) | MakeThePlay-synergi, enorm NA-marknad |
| **NBA** | Balldontlie (30 req/min, gratis) | Stor global marknad |
| Tennis Grand Slams | Framtida | Per-demand |
| UFC/MMA | Framtida | Per-demand |
| F1 | Framtida | Per-demand |

---

## 9. Allsvenskan Special (löpande från M3)

| Feature | Beskrivning |
|---------|-------------|
| Djupare artiklar | Mer detaljerad omgångsanalys än toppligorna |
| Spelarscout | Unga spelare, marknadsvärde, transferrykten |
| Svenska som förstaspråk | All content genereras primärt på svenska |
| Dedikerade RSS-feeds | Fotbollskanalen + SVT Sport + Aftonbladet |
| Säsongsanalys-serie | "Vägen till guld" — löpande AI-driven berättelse |
| Superettan/Division 1 (framtida) | Djupare pyramid om det finns efterfrågan |

---

## 10. Kostnadskalkyl

| Post | Månad 1–2 | Månad 3+ (med trafik) |
|------|-----------|----------------------|
| API-Football (Free) | $0 | $0 |
| football-data.org (Free) | $0 | $0 |
| The Odds API (Free) | $0 | $0 |
| Railway hosting (5 services) | $20 | $20–50 |
| Anthropic API (artiklar) | $5–15 | $15–30 |
| Cloudflare + domain | ~$2 | ~$2 |
| OneSignal (push) | $0 | $0 (gratis <10k) |
| **Totalt** | **~$27–37/mån** | **~$37–82/mån** |

**Break-even (affiliate)**: 1 konvertering × $100 CPA = $100 > $37 kostnad → **dag 1**.

---

## 11. Riskregister

| Risk | Sannolikhet | Impact | Mitigering |
|------|------------|--------|------------|
| API-Football ändrar priser/limits | Medel | Hög | football-data.org som primär + TheSportsDB som fallback |
| ML-modell accuracy sjunker | Medel | Medel | Auto-retrain pipeline, accuracy monitoring, threshold alerts |
| Stripe-buggar → förlorade betalningar | Låg | Kritisk | Webhook idempotency, test mode, logging |
| API-kvota bränns | Hög | Hög | Multi-source strategi, hard limits, budget system |
| Burnout (solo-utvecklare) | Medel | Hög | AI-agenter gör bulk-implementation, fokus på review |
| Konkurrent lanserar samma produkt | Medel | Medel | Speed to market + nordisk nisch + Allsvenskan focus |
| GDPR/spellagar-regulation | Låg | Hög | Privacy policy, cookie consent, "reklamlänk"-märkning, Stödlinjen |
| Anthropic API-priset ökar | Låg | Medel | Cache genererade artiklar, alternativ: OpenAI, Mistral |
| Affiliate-program nekar ansökan | Medel | Hög | Sök till 4+, minst 1 bör godkännas; fallback till Stripe premium |

---

## 12. Beslutslogg

| Datum | Beslut | Motivering |
|-------|--------|-----------|
| 2026-02-09 | PostgreSQL + TimescaleDB | Time-series för odds/scores, hyper-tables för framtida skalning |
| 2026-02-09 | FastAPI framför Django | Async-native, lättare, bättre WebSocket-stöd |
| 2026-02-09 | Redis: cache + broker + pub/sub | En dependency för tre syften |
| 2026-02-10 | XGBoost framför neural nets | Tolkbart, snabb träning, fungerar bra med tabular data |
| 2026-02-10 | Direkt bcrypt istället för passlib | passlib har olöst bcrypt-kompatibilitetsproblem |
| 2026-02-11 | Anthropic Claude för content | Bäst på svenska, billigast per token vs kvalitet |
| 2026-02-11 | RSS-feeds istället för Twitter API | Twitter/X API kostar pengar; RSS är gratis och pålitligt |
| 2026-02-11 | Stanna på API-Football Free | Supplement med football-data.org istället för att betala |
| 2026-02-11 | Railway + Cloudflare Pages | Enklast för solo-dev; kan migrera till AWS/GCP senare |
| 2026-02-11 | Affiliate first, Premium later | Content bör vara gratis för SEO; affiliate betalar |
| 2026-02-11 | Multi-source API-strategi | Aldrig vara beroende av en enda datakälla |
| 2026-02-11 | Content-plattform, inte dashboard | Artiklar + berättelser differentierar oss; siffror har alla |

---

## 13. KPI:er & Success Metrics

### Launch (vecka 8)

| Metric | Target |
|--------|--------|
| Site live på `scorelock.saidborna.com` | ✅ |
| AI-artiklar genereras automatiskt | ✅ |
| Value bets med affiliate-länkar | ✅ |
| Sida laddar <2s (LCP) | ✅ |
| 50+ beta-användare | ✅ |

### Månad 3

| Metric | Target |
|--------|--------|
| Månatliga besökare | ≥ 500 |
| Artikel-SEO-indexering | ≥ 100 sidor i Google |
| Affiliate-klick | ≥ 200/mån |
| Affiliate-konverteringar | ≥ 5 |
| Prediction accuracy | ≥ 48% |
| Ligor täckta | 8 |

### Månad 6

| Metric | Target |
|--------|--------|
| Månatliga besökare | ≥ 5 000 |
| Tipping league-deltagare | ≥ 50 |
| Affiliate-intäkt | ≥ $500/mån |
| Google-indexerade sidor | ≥ 500 |
| Ligor täckta | ≥ 11 |
| Uptime | ≥ 99.5% |
| API response p95 | <200ms |

---

## 14. Teknisk Arkitektur (Target)

```
┌─────────────────────────────────────────────────────────────────┐
│                     SCORELOCK PRODUCTION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Användare → Cloudflare (CDN + WAF + SSL)                      │
│              ├── /*      → Vercel / CF Pages (Next.js SSR)     │
│              └── /api/*  → Railway (FastAPI)                    │
│                                                                 │
│  Railway:                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ FastAPI   │  │ Celery   │  │ Celery   │  │ Redis    │       │
│  │ (uvicorn) │  │ Worker   │  │ Beat     │  │          │       │
│  └─────┬────┘  └─────┬────┘  └──────────┘  └──────────┘       │
│        │              │                                         │
│        ▼              ▼                                         │
│  ┌──────────────────────┐                                       │
│  │ PostgreSQL 16        │                                       │
│  │ + TimescaleDB        │                                       │
│  └──────────────────────┘                                       │
│                                                                 │
│  Datakällor:                                                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ football-  │  │ API-       │  │ The Odds   │               │
│  │ data.org   │  │ Football   │  │ API        │               │
│  │ (primär)   │  │ (live)     │  │ (odds)     │               │
│  └────────────┘  └────────────┘  └────────────┘               │
│                                                                 │
│  AI & Services:                                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ Anthropic  │  │ Stripe     │  │ Sentry     │               │
│  │ (content)  │  │ (payments) │  │ (errors)   │               │
│  └────────────┘  └────────────┘  └────────────┘               │
│                                                                 │
│  Distribution:                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐               │
│  │ OneSignal  │  │ Twitter/X  │  │ Telegram   │               │
│  │ (push)     │  │ (bot)      │  │ (bot)      │               │
│  └────────────┘  └────────────┘  └────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 15. Prioriteringsregler

1. **Content är kung.** Utan AI-artiklar är vi bara ett siffror-verktyg bland hundra andra.
2. **Data före allt.** Utan data kan ingenting genereras.
3. **Gratis för användaren.** Affiliate betalar — inte användaren.
4. **SEO från dag 1.** Varje artikel = indexerbar sida som drar trafik.
5. **Svenska först.** Nordisk nisch = lägre konkurrens = snabbare traction.
6. **Ship > Perfect.** 80% ute slår 100% i utveckling.
7. **Mätbart.** Om det inte mäts vet vi inte om det fungerar.
8. **Multi-source.** Aldrig beroende av ett enda API.

---

## 16. Juridik

| Område | Status | Vad som krävs |
|--------|--------|---------------|
| Betting-content | ✅ Lagligt i Sverige att skriva om odds | Inget speciellt |
| Affiliate-länkar | Kräver märkning | "Reklamlänk" vid varje affiliate-CTA |
| AI-genererat content | Inga restriktioner | Rekommenderat: "Genererat med AI-stöd" disclaimer |
| Sportdata | Fakta kan inte copyrightskyddas (EU-domstol) | Säkert att visa resultat och tabeller |
| RSS-nyheter | Omskrivning via AI = egen artikel | Citera källa vid behov |
| GDPR | Cookie consent + privacy policy + dataminimering | Implementeras i M7.11 |
| Spelansvar | Stödlinjen: 020-819 100, 18+ | Synligt på alla sidor med odds-innehåll |
| Varumärke | ScoreLock — verifiera att det är fritt | Kontrollera PRV |

---

*Senast uppdaterad: 2026-02-11 — Session 4 (M1–M5 complete)*
*Källdokument: PROJECT_BLUEPRINT.md + ROADMAP v1 + ROADMAP v2*

# ⚽ ScoreLock Football Analytics

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
| **Task Queue** | Celery + Redis |
| **ML** | scikit-learn, XGBoost, Hugging Face Transformers |
| **Frontend** | Next.js 14 + TypeScript + Tailwind CSS |
| **Charts** | Recharts / D3.js |
| **Realtime** | WebSockets via FastAPI |
| **Infrastructure** | Docker, GitHub Actions, Railway → AWS/GCP |
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
git clone https://github.com/yourusername/scorelock.git
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

## License

Proprietary — All rights reserved.

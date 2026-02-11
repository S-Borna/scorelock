"""Celery tasks — the data pipeline that powers ScoreLock.

These tasks run on schedule (configured in celery_app.py) and keep
the database up to date with fixtures, scores, odds, and predictions.

Data source strategy:
  - football-data.org: Primary for fixtures + standings (generous free quota)
  - API-Football: Live scores only + Allsvenskan/EL/ECL (not on football-data.org)
  - The Odds API: All odds (40+ bookmakers, 500 req/month)
"""

import asyncio
from datetime import date, datetime, timedelta, timezone

import structlog
from app.core.celery_app import celery_app
from app.core.database import async_session

logger = structlog.get_logger()


def run_async(coro):
    """Helper to run async code inside sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.services.tasks.fetch_daily_fixtures")
def fetch_daily_fixtures():
    """Fetch upcoming fixtures — football-data.org primary, API-Football fallback.

    Strategy:
      - football-data.org: PL, La Liga, Serie A, Bundesliga, CL (14 days ahead)
      - API-Football: Allsvenskan, EL, ECL (today + tomorrow only, quota-limited)
    """
    async def _fetch():
        from app.services.football_data import (
            football_data, FD_COMPETITIONS, FD_UNSUPPORTED_LEAGUES,
            FootballDataClient,
        )
        from app.services.api_football import api_football, LEAGUE_IDS, PHASE_1_LEAGUES
        from app.services.db_service import (
            upsert_fixtures_batch, upsert_fixture, get_league_by_api_id,
            ensure_team,
        )
        from app.core.quota_manager import get_quota_manager

        total = 0
        quota = get_quota_manager()

        async with async_session() as session:
            # ── 1. football-data.org leagues (generous quota) ──
            for code, info in FD_COMPETITIONS.items():
                api_football_id = info["api_football_id"]
                league = await get_league_by_api_id(session, api_football_id)
                if not league:
                    # Auto-create league if not in DB yet
                    from app.services.db_service import upsert_league
                    league = await upsert_league(
                        session,
                        api_id=api_football_id,
                        name=info["name"],
                        country=code,
                        logo_url=None,
                        league_type="league" if code != "CL" else "cup",
                        current_season=date.today().year,
                    )

                try:
                    matches = await football_data.get_upcoming_matches(code, days_ahead=14)
                    normalized = [
                        FootballDataClient.normalize_match_to_fixture(m, api_football_id)
                        for m in matches
                    ]
                    normalized = [n for n in normalized if n]  # Filter empty
                    if normalized:
                        count = await upsert_fixtures_batch(session, normalized, league)
                        total += count
                        logger.info(
                            "fd_fixtures_synced",
                            league=info["name"],
                            count=count,
                        )
                except Exception as exc:
                    logger.error("fd_fixture_fetch_failed", league=info["name"], error=str(exc))

            # ── 2. API-Football for unsupported leagues ──
            today = date.today()
            tomorrow = today + timedelta(days=1)

            for league_name in PHASE_1_LEAGUES:
                if league_name not in FD_UNSUPPORTED_LEAGUES:
                    continue  # Already handled by football-data.org

                if not await quota.can_call("api_football"):
                    logger.warning("api_football_quota_exhausted", skipping=league_name)
                    break

                api_id = LEAGUE_IDS[league_name]
                league = await get_league_by_api_id(session, api_id)
                if not league:
                    continue

                for day in [today, tomorrow]:
                    try:
                        await quota.record_call("api_football")
                        fixtures = await api_football.get_fixtures_by_date(day, api_id)
                    except Exception as exc:
                        logger.error("fixture_fetch_failed", league=league_name, error=str(exc))
                        continue

                    if fixtures:
                        count = await upsert_fixtures_batch(session, fixtures, league)
                        total += count

            await session.commit()

        return total

    count = run_async(_fetch())
    return {"status": "ok", "fixtures_processed": count}


@celery_app.task(name="app.services.tasks.update_live_scores")
def update_live_scores():
    """Update scores for currently live matches (API-Football only — needs live data)."""
    async def _update():
        from app.services.api_football import api_football
        from app.services.db_service import upsert_fixture, get_league_by_api_id
        from app.core.quota_manager import get_quota_manager

        quota = get_quota_manager()
        if not await quota.can_call("api_football"):
            logger.warning("api_football_quota_exhausted", task="update_live_scores")
            return 0

        try:
            await quota.record_call("api_football")
            live = await api_football.get_live_fixtures()
        except Exception as exc:
            logger.error("live_fetch_failed", error=str(exc))
            return 0

        if not live:
            return 0

        updated = 0
        async with async_session() as session:
            for fixture_data in live:
                league_api_id = fixture_data.get("league", {}).get("id")
                if not league_api_id:
                    continue

                league = await get_league_by_api_id(session, league_api_id)
                if not league:
                    continue  # Not a league we track

                result = await upsert_fixture(session, fixture_data, league)
                if result:
                    updated += 1

                    # Publish live update via WebSocket
                    try:
                        from app.api.websocket import publish_score_update
                        goals = fixture_data.get("goals", {})
                        status_info = fixture_data.get("fixture", {}).get("status", {})
                        publish_score_update(
                            fixture_id=result.id,
                            home_goals=goals.get("home", 0) or 0,
                            away_goals=goals.get("away", 0) or 0,
                            status=result.status.value if hasattr(result.status, "value") else str(result.status),
                            minute=status_info.get("elapsed"),
                        )
                    except Exception as exc:
                        logger.warning("ws_publish_failed", error=str(exc))

            await session.commit()

        logger.info("live_scores_updated", count=updated)
        return updated

    count = run_async(_update())
    return {"status": "ok", "updated": count}


@celery_app.task(name="app.services.tasks.fetch_odds_updates")
def fetch_odds_updates():
    """Fetch odds from The Odds API (40+ bookmakers) — replaces API-Football odds.

    Strategy: One call per league fetches ALL upcoming match odds.
    500 req/month budget → ~2 calls/league × 8 leagues × 2/day = ~32 req/day = 960/month
    So we only run this 1-2x/day, controlled by Celery Beat.
    """
    async def _fetch():
        from app.services.odds_api import odds_api, ODDS_SPORT_KEYS, OddsAPIClient
        from app.services.db_service import upsert_odds, get_league_by_api_id
        from app.models.models import Fixture, MatchStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.core.quota_manager import get_quota_manager

        quota = get_quota_manager()
        total_odds = 0

        async with async_session() as session:
            for sport_key, info in ODDS_SPORT_KEYS.items():
                if not await quota.can_call("the_odds_api"):
                    logger.warning("odds_api_quota_exhausted")
                    break

                api_football_id = info["api_football_id"]
                league = await get_league_by_api_id(session, api_football_id)
                if not league:
                    continue

                try:
                    # Single call gets h2h + totals for all upcoming matches
                    events = await odds_api.get_h2h_and_totals(sport_key)
                except Exception as exc:
                    logger.error("odds_fetch_failed", league=info["name"], error=str(exc))
                    continue

                if not events:
                    continue

                # Build fixture name map for matching
                from datetime import datetime
                result = await session.execute(
                    select(Fixture)
                    .where(
                        Fixture.league_id == league.id,
                        Fixture.status == MatchStatus.SCHEDULED,
                        Fixture.kickoff >= datetime.utcnow(),
                    )
                    .options(
                        selectinload(Fixture.home_team),
                        selectinload(Fixture.away_team),
                    )
                )
                fixtures = list(result.scalars().all())

                # Create name → fixture_id map
                name_map: dict[str, int] = {}
                for f in fixtures:
                    if f.home_team and f.away_team:
                        key = f"{f.home_team.name.lower().strip()} vs {f.away_team.name.lower().strip()}"
                        name_map[key] = f.id

                for event in events:
                    fixture_id = OddsAPIClient.match_event_to_fixture(event, name_map)
                    if not fixture_id:
                        continue

                    best = OddsAPIClient.extract_best_odds(event)

                    # Store 1X2 odds (best across all bookmakers)
                    if best["home_odds"] and best["draw_odds"] and best["away_odds"]:
                        await upsert_odds(
                            session,
                            fixture_id=fixture_id,
                            bookmaker=f"Best ({best['home_bookmaker']})",
                            market="1X2",
                            home_odds=best["home_odds"],
                            draw_odds=best["draw_odds"],
                            away_odds=best["away_odds"],
                        )
                        total_odds += 1

                    # Store individual bookmaker odds too
                    for bm in event.get("bookmakers", []):
                        bm_name = bm.get("title", "Unknown")
                        for market in bm.get("markets", []):
                            market_key = market.get("key", "")
                            outcomes = {o["name"]: o.get("price", 0) for o in market.get("outcomes", [])}

                            if market_key == "h2h":
                                home_team = event.get("home_team", "")
                                away_team = event.get("away_team", "")
                                await upsert_odds(
                                    session,
                                    fixture_id=fixture_id,
                                    bookmaker=bm_name,
                                    market="1X2",
                                    home_odds=outcomes.get(home_team),
                                    draw_odds=outcomes.get("Draw"),
                                    away_odds=outcomes.get(away_team),
                                )
                                total_odds += 1

                            elif market_key == "totals":
                                for o in market.get("outcomes", []):
                                    point = o.get("point", 0)
                                    if point == 2.5:
                                        await upsert_odds(
                                            session,
                                            fixture_id=fixture_id,
                                            bookmaker=bm_name,
                                            market="Over/Under 2.5",
                                            over_odds=outcomes.get("Over"),
                                            under_odds=outcomes.get("Under"),
                                            line=2.5,
                                        )

                logger.info("odds_synced", league=info["name"], events=len(events))

            await session.commit()

        logger.info("odds_sync_complete", total_odds=total_odds)
        return total_odds

    count = run_async(_fetch())
    return {"status": "ok", "odds_updated": count}


@celery_app.task(name="app.services.tasks.run_daily_predictions")
def run_daily_predictions():
    """Run ML predictions for upcoming matches using trained model."""
    async def _predict():
        from app.ml.predictor import get_predictor, identify_value_bets
        from app.ml.features import FeatureComputer
        from app.services.db_service import (
            get_finished_fixtures_for_training,
            get_upcoming_fixtures_for_prediction,
            upsert_prediction,
            update_prediction_results,
        )

        predictor = get_predictor()
        if not predictor.is_loaded:
            logger.warning("model_not_loaded", reason="No trained model found")
            return {"status": "skipped", "reason": "model_not_loaded"}

        async with async_session() as session:
            # 1. Update results for past predictions
            updated = await update_prediction_results(session)
            if updated:
                logger.info("prediction_results_updated", count=updated)

            # 2. Load historical fixtures to populate feature computer
            finished = await get_finished_fixtures_for_training(session)
            computer = FeatureComputer()
            computer.populate_from_fixtures(finished)

            # 3. Get upcoming fixtures without predictions
            upcoming = await get_upcoming_fixtures_for_prediction(session)
            if not upcoming:
                logger.info("no_upcoming_fixtures")
                await session.commit()
                return {"status": "ok", "predictions": 0, "results_updated": updated}

            # 4. Generate predictions
            predicted = 0
            for fixture in upcoming:
                try:
                    prediction = predictor.predict_match(
                        computer,
                        fixture.home_team_id,
                        fixture.away_team_id,
                        fixture.kickoff,
                        fixture.season,
                    )

                    # Check for value bets using best available odds
                    is_value_home = False
                    is_value_draw = False
                    is_value_away = False
                    value_edge = None

                    odds_1x2 = [o for o in fixture.odds if o.market == "1X2"]
                    if odds_1x2:
                        # Find best odds across all bookmakers
                        best_home = max((o.home_odds for o in odds_1x2 if o.home_odds), default=0)
                        best_draw = max((o.draw_odds for o in odds_1x2 if o.draw_odds), default=0)
                        best_away = max((o.away_odds for o in odds_1x2 if o.away_odds), default=0)

                        if best_home and best_draw and best_away:
                            vb = identify_value_bets(
                                prediction,
                                {
                                    "home": best_home,
                                    "draw": best_draw,
                                    "away": best_away,
                                },
                            )
                            is_value_home = vb.get("is_value_home", False)
                            is_value_draw = vb.get("is_value_draw", False)
                            is_value_away = vb.get("is_value_away", False)
                            value_edge = vb.get("value_edge")

                    await upsert_prediction(
                        session,
                        fixture_id=fixture.id,
                        home_win_prob=prediction.home_win_prob,
                        draw_prob=prediction.draw_prob,
                        away_win_prob=prediction.away_win_prob,
                        confidence=prediction.confidence,
                        over_25_prob=prediction.over_25_prob,
                        expected_goals=prediction.expected_goals,
                        model_version=prediction.model_version,
                        is_value_home=is_value_home,
                        is_value_draw=is_value_draw,
                        is_value_away=is_value_away,
                        value_edge=value_edge,
                    )
                    predicted += 1

                except Exception as exc:
                    logger.error(
                        "prediction_failed",
                        fixture_id=fixture.id,
                        error=str(exc),
                    )

            await session.commit()

        logger.info("daily_predictions_complete", predicted=predicted)
        return {"status": "ok", "predictions": predicted, "results_updated": updated}

    return run_async(_predict())


@celery_app.task(name="app.services.tasks.run_sentiment_analysis")
def run_sentiment_analysis():
    """Run LLM sentiment analysis on teams with upcoming fixtures."""
    async def _analyze():
        from app.services.sentiment import get_sentiment_analyzer
        from app.services.news_fetcher import fetch_team_news, format_articles_for_analysis
        from app.services.db_service import get_upcoming_fixtures_for_prediction
        from app.models.models import SentimentScore

        analyzer = get_sentiment_analyzer()
        analyzed = 0

        async with async_session() as session:
            upcoming = await get_upcoming_fixtures_for_prediction(session, days_ahead=3)

            team_ids_done: set[int] = set()
            for fixture in upcoming:
                for team, team_id in [
                    (fixture.home_team, fixture.home_team_id),
                    (fixture.away_team, fixture.away_team_id),
                ]:
                    if team_id in team_ids_done:
                        continue
                    team_ids_done.add(team_id)

                    team_name = team.name if team else f"Team {team_id}"

                    # Fetch real news articles about this team
                    try:
                        articles = await fetch_team_news(team_name)
                    except Exception as exc:
                        logger.warning("news_fetch_failed", team=team_name, error=str(exc))
                        articles = []

                    if not articles:
                        logger.info("sentiment_no_news", team=team_name)
                        continue

                    news_text = format_articles_for_analysis(articles)

                    try:
                        result = await analyzer.analyze_text(team_name, news_text)
                    except RuntimeError:
                        logger.warning("sentiment_skipped", reason="anthropic_key_missing")
                        return {"status": "skipped", "reason": "anthropic_key_missing"}
                    except Exception as exc:
                        logger.error("sentiment_failed", team=team_name, error=str(exc))
                        continue

                    score = SentimentScore(
                        team_id=team_id,
                        fixture_id=fixture.id,
                        score=result["score"],
                        buzz_score=result["buzz_score"],
                        source="llm_analysis",
                        summary=result.get("summary"),
                        raw_data=result,
                    )
                    session.add(score)
                    analyzed += 1

            await session.commit()

        logger.info("sentiment_analysis_complete", teams_analyzed=analyzed)
        return {"status": "ok", "analyzed": analyzed}

    return run_async(_analyze())


@celery_app.task(name="app.services.tasks.update_standings")
def update_standings():
    """Update league standings — football-data.org primary, API-Football fallback.

    football-data.org: PL, La Liga, Serie A, Bundesliga, CL
    API-Football: Allsvenskan, EL, ECL
    """
    async def _update():
        from app.services.football_data import (
            football_data, FD_COMPETITIONS, FD_UNSUPPORTED_LEAGUES,
            FootballDataClient,
        )
        from app.services.api_football import api_football, LEAGUE_IDS, PHASE_1_LEAGUES
        from app.services.db_service import upsert_standing, get_league_by_api_id
        from app.core.quota_manager import get_quota_manager

        current_year = date.today().year
        total = 0
        quota = get_quota_manager()

        async with async_session() as session:
            # ── 1. football-data.org leagues ──
            for code, info in FD_COMPETITIONS.items():
                api_football_id = info["api_football_id"]
                league = await get_league_by_api_id(session, api_football_id)
                if not league:
                    continue

                try:
                    standings = await football_data.get_standings(code)
                except Exception as exc:
                    logger.error("fd_standings_failed", league=info["name"], error=str(exc))
                    continue

                season = current_year if code == "BL1" else current_year - 1
                for entry in standings:
                    normalized = FootballDataClient.normalize_standing(entry, code)
                    result = await upsert_standing(session, normalized, league, season)
                    if result:
                        total += 1

                logger.info("fd_standings_synced", league=info["name"], teams=len(standings))

            # ── 2. API-Football for unsupported leagues ──
            for league_name in PHASE_1_LEAGUES:
                if league_name not in FD_UNSUPPORTED_LEAGUES:
                    continue

                if not await quota.can_call("api_football"):
                    logger.warning("api_football_quota_exhausted", skipping=league_name)
                    break

                api_id = LEAGUE_IDS[league_name]
                league = await get_league_by_api_id(session, api_id)
                if not league:
                    continue

                season = current_year if league_name == "allsvenskan" else current_year - 1

                try:
                    await quota.record_call("api_football")
                    standings = await api_football.get_standings(api_id, season)
                except Exception as exc:
                    logger.error("standings_fetch_failed", league=league_name, error=str(exc))
                    continue

                for entry in standings:
                    result = await upsert_standing(session, entry, league, season)
                    if result:
                        total += 1

                logger.info("standings_upserted", league=league_name, teams=len(standings))

            await session.commit()

        return total

    count = run_async(_update())
    return {"status": "ok", "standings_updated": count}


@celery_app.task(name="app.services.tasks.seed_data")
def seed_data():
    """One-time seed task — fetch leagues and teams from API-Football."""
    async def _seed():
        from app.services.seed import seed_all
        await seed_all()

    run_async(_seed())
    return {"status": "ok"}


@celery_app.task(name="app.services.tasks.train_model")
def train_model():
    """Train/retrain the ML prediction model from historical data."""
    async def _train():
        from app.ml.trainer import run_training_pipeline
        return await run_training_pipeline()

    return run_async(_train())


@celery_app.task(name="app.services.tasks.fetch_historical_data")
def fetch_historical_data():
    """Fetch historical fixtures and standings from API-Football."""
    async def _fetch():
        from app.services.historical import (
            fetch_historical_fixtures,
            fetch_historical_standings,
        )
        fixtures = await fetch_historical_fixtures()
        standings = await fetch_historical_standings()
        return {
            "status": "ok",
            "fixtures": fixtures["total_fixtures"],
            "standings": standings["total_standings"],
            "api_requests": fixtures["total_requests"] + standings["total_requests"],
        }

    return run_async(_fetch())


# ══════════════════════════════════════════════════════════
# AI Content Engine Tasks  (M3)
# ══════════════════════════════════════════════════════════

@celery_app.task(name="app.services.tasks.generate_content_previews")
def generate_content_previews():
    """Generate match previews for tomorrow's fixtures.

    Runs daily at 10:00 UTC — generates Swedish AI-articles for
    every scheduled fixture in the next 24 hours.
    """
    async def _gen():
        from app.services.content_generator import generate_match_preview
        from app.services.db_service import get_fixtures
        from app.models.models import MatchStatus

        created = 0
        async with async_session() as session:
            fixtures = await get_fixtures(
                session, days_ahead=1, league_id=None, status="scheduled"
            )
            for fixture in fixtures:
                article = await generate_match_preview(session, fixture)
                if article:
                    created += 1
        return {"status": "ok", "previews_created": created}

    return run_async(_gen())


@celery_app.task(name="app.services.tasks.generate_content_reports")
def generate_content_reports():
    """Generate match reports for recently finished fixtures.

    Runs every hour during match hours — picks up fixtures that
    finished within the last 3 hours and generates reports.
    """
    async def _gen():
        from app.services.content_generator import generate_match_report
        from app.models.models import MatchStatus, Fixture
        from sqlalchemy import select

        created = 0
        cutoff = datetime.now(timezone.utc) - timedelta(hours=3)
        async with async_session() as session:
            q = (
                select(Fixture)
                .where(
                    Fixture.status == MatchStatus.FINISHED,
                    Fixture.updated_at >= cutoff,
                )
                .order_by(Fixture.kickoff.desc())
            )
            result = await session.execute(q)
            fixtures = list(result.scalars().all())

            for fixture in fixtures:
                article = await generate_match_report(session, fixture)
                if article:
                    created += 1
        return {"status": "ok", "reports_created": created}

    return run_async(_gen())


@celery_app.task(name="app.services.tasks.generate_content_round_summaries")
def generate_content_round_summaries():
    """Generate round summaries for completed rounds.

    Runs daily at 04:00 UTC — checks each league for rounds
    where all fixtures are finished but no summary exists yet.
    """
    async def _gen():
        from app.services.content_generator import generate_round_summary
        from app.services.db_service import get_all_leagues
        from app.models.models import Fixture, MatchStatus
        from sqlalchemy import select, func

        created = 0
        async with async_session() as session:
            leagues = await get_all_leagues(session)
            for league in leagues:
                # Find rounds with all fixtures finished
                rounds_q = await session.execute(
                    select(Fixture.round)
                    .where(Fixture.league_id == league.id)
                    .group_by(Fixture.round)
                    .having(
                        func.count(Fixture.id)
                        == func.count(
                            func.nullif(Fixture.status != MatchStatus.FINISHED, True)
                        )
                    )
                )
                rounds_done = [r[0] for r in rounds_q.all() if r[0]]

                for round_str in rounds_done[-3:]:  # Last 3 completed rounds
                    article = await generate_round_summary(
                        session, league.id, round_str
                    )
                    if article:
                        created += 1

        return {"status": "ok", "summaries_created": created}

    return run_async(_gen())


@celery_app.task(name="app.services.tasks.generate_content_value_bets")
def generate_content_value_bets():
    """Generate daily value bet article.

    Runs daily at 09:00 UTC — analyses all upcoming fixtures (next 48h)
    and creates a value bet article if any value bets are found.
    """
    async def _gen():
        from app.services.content_generator import generate_value_bet_article

        async with async_session() as session:
            article = await generate_value_bet_article(session)
            return {
                "status": "ok",
                "created": article is not None,
                "slug": article.slug if article else None,
            }

    return run_async(_gen())


@celery_app.task(name="app.services.tasks.generate_content_news_rewrites")
def generate_content_news_rewrites():
    """Fetch RSS news and rewrite as original Swedish articles.

    Runs every 4 hours — fetches top stories from 10 RSS feeds,
    deduplicates, and rewrites as Swedish articles.
    """
    async def _gen():
        from app.services.content_generator import generate_news_rewrite
        from app.services.news_fetcher import fetch_team_news

        created = 0
        top_teams = [
            "Arsenal", "Manchester City", "Liverpool", "Barcelona",
            "Real Madrid", "Bayern Munich", "Inter", "PSG",
        ]

        async with async_session() as session:
            for team in top_teams:
                articles = fetch_team_news(team)
                for art in articles[:2]:  # Max 2 per team per run
                    if len(art.get("content", "")) < 100:
                        continue
                    article = await generate_news_rewrite(
                        session,
                        source=art.get("source", "Unknown"),
                        original_title=art.get("title", ""),
                        original_content=art.get("content", ""),
                        context=f"Lag: {team}",
                    )
                    if article:
                        created += 1

        return {"status": "ok", "rewrites_created": created}

    return run_async(_gen())

"""Phase 7.2 — SportMonksProvider static-fixture mode.

Verifierar att adaptern parser SportMonks Components-payloads korrekt.
Inga API-keys, ingen DB, ingen nätverk. Använder statiska JSON-filer i
`/competitor-ref/sportmonks/payloads/`.

Live-mode (httpx mot api.sportmonks.com) testas separat när tier-uppgradering
landar i augusti.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import Settings
from app.providers.base import ProviderStatus
from app.providers.sportmonks import SportMonksProvider


PAYLOAD_DIR = Path("/competitor-ref/sportmonks/payloads")
TEST_FIXTURE_ID = "19425203"
TEST_LEAGUE_ID = "384"
TEST_SEASON = 25533


@pytest.fixture
def static_settings() -> Settings:
    return Settings(
        sportmonks_use_static_fixtures=True,
        sportmonks_static_payload_dir=str(PAYLOAD_DIR),
    )


@pytest.fixture
def provider(static_settings: Settings) -> SportMonksProvider:
    return SportMonksProvider(static_settings)


@pytest.mark.skipif(
    not PAYLOAD_DIR.exists(),
    reason="SportMonks static payloads not mounted (skip outside docker)",
)
class TestSportMonksStatic:
    @pytest.mark.asyncio
    async def test_fetch_fixture_detail(self, provider: SportMonksProvider) -> None:
        fix = await provider.fetch_fixture_detail(TEST_FIXTURE_ID)
        assert fix.external_id == TEST_FIXTURE_ID
        assert fix.name == "Inter vs Cagliari"
        assert fix.league_external_id == TEST_LEAGUE_ID
        assert fix.season_external_id == str(TEST_SEASON)
        assert fix.home_team_external_id == "2930"
        assert fix.away_team_external_id == "585"
        assert fix.home_score == 3
        assert fix.away_score == 0
        assert fix.length_minutes == 90
        assert fix.status == "FINISHED"
        assert fix.venue_external_id == "1721"
        assert fix.kickoff.year == 2026
        assert fix.kickoff.month == 4

    @pytest.mark.asyncio
    async def test_fetch_lineups_two_teams(
        self, provider: SportMonksProvider
    ) -> None:
        lineups = await provider.fetch_lineups(TEST_FIXTURE_ID)
        assert len(lineups) == 2
        team_ids = {ln.team_external_id for ln in lineups}
        assert team_ids == {"2930", "585"}
        for ln in lineups:
            assert ln.fixture_external_id == TEST_FIXTURE_ID
            assert ln.state == "CONFIRMED"
            starters = [p for p in ln.players if p.is_starter]
            assert len(starters) == 11

    @pytest.mark.asyncio
    async def test_fetch_events_returns_recognised_types(
        self, provider: SportMonksProvider
    ) -> None:
        events = await provider.fetch_events(TEST_FIXTURE_ID)
        assert len(events) > 0
        types = {ev.event_type for ev in events}
        # Inter 3-0 Cagliari ska innehålla mål + kort + byten
        assert "GOAL" in types
        assert "YELLOW_CARD" in types
        assert "SUBSTITUTION" in types
        # Alla events har fixture_external_id satt
        assert all(ev.fixture_external_id == TEST_FIXTURE_ID for ev in events)

    @pytest.mark.asyncio
    async def test_fetch_statistics_per_team_two_rollups(
        self, provider: SportMonksProvider
    ) -> None:
        stats = await provider.fetch_statistics_per_team(TEST_FIXTURE_ID)
        assert len(stats) == 2
        for s in stats:
            assert s.fixture_external_id == TEST_FIXTURE_ID
            assert s.team_external_id in {"2930", "585"}
            # Trends.json har 1132 entries — minst 30 olika stat-types per lag
            assert len(s.stats) >= 20
            # SportMonks fixture-stat type-IDs: 41=shots-off-target, 42=shots-on-target,
            # 44=dangerous-attacks, 45=ball-possession% etc. Vi vet att 44 finns.
            assert 44 in s.stats

    @pytest.mark.asyncio
    async def test_fetch_standings_serie_a_20_teams(
        self, provider: SportMonksProvider
    ) -> None:
        standings = await provider.fetch_standings(TEST_LEAGUE_ID, TEST_SEASON)
        assert len(standings) == 20
        positions = sorted(s.position for s in standings)
        assert positions == list(range(1, 21))
        leader = next(s for s in standings if s.position == 1)
        assert leader.team_external_id == "2930"  # Inter
        assert leader.points >= 75
        assert leader.played == 34
        assert leader.won >= 20

    @pytest.mark.asyncio
    async def test_fetch_teams_from_standings(
        self, provider: SportMonksProvider
    ) -> None:
        teams = await provider.fetch_teams(TEST_LEAGUE_ID, TEST_SEASON)
        assert len(teams) == 20
        inter = next(t for t in teams if t.external_id == "2930")
        assert inter.name == "Inter"
        assert inter.short_code == "INT"
        assert inter.founded == 1908

    @pytest.mark.asyncio
    async def test_fetch_players_team_squad(
        self, provider: SportMonksProvider
    ) -> None:
        players = await provider.fetch_players("2930")
        assert len(players) >= 20  # Team Squad-payload har 24 spelare
        # Alla spelare har external_id + name
        assert all(p.external_id and p.name for p in players)

    @pytest.mark.asyncio
    async def test_health_static_mode_healthy(
        self, provider: SportMonksProvider
    ) -> None:
        health = await provider.health()
        assert health.provider == "sportmonks"
        assert health.status == ProviderStatus.HEALTHY


class TestSportMonksMode:
    """Tester som inte kräver mounted payload-dir."""

    def test_supports_operations(self) -> None:
        from app.providers.base import Operation

        # Adaptern stödjer 8 operationer (allt utom ODDS/IN_PLAY_ODDS/BROADCASTS/WEATHER)
        settings = Settings(sportmonks_use_static_fixtures=True)
        provider = SportMonksProvider(settings)
        assert Operation.FIXTURES in provider.supports
        assert Operation.LINEUPS in provider.supports
        assert Operation.EVENTS in provider.supports
        assert Operation.STATISTICS in provider.supports
        assert Operation.STANDINGS in provider.supports
        assert Operation.ODDS not in provider.supports

    def test_static_mode_flag(self) -> None:
        static = SportMonksProvider(Settings(sportmonks_use_static_fixtures=True))
        live = SportMonksProvider(Settings(sportmonks_use_static_fixtures=False))
        assert static.is_static is True
        assert live.is_static is False

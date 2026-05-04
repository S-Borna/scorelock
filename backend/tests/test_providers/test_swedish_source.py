"""Track S-1.1 — SwedishSourceProvider tests.

Verifierar:
- Static-mode laddar HTML från snapshots
- Multi-source-fallback kicks in när primary returnerar 0 rader (schema-drift)
- Slug-generation hanterar svenska tecken (åäö)
- Operations vi inte stödjer raise:ar ProviderUnsupported
- Health-check rapporterar HEALTHY när snapshots finns

Inga live HTTP-calls. Allt mot static snapshots i
/competitor-ref/swedish/snapshots/.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import Settings
from app.providers.base import ProviderStatus
from app.providers.errors import ProviderUnavailable, ProviderUnsupported
from app.providers.swedish_source import (
    DEFAULT_SOURCES,
    FOTBOLLSKANALEN_SOURCE,
    SwedishSourceProvider,
)


SNAPSHOT_DIR = Path("/competitor-ref/swedish/snapshots")


@pytest.fixture
def static_settings() -> Settings:
    return Settings(
        sportmonks_use_static_fixtures=True,
        sportmonks_static_payload_dir="/competitor-ref/sportmonks/payloads",
    )


@pytest.fixture
def provider(static_settings: Settings) -> SwedishSourceProvider:
    return SwedishSourceProvider(static_settings)


@pytest.mark.skipif(
    not SNAPSHOT_DIR.exists(),
    reason="Swedish snapshots not mounted (skip outside docker)",
)
class TestStaticMode:
    @pytest.mark.asyncio
    async def test_fetch_standings_falls_to_fotbollskanalen(
        self, provider: SwedishSourceProvider
    ) -> None:
        """SvFF-snapshot är tom → fallback till Fotbollskanalen vars snapshot har 8 rader."""
        standings = await provider.fetch_standings("allsvenskan", 2026)
        assert len(standings) == 8
        # Verifiera ordningen
        positions = [s.position for s in standings]
        assert positions == [1, 2, 3, 4, 5, 6, 7, 8]
        # Verifiera leadern
        leader = standings[0]
        assert leader.points == 62
        assert leader.played == 26
        assert leader.team_external_id == "malmo-ff"

    @pytest.mark.asyncio
    async def test_fetch_fixtures_returns_three(
        self, provider: SwedishSourceProvider
    ) -> None:
        """SvFF-fixtures-snapshot har 3 rader inklusive 1 utan score."""
        fixtures = await provider.fetch_fixtures("allsvenskan", 2026)
        assert len(fixtures) == 3
        finished = [f for f in fixtures if f.status == "FINISHED"]
        scheduled = [f for f in fixtures if f.status == "SCHEDULED"]
        assert len(finished) == 2
        assert len(scheduled) == 1
        # Första matchen
        first = fixtures[0]
        assert "malmo" in first.home_team_external_id.lower()
        assert "aik" in first.away_team_external_id.lower()
        assert first.home_score == 2
        assert first.away_score == 1

    @pytest.mark.asyncio
    async def test_fetch_teams_derived_from_standings(
        self, provider: SwedishSourceProvider
    ) -> None:
        teams = await provider.fetch_teams("allsvenskan", 2026)
        assert len(teams) == 8
        names = {t.name for t in teams}
        # Slug → Title-Case ger "Malmo Ff" etc — råform, normalizer kan refina
        assert any("Malmo" in n for n in names)
        assert any("Aik" in n for n in names)

    @pytest.mark.asyncio
    async def test_health_static_mode_healthy(
        self, provider: SwedishSourceProvider
    ) -> None:
        health = await provider.health()
        assert health.provider == "swedish_source"
        assert health.status == ProviderStatus.HEALTHY
        assert "sources har snapshots" in (health.last_error or "")


class TestFallbackCascadeAllFail:
    """Test fallback när alla källor saknar snapshot (no-snapshot-dir)."""

    @pytest.mark.asyncio
    async def test_all_sources_missing_snapshots_raises(self) -> None:
        # Pekar mot katalog utan snapshots — alla källor faller, sista fel propagerar
        provider = SwedishSourceProvider(
            Settings(sportmonks_use_static_fixtures=True),
            snapshot_dir="/tmp/nonexistent_snapshots",
        )
        # is_static blir False eftersom katalogen inte finns →  hoppar live-fetch
        # men live HTTP utan riktigt nät kommer också misslyckas → ProviderUnavailable
        # eller ProviderUnsupported (om source-list är tom).
        # Acceptera båda som "fallback exhausted".
        with pytest.raises((ProviderUnavailable, ProviderUnsupported, OSError, ConnectionError)):
            await provider.fetch_standings("allsvenskan", 2026)
        await provider.aclose()


class TestUnsupportedOperations:
    """fetch_lineup/events/statistics/players ska raise:a ProviderUnsupported."""

    @pytest.mark.asyncio
    async def test_fetch_lineup_unsupported(
        self, provider: SwedishSourceProvider
    ) -> None:
        with pytest.raises(ProviderUnsupported):
            await provider.fetch_lineup("any-fixture-id")

    @pytest.mark.asyncio
    async def test_fetch_events_unsupported(
        self, provider: SwedishSourceProvider
    ) -> None:
        with pytest.raises(ProviderUnsupported):
            await provider.fetch_events("any-fixture-id")

    @pytest.mark.asyncio
    async def test_fetch_statistics_unsupported(
        self, provider: SwedishSourceProvider
    ) -> None:
        with pytest.raises(ProviderUnsupported):
            await provider.fetch_statistics("any-fixture-id")

    @pytest.mark.asyncio
    async def test_fetch_players_unsupported(
        self, provider: SwedishSourceProvider
    ) -> None:
        with pytest.raises(ProviderUnsupported):
            await provider.fetch_players("any-team-id")

    @pytest.mark.asyncio
    async def test_fetch_fixture_detail_unsupported(
        self, provider: SwedishSourceProvider
    ) -> None:
        with pytest.raises(ProviderUnsupported):
            await provider.fetch_fixture_detail("any-fixture-id")


class TestSlugAndConfig:
    """Tester utan provider-instance."""

    def test_slug_handles_swedish_chars(self) -> None:
        from app.providers.swedish_source import SwedishSourceProvider as P

        assert P._slugify("Malmö FF") == "malmo-ff"
        assert P._slugify("Hägersten Lyfter") == "hagersten-lyfter"
        assert P._slugify("AIK") == "aik"

    def test_default_sources_in_priority_order(self) -> None:
        names = [s.name for s in DEFAULT_SOURCES]
        # SvFF primary, sedan Fotbollskanalen, sedan Allsvenskan.se
        assert names == ["svff", "fotbollskanalen", "allsvenskan_se"]

    def test_unsupported_league_raises(
        self, provider: SwedishSourceProvider
    ) -> None:
        with pytest.raises(ProviderUnsupported):
            provider._league_segment("la-liga", FOTBOLLSKANALEN_SOURCE)

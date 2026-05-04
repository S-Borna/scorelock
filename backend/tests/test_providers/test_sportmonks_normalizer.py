"""Phase 7.3 — SportMonks normalizer end-to-end mot static fixture.

Verifierar att Provider-output → DB-rader fungerar end-to-end.
Använder static-mode + Inter-Cagliari (19425203) som test-fixture.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select, and_

from app.core.config import Settings
from app.core.database import async_session as AsyncSessionLocal
from app.models.models import (
    Fixture,
    FixtureEvent,
    FixtureLineup,
    FixtureLineupPlayer,
    FixtureStatistics,
    League,
    MatchStatus,
    Player,
    ProviderEntityMapping,
    ProviderPayload,
    Team,
)
from app.providers.sportmonks import SportMonksProvider
from app.services.sportmonks_normalizer import (
    PROVIDER,
    sync_fixture_detail,
)


PAYLOAD_DIR = Path("/competitor-ref/sportmonks/payloads")
TEST_FIXTURE_ID = "19425203"


@pytest.mark.skipif(
    not PAYLOAD_DIR.exists(),
    reason="SportMonks static payloads not mounted (skip outside docker)",
)
class TestNormalizerE2E:
    @pytest.mark.asyncio
    async def test_sync_fixture_detail_full_pipeline(self) -> None:
        """End-to-end: provider → normalizer → DB. Verifiera alla entiteter."""
        provider = SportMonksProvider(
            Settings(
                sportmonks_use_static_fixtures=True,
                sportmonks_static_payload_dir=str(PAYLOAD_DIR),
            )
        )
        async with AsyncSessionLocal() as session:
            fixture = await sync_fixture_detail(
                session, provider, TEST_FIXTURE_ID
            )
            await session.commit()

            # Fixture-kontroll
            assert fixture.id is not None
            assert fixture.status == MatchStatus.FINISHED
            assert fixture.home_goals == 3
            assert fixture.away_goals == 0
            assert fixture.external_ids.get("sportmonks") == TEST_FIXTURE_ID

            # League-mapping
            mapping = await session.execute(
                select(ProviderEntityMapping).where(
                    and_(
                        ProviderEntityMapping.provider == PROVIDER,
                        ProviderEntityMapping.entity_type == "league",
                        ProviderEntityMapping.external_id == "384",
                    )
                )
            )
            assert mapping.scalar_one_or_none() is not None

            # Team-mappings (Inter + Cagliari)
            for team_ext_id in ("2930", "585"):
                m = await session.execute(
                    select(ProviderEntityMapping).where(
                        and_(
                            ProviderEntityMapping.provider == PROVIDER,
                            ProviderEntityMapping.entity_type == "team",
                            ProviderEntityMapping.external_id == team_ext_id,
                        )
                    )
                )
                assert m.scalar_one_or_none() is not None, (
                    f"Team {team_ext_id} missing mapping"
                )

            # Fixture-mapping
            fix_map = await session.execute(
                select(ProviderEntityMapping).where(
                    and_(
                        ProviderEntityMapping.provider == PROVIDER,
                        ProviderEntityMapping.entity_type == "fixture",
                        ProviderEntityMapping.external_id == TEST_FIXTURE_ID,
                    )
                )
            )
            assert fix_map.scalar_one_or_none() is not None

            # Provider-payload audit (append-only — kan finnas N rader vid re-sync)
            audit = await session.execute(
                select(ProviderPayload).where(
                    and_(
                        ProviderPayload.provider == PROVIDER,
                        ProviderPayload.entity_type == "fixture",
                        ProviderPayload.external_id == TEST_FIXTURE_ID,
                    )
                )
            )
            assert audit.scalars().first() is not None

            # Lineups (2 stycken)
            lineups = await session.execute(
                select(FixtureLineup).where(
                    FixtureLineup.fixture_id == fixture.id
                )
            )
            lineup_list = list(lineups.scalars())
            assert len(lineup_list) == 2

            # Lineup players (24 + 22 = 46 totalt)
            for lineup in lineup_list:
                players = await session.execute(
                    select(FixtureLineupPlayer).where(
                        FixtureLineupPlayer.lineup_id == lineup.id
                    )
                )
                p_list = list(players.scalars())
                assert len(p_list) >= 11, (
                    f"Lineup {lineup.id} has only {len(p_list)} players"
                )
                starters = [p for p in p_list if p.is_starting]
                assert len(starters) == 11

            # Events (≥10)
            events = await session.execute(
                select(FixtureEvent).where(
                    FixtureEvent.fixture_id == fixture.id
                )
            )
            event_list = list(events.scalars())
            assert len(event_list) >= 10
            event_types = {ev.event_type for ev in event_list}
            assert "GOAL" in event_types
            assert "YELLOW_CARD" in event_types
            assert "SUBSTITUTION" in event_types

            # Statistics (2 team-rows)
            stats = await session.execute(
                select(FixtureStatistics).where(
                    FixtureStatistics.fixture_id == fixture.id
                )
            )
            stat_list = list(stats.scalars())
            assert len(stat_list) == 2
            for s in stat_list:
                # Inter ska ha xG runt 2.33, Cagliari runt 0.59 — minst en stat-typ ska finnas
                assert s.shots_on_target is not None or s.corners is not None

    @pytest.mark.asyncio
    async def test_sync_idempotent(self) -> None:
        """Andra sync av samma fixture ska inte duplicera rader."""
        provider = SportMonksProvider(
            Settings(
                sportmonks_use_static_fixtures=True,
                sportmonks_static_payload_dir=str(PAYLOAD_DIR),
            )
        )
        async with AsyncSessionLocal() as session:
            await sync_fixture_detail(session, provider, TEST_FIXTURE_ID)
            await session.commit()

            fix1 = await session.execute(
                select(Fixture).where(
                    Fixture.external_ids["sportmonks"].astext == TEST_FIXTURE_ID
                )
            )
            count1 = len(list(fix1.scalars()))

            await sync_fixture_detail(session, provider, TEST_FIXTURE_ID)
            await session.commit()

            fix2 = await session.execute(
                select(Fixture).where(
                    Fixture.external_ids["sportmonks"].astext == TEST_FIXTURE_ID
                )
            )
            count2 = len(list(fix2.scalars()))

            assert count1 == count2, "Re-sync skapade duplicerade fixtures"

            # Player-mapping ska inte heller dubbleras
            player_maps = await session.execute(
                select(ProviderEntityMapping).where(
                    and_(
                        ProviderEntityMapping.provider == PROVIDER,
                        ProviderEntityMapping.entity_type == "player",
                    )
                )
            )
            player_map_list = list(player_maps.scalars())
            external_ids = [m.external_id for m in player_map_list]
            assert len(external_ids) == len(set(external_ids))


class TestStatColumnMapping:
    """Tester för stats-mapping utan DB."""

    def test_stats_to_columns_basic(self) -> None:
        from app.services.sportmonks_normalizer import _stats_to_columns

        stats = {
            34: 7,         # corners
            42: 5,         # shots-on-target
            45: 60,        # possession-pct
            5304: 2.33,    # xg
            999: 100,      # unknown — should be skipped
            44: 50,        # dangerous-attacks — explicit None mapping, skip
        }
        out = _stats_to_columns(stats)
        assert out == {
            "corners": 7,
            "shots_on_target": 5,
            "possession_pct": 60.0,
            "xg": 2.33,
        }

    def test_stats_to_columns_handles_none(self) -> None:
        from app.services.sportmonks_normalizer import _stats_to_columns

        stats = {34: None, 42: 5}
        out = _stats_to_columns(stats)
        assert out == {"shots_on_target": 5}

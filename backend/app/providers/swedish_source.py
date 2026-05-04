"""SwedishSourceProvider — Track S-1.1.

Multi-source-fallback för Allsvenskan-djup-pipeline. Den här provider:n är
ScoreLocks **moat** (CLAUDE.md §4) — Allsvenskan-data ingen konkurrent har
investerat i att bygga, eftersom det kräver SE-kontext + manuell selector-
skötsel som inte kan outsource:as till en data-broker.

Implementerar `SportsDataProvider`-Protocol parallellt med SportMonksProvider.
Båda kan registreras i providers.registry och driftsättas mot samma DB-rader
via `sportmonks_normalizer`-helpers (find_or_create_*, record_mapping,
record_payload — verifierat compounding-pattern från Phase 7.3).

Fallback-cascade:
    1. SvFF (svenskfotboll.se)             — official primary
    2. Fotbollskanalen (fotbollskanalen.se) — secondary
    3. Allsvenskan.se                       — tertiary

Schema-drift-detection: när en source matchar 0 rader på en lyckad fetch →
log + try next source. Full drift-monitoring (per-selector-counts +
threshold-larm) landar i S-1.2.

Två modes:
- **static**: läser HTML-snapshots från
  `/competitor-ref/swedish/snapshots/{source}/{operation}.html`. Default i
  tests + CI för deterministisk validering. Snapshot-skörd från Said i
  S-1.2 ger riktiga selectors.
- **live**: httpx GET mot publika URL:er. Default i prod när augusti-tier
  togglas (samma toggle-pattern som SportMonks-providern, env-baserad).

Selector-status (S-1.1): **PLACEHOLDERS — kommer ersättas i S-1.2 efter
HTML-snapshot-skörd**. Strukturen + fallback-pipeline är klar; selectors är
bästa-gissning utan verifierad target-HTML.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx
from bs4 import BeautifulSoup

from app.core.config import Settings
from app.providers.base import (
    DateRange,
    LiveEventEnvelope,
    Operation,
    ProviderHealth,
    ProviderStatus,
    Scope,
)
from app.providers.errors import (
    ProviderPayloadError,
    ProviderUnavailable,
    ProviderUnsupported,
)
from app.providers.normalization import (
    NormalizedFixture,
    NormalizedLineup,
    NormalizedMatchEvent,
    NormalizedMatchStatistics,
    NormalizedPlayer,
    NormalizedStanding,
    NormalizedTeam,
)


logger = logging.getLogger(__name__)


# ── Source configuration ────────────────────────────────────────────────


@dataclass(frozen=True)
class SourceConfig:
    """En SE-källa med URL-templates + CSS-selectors per operation.

    Selectors är PLACEHOLDERS i S-1.1 — Said skördar HTML-snapshots i S-1.2
    och uppdaterar med verifierade selectors.
    """

    name: str
    base_url: str
    standings_url_template: str  # {league} substitueras
    fixtures_url_template: str   # {league} + {round} substitueras
    standings_row_selector: str  # CSS-selector för tabellraderna
    standings_team_selector: str
    standings_position_selector: str
    standings_played_selector: str
    standings_points_selector: str
    fixtures_row_selector: str
    fixtures_home_selector: str
    fixtures_away_selector: str
    fixtures_score_selector: str
    fixtures_kickoff_selector: str


# Default-konfigurationer — selectors verifieras i S-1.2.
SVFF_SOURCE = SourceConfig(
    name="svff",
    base_url="https://www.svenskfotboll.se",
    standings_url_template="/{league}/serien",
    fixtures_url_template="/{league}/spelschema",
    # PLACEHOLDER selectors — verifiera mot live SvFF-HTML i S-1.2
    standings_row_selector="table.standings tbody tr",
    standings_team_selector="td.team a",
    standings_position_selector="td.position",
    standings_played_selector="td.played",
    standings_points_selector="td.points",
    fixtures_row_selector="div.match-list div.match-row",
    fixtures_home_selector="span.team-home",
    fixtures_away_selector="span.team-away",
    fixtures_score_selector="span.score",
    fixtures_kickoff_selector="time.kickoff",
)

FOTBOLLSKANALEN_SOURCE = SourceConfig(
    name="fotbollskanalen",
    base_url="https://www.fotbollskanalen.se",
    standings_url_template="/{league}/tabell",
    fixtures_url_template="/{league}/spelschema",
    standings_row_selector="table.league-table tbody tr",
    standings_team_selector="td.team-name",
    standings_position_selector="td.pos",
    standings_played_selector="td.matches",
    standings_points_selector="td.pts",
    fixtures_row_selector="li.fixture-row",
    fixtures_home_selector="span.home-team",
    fixtures_away_selector="span.away-team",
    fixtures_score_selector="span.match-score",
    fixtures_kickoff_selector="time",
)

ALLSVENSKAN_SE_SOURCE = SourceConfig(
    name="allsvenskan_se",
    base_url="https://allsvenskan.se",
    standings_url_template="/serien/serien-{year}",
    fixtures_url_template="/spelschema/{year}",
    standings_row_selector="div.standings-row",
    standings_team_selector="div.team-name",
    standings_position_selector="div.position",
    standings_played_selector="div.played",
    standings_points_selector="div.points",
    fixtures_row_selector="div.fixture",
    fixtures_home_selector="div.home",
    fixtures_away_selector="div.away",
    fixtures_score_selector="div.score",
    fixtures_kickoff_selector="div.kickoff",
)

DEFAULT_SOURCES: tuple[SourceConfig, ...] = (
    SVFF_SOURCE,
    FOTBOLLSKANALEN_SOURCE,
    ALLSVENSKAN_SE_SOURCE,
)


# League-mapping: våra interna ID-strängar → URL-segments per source.
# Just nu bara Allsvenskan; utöka för Superettan / damer / lägre divisioner senare.
LEAGUE_URL_SEGMENTS: dict[str, dict[str, str]] = {
    "allsvenskan": {
        "svff": "allsvenskan",
        "fotbollskanalen": "allsvenskan",
        "allsvenskan_se": "allsvenskan",
    },
}


HTTP_HEADERS = {
    "User-Agent": (
        "ScoreLockBot/1.0 (+https://scorelock.saidborna.com/about/bot) "
        "scrapes-svenska-fotbollsdata-respektfullt"
    ),
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.5",
    "Accept": "text/html,application/xhtml+xml",
}


# ── Provider implementation ────────────────────────────────────────────


class SwedishSourceProvider:
    """SportsDataProvider-implementation för svenska källor."""

    name: str = "swedish_source"
    supports: frozenset[Operation] = frozenset(
        {
            Operation.FIXTURES,
            Operation.STANDINGS,
            Operation.LIVE_FIXTURES,
            Operation.TEAMS,
        }
    )

    def __init__(
        self,
        settings: Settings,
        sources: tuple[SourceConfig, ...] = DEFAULT_SOURCES,
        snapshot_dir: str = "/competitor-ref/swedish/snapshots",
    ) -> None:
        self._settings = settings
        self._sources = sources
        self._snapshot_dir = Path(snapshot_dir)
        self._client: httpx.AsyncClient | None = None
        # Static-mode aktiveras via samma flag som SportMonks (gemensam env-toggle
        # för pre-augusti-development) ELLER om snapshot-katalog finns.
        self._use_static = (
            settings.sportmonks_use_static_fixtures and self._snapshot_dir.exists()
        )

    # ── Internal helpers ────────────────────────────────────

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=15.0,
                headers=HTTP_HEADERS,
                follow_redirects=True,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def is_static(self) -> bool:
        return self._use_static

    def _league_segment(self, league_external_id: str, source: SourceConfig) -> str:
        seg = LEAGUE_URL_SEGMENTS.get(league_external_id, {}).get(source.name)
        if seg is None:
            raise ProviderUnsupported(
                f"Source {source.name} har ingen URL-mapping för liga "
                f"{league_external_id!r} — utöka LEAGUE_URL_SEGMENTS"
            )
        return seg

    def _load_snapshot(self, source: SourceConfig, operation: str) -> str:
        path = self._snapshot_dir / source.name / f"{operation}.html"
        if not path.exists():
            raise ProviderPayloadError(
                f"Static snapshot saknas: {path}. Kör S-1.2-skörd."
            )
        return path.read_text(encoding="utf-8")

    async def _fetch_html(self, url: str) -> str:
        """Live HTTP GET med standard error-mapping."""
        client = await self._ensure_client()
        try:
            resp = await client.get(url)
        except httpx.HTTPError as exc:
            raise ProviderUnavailable(f"GET {url} failed: {exc}") from exc
        if resp.status_code in (401, 403):
            raise ProviderUnavailable(f"{url} returned {resp.status_code}")
        if resp.status_code == 429:
            raise ProviderUnavailable(f"{url} rate-limited (429)")
        if resp.status_code >= 500:
            raise ProviderUnavailable(f"{url} 5xx: {resp.status_code}")
        if resp.status_code >= 400:
            raise ProviderPayloadError(
                f"{url} returned {resp.status_code}: {resp.text[:200]}"
            )
        return resp.text

    async def _get_html(
        self,
        source: SourceConfig,
        operation: str,
        url: str,
    ) -> str:
        """Static-aware HTML-laddning. Static läser snapshot, live HTTP-GET:ar."""
        if self._use_static:
            return self._load_snapshot(source, operation)
        return await self._fetch_html(url)

    async def _try_sources(
        self,
        operation: str,
        url_builder: Callable[[SourceConfig], str],
        parser: Callable[[BeautifulSoup, SourceConfig], list[Any]],
    ) -> list[Any]:
        """Fallback-cascade — testa varje källa i ordning, returnera första som ger >0 rader.

        Schema-drift-detection: 0 rader på en lyckad fetch = behandlas som
        misslyckande, log + nästa source. Det fångar både parse-fel och
        layout-ändringar.
        """
        last_error: Exception | None = None
        for source in self._sources:
            try:
                url = url_builder(source)
            except ProviderUnsupported as exc:
                logger.info(
                    "skip source %s for %s: %s", source.name, operation, exc
                )
                continue
            try:
                html = await self._get_html(source, operation, url)
            except (ProviderUnavailable, ProviderPayloadError) as exc:
                logger.warning(
                    "source %s failed on %s: %s", source.name, operation, exc
                )
                last_error = exc
                continue
            soup = BeautifulSoup(html, "lxml")
            try:
                rows = parser(soup, source)
            except Exception as exc:  # parser-fel
                logger.warning(
                    "parser %s failed on %s: %s", source.name, operation, exc
                )
                last_error = exc
                continue
            if not rows:
                logger.warning(
                    "source %s returned 0 rows on %s — schema drift?",
                    source.name,
                    operation,
                )
                last_error = ProviderPayloadError(
                    f"{source.name}: 0 rows på {operation}"
                )
                continue
            logger.info(
                "source %s ok on %s — %d rows", source.name, operation, len(rows)
            )
            return rows
        if last_error is None:
            raise ProviderUnavailable(
                f"Alla {len(self._sources)} svenska källor misslyckades på {operation}"
            )
        raise ProviderUnavailable(
            f"Alla {len(self._sources)} svenska källor misslyckades på "
            f"{operation}; senaste fel: {last_error}"
        )

    # ── Parsers (HTML → Normalized*) ────────────────────────

    def _parse_standings_rows(
        self, soup: BeautifulSoup, source: SourceConfig
    ) -> list[dict[str, Any]]:
        """Parse standings-tabell. Returnerar dict-rader; normalizing sker senare."""
        rows = soup.select(source.standings_row_selector)
        out: list[dict[str, Any]] = []
        for row in rows:
            team_el = row.select_one(source.standings_team_selector)
            position_el = row.select_one(source.standings_position_selector)
            played_el = row.select_one(source.standings_played_selector)
            points_el = row.select_one(source.standings_points_selector)
            if not (team_el and position_el and points_el):
                continue
            try:
                position = int((position_el.get_text(strip=True) or "0").rstrip("."))
                points = int(points_el.get_text(strip=True) or "0")
                played = int(played_el.get_text(strip=True) or "0") if played_el else 0
            except ValueError:
                continue
            team_name = team_el.get_text(strip=True)
            if not team_name:
                continue
            out.append(
                {
                    "team_name": team_name,
                    "position": position,
                    "played": played,
                    "points": points,
                    "raw_text": row.get_text(" ", strip=True),
                }
            )
        return out

    def _parse_fixture_rows(
        self, soup: BeautifulSoup, source: SourceConfig
    ) -> list[dict[str, Any]]:
        """Parse fixture-list. Returnerar dict-rader; normalizing sker senare."""
        rows = soup.select(source.fixtures_row_selector)
        out: list[dict[str, Any]] = []
        for row in rows:
            home_el = row.select_one(source.fixtures_home_selector)
            away_el = row.select_one(source.fixtures_away_selector)
            score_el = row.select_one(source.fixtures_score_selector)
            kickoff_el = row.select_one(source.fixtures_kickoff_selector)
            if not (home_el and away_el):
                continue
            kickoff_str: str | None = None
            if kickoff_el:
                kickoff_str = (
                    kickoff_el.get("datetime") or kickoff_el.get_text(strip=True)
                )
            score_text = score_el.get_text(strip=True) if score_el else ""
            home_score: int | None = None
            away_score: int | None = None
            if "-" in score_text or "–" in score_text:
                normalized = score_text.replace("–", "-")
                parts = normalized.split("-")
                if len(parts) == 2:
                    try:
                        home_score = int(parts[0].strip())
                        away_score = int(parts[1].strip())
                    except ValueError:
                        home_score = away_score = None
            out.append(
                {
                    "home_team": home_el.get_text(strip=True),
                    "away_team": away_el.get_text(strip=True),
                    "kickoff_str": kickoff_str,
                    "home_score": home_score,
                    "away_score": away_score,
                }
            )
        return out

    @staticmethod
    def _slugify(name: str) -> str:
        """Slug för team-external-id (källor saknar publika ID:n — slug är canonical)."""
        return (
            name.lower()
            .strip()
            .replace("å", "a")
            .replace("ä", "a")
            .replace("ö", "o")
            .replace(" ", "-")
        )

    @staticmethod
    def _parse_kickoff(value: str | None) -> datetime:
        if not value:
            # Fallback om kickoff saknas — markera som nu, normalizer kan
            # senare flagga som drift
            return datetime.now(timezone.utc)
        # ISO-format först (datetime-attribut)
        try:
            if "T" in value:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
        # SE-textformat: "lör 24 maj 15:00" — placeholder-parser för snapshot-tester.
        # Riktig parser landar i S-1.2 efter Said visat verklig HTML-output.
        return datetime.now(timezone.utc)

    # ── Public Provider API ─────────────────────────────────

    async def fetch_standings(
        self,
        league_external_id: str,
        season: int,
    ) -> list[NormalizedStanding]:
        def url_for(source: SourceConfig) -> str:
            seg = self._league_segment(league_external_id, source)
            template = source.standings_url_template
            url = template.format(league=seg, year=season)
            return f"{source.base_url}{url}"

        rows = await self._try_sources(
            operation="standings",
            url_builder=url_for,
            parser=self._parse_standings_rows,
        )
        return [
            NormalizedStanding(
                league_external_id=league_external_id,
                season_external_id=str(season),
                team_external_id=self._slugify(r["team_name"]),
                position=r["position"],
                points=r["points"],
                played=r["played"],
                won=0,
                drawn=0,
                lost=0,
                goals_for=0,
                goals_against=0,
                form=None,
                zone=None,
            )
            for r in rows
        ]

    async def fetch_fixtures(
        self,
        league_external_id: str,
        season: int,
        window: DateRange | None = None,
    ) -> list[NormalizedFixture]:
        def url_for(source: SourceConfig) -> str:
            seg = self._league_segment(league_external_id, source)
            template = source.fixtures_url_template
            url = template.format(league=seg, year=season, round="")
            return f"{source.base_url}{url}"

        rows = await self._try_sources(
            operation="fixtures",
            url_builder=url_for,
            parser=self._parse_fixture_rows,
        )
        out: list[NormalizedFixture] = []
        for r in rows:
            home_slug = self._slugify(r["home_team"])
            away_slug = self._slugify(r["away_team"])
            kickoff = self._parse_kickoff(r.get("kickoff_str"))
            external_id = f"{home_slug}_vs_{away_slug}_{kickoff.date().isoformat()}"
            status = "FINISHED" if r["home_score"] is not None else "SCHEDULED"
            out.append(
                NormalizedFixture(
                    external_id=external_id,
                    league_external_id=league_external_id,
                    season_external_id=str(season),
                    home_team_external_id=home_slug,
                    away_team_external_id=away_slug,
                    name=f"{r['home_team']} vs {r['away_team']}",
                    kickoff=kickoff,
                    status=status,
                    home_score=r["home_score"],
                    away_score=r["away_score"],
                    raw_payload={"swedish_source": True, **r},
                )
            )
        return out

    async def fetch_live_fixtures(
        self,
        scope: Scope | None = None,
    ) -> list[NormalizedFixture]:
        # Live-fixtures = filtrera fixtures-listan på status. SE-källor uppdaterar
        # in-play-rader sällan — för in-play-data är SportMonksProvider primär.
        # SwedishSourceProvider returnerar bara dagens-/senaste-omgång-rader
        # där score sätts post-final-pip.
        league = (
            scope.value if scope and scope.kind == "league" else "allsvenskan"
        )
        all_fixtures = await self.fetch_fixtures(league, datetime.now().year)
        return [f for f in all_fixtures if f.status == "FINISHED"]

    async def fetch_teams(
        self,
        league_external_id: str,
        season: int,
    ) -> list[NormalizedTeam]:
        # Härleds från standings-listan (varje rad = ett lag).
        standings = await self.fetch_standings(league_external_id, season)
        return [
            NormalizedTeam(
                external_id=s.team_external_id,
                name=s.team_external_id.replace("-", " ").title(),
                short_code=None,
                country_external_id=None,
                founded=None,
                image_ref=None,
                venue_external_id=None,
            )
            for s in standings
        ]

    # ── Operations vi inte stödjer (utan extra HTML-skörd) ──

    async def fetch_fixture_detail(
        self, fixture_external_id: str
    ) -> NormalizedFixture:
        raise ProviderUnsupported(
            "fetch_fixture_detail kräver match-side-snapshot — landar i S-1.4"
        )

    async def fetch_lineup(
        self, fixture_external_id: str
    ) -> NormalizedLineup:
        raise ProviderUnsupported(
            "fetch_lineup ej tillgänglig från SE-källor — använd SportMonks"
        )

    async def fetch_events(
        self, fixture_external_id: str
    ) -> list[NormalizedMatchEvent]:
        raise ProviderUnsupported(
            "fetch_events ej tillgänglig från SE-källor — använd SportMonks"
        )

    async def fetch_statistics(
        self, fixture_external_id: str
    ) -> NormalizedMatchStatistics:
        raise ProviderUnsupported(
            "fetch_statistics ej tillgänglig från SE-källor — använd SportMonks"
        )

    async def fetch_players(
        self, team_external_id: str
    ) -> list[NormalizedPlayer]:
        raise ProviderUnsupported(
            "fetch_players kräver squad-side-snapshot — landar i S-1.4"
        )

    async def stream_live(
        self, scope: Scope | None = None
    ) -> AsyncIterator[LiveEventEnvelope]:
        raise ProviderUnsupported(
            "stream_live ej supporterad — SE-källor är HTTP-poll bara"
        )
        yield  # type: ignore[unreachable]

    async def health(self) -> ProviderHealth:
        if self._use_static:
            # Räkna källor som har snapshots
            available = sum(
                1
                for source in self._sources
                if (self._snapshot_dir / source.name).exists()
            )
            if available == 0:
                return ProviderHealth(
                    provider=self.name,
                    status=ProviderStatus.DISABLED,
                    last_error="Inga snapshots i static-mode",
                )
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.HEALTHY,
                last_error=f"{available}/{len(self._sources)} sources har snapshots",
            )
        # Live: pinga primary
        try:
            await self._fetch_html(self._sources[0].base_url)
            return ProviderHealth(
                provider=self.name, status=ProviderStatus.HEALTHY
            )
        except ProviderUnavailable as exc:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.DEGRADED,
                last_error=str(exc),
            )

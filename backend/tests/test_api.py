"""Smoke tests to verify the app starts correctly."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Verify the health endpoint responds."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "scorelock-api"


@pytest.mark.asyncio
async def test_get_leagues():
    """Verify the leagues endpoint exists."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/leagues")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_fixtures():
    """Verify the fixtures endpoint exists."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/fixtures")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_value_bets():
    """Verify the value bets endpoint exists."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/value-bets")
        assert response.status_code == 200

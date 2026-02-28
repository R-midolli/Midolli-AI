"""
Tests for backend.main — FastAPI endpoints.
"""

import os
import sys

import pytest
import httpx

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.main import app


@pytest.fixture
def client():
    """Create an httpx test client for the FastAPI app."""
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


class TestHealthEndpoint:
    """Tests for GET /health."""

    @pytest.mark.anyio
    async def test_health_returns_200(self, client):
        """GET /health should return 200."""
        async with client as c:
            response = await c.get("/health")
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_health_returns_ok_status(self, client):
        """GET /health should return status: ok."""
        async with client as c:
            response = await c.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "Midolli-AI"


class TestChatEndpoint:
    """Tests for POST /chat."""

    @pytest.mark.anyio
    async def test_chat_valid_message_returns_200(self, client):
        """POST /chat with a valid message should return 200."""
        async with client as c:
            response = await c.post(
                "/chat",
                json={"message": "What are Rafael's projects?", "history": []},
            )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_chat_response_has_reply(self, client):
        """POST /chat should return a response with a reply field."""
        async with client as c:
            response = await c.post(
                "/chat",
                json={"message": "Tell me about Rafael", "history": []},
            )
        data = response.json()
        assert "reply" in data
        assert isinstance(data["reply"], str)
        assert len(data["reply"]) > 0

    @pytest.mark.anyio
    async def test_chat_empty_message_returns_400(self, client):
        """POST /chat with empty message should return 400."""
        async with client as c:
            response = await c.post(
                "/chat", json={"message": "", "history": []}
            )
        assert response.status_code == 400

    @pytest.mark.anyio
    async def test_chat_whitespace_message_returns_400(self, client):
        """POST /chat with whitespace-only message should return 400."""
        async with client as c:
            response = await c.post(
                "/chat", json={"message": "   ", "history": []}
            )
        assert response.status_code == 400

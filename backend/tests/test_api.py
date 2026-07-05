"""Comprehensive backend tests for Genesis AI API."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

pytestmark = pytest.mark.asyncio


# --- Health & Root ---

class TestHealthEndpoints:
    """Test root and health endpoints."""

    async def test_root(self, async_client):
        resp = await async_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "evolving"

    async def test_health(self, async_client):
        resp = await async_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["brain"] == "active"


# --- Memory Endpoints ---

class TestMemoriesEndpoints:
    """Test /memories CRUD."""

    async def test_create_memory(self, async_client):
        resp = await async_client.post("/memories?user_id=test1", json={
            "content": "Test memory content",
            "content_type": "text",
            "tags": ["test"],
            "importance_score": 0.8,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "stored"

    async def test_list_memories(self, async_client):
        await async_client.post("/memories?user_id=test2", json={
            "content": "Memory 1",
        })
        await async_client.post("/memories?user_id=test2", json={
            "content": "Memory 2",
        })
        resp = await async_client.get("/memories?user_id=test2")
        assert resp.status_code == 200
        data = resp.json()
        assert "memories" in data
        assert data["count"] >= 0

    async def test_memory_stats(self, async_client):
        resp = await async_client.get("/memories/stats?user_id=test3")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "by_type" in data


# --- Reflection Endpoints ---

class TestReflectionsEndpoints:
    """Test /reflections endpoints."""

    async def test_create_reflection(self, async_client):
        resp = await async_client.post("/reflections?user_id=test1", json={
            "trigger_event": "Test event",
            "what_worked": "Everything",
            "what_failed": "Nothing",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "reflection" in data
        assert "id" in data

    async def test_list_reflections(self, async_client):
        resp = await async_client.get("/reflections?user_id=test1")
        assert resp.status_code == 200

    async def test_reflection_stats(self, async_client):
        resp = await async_client.get("/reflections/stats/summary?user_id=test1")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data


# --- Prediction Endpoints ---

class TestPredictionsEndpoints:
    """Test /predictions endpoints."""

    async def test_create_prediction(self, async_client):
        resp = await async_client.post("/predictions?user_id=test1&prediction_type=general")
        assert resp.status_code == 201
        data = resp.json()
        assert "prediction" in data

    async def test_list_predictions(self, async_client):
        resp = await async_client.get("/predictions?user_id=test1")
        assert resp.status_code == 200
        data = resp.json()
        assert "predictions" in data

    async def test_prediction_stats(self, async_client):
        resp = await async_client.get("/predictions/stats/summary?user_id=test1")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data


# --- Skill Endpoints ---

class TestSkillsEndpoints:
    """Test /skills endpoints."""

    async def test_list_skills(self, async_client):
        resp = await async_client.get("/skills?user_id=test1")
        assert resp.status_code == 200

    async def test_detect_skills(self, async_client):
        resp = await async_client.post("/skills/detect?user_id=test1")
        assert resp.status_code == 200
        data = resp.json()
        assert "skill_detected" in data

    async def test_skill_stats(self, async_client):
        resp = await async_client.get("/skills/stats/summary?user_id=test1")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data


# --- Dashboard Endpoints ---

class TestDashboardEndpoints:
    """Test /dashboard endpoints."""

    async def test_dashboard(self, async_client):
        resp = await async_client.get("/dashboard?user_id=test1")
        assert resp.status_code == 200
        data = resp.json()
        assert "memory_count" in data
        assert "knowledge_nodes" in data
        assert "brain_health" in data
        assert "evolution_level" in data
        assert data["memory_count"] >= 0


# --- Knowledge Graph Endpoints ---

class TestKnowledgeEndpoints:
    """Test /knowledge endpoints."""

    async def test_knowledge_graph(self, async_client):
        resp = await async_client.get("/knowledge/graph?user_id=test1")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data
        assert "count" in data

    async def test_knowledge_status(self, async_client):
        resp = await async_client.get("/knowledge/status?user_id=test1")
        assert resp.status_code == 200

    async def test_knowledge_search(self, async_client):
        resp = await async_client.get("/knowledge/search?query=test&user_id=test1")
        assert resp.status_code == 200


# --- Upload Endpoints ---

class TestUploadEndpoints:
    """Test /upload endpoints."""

    async def test_supported_types(self, async_client):
        resp = await async_client.get("/upload/supported")
        assert resp.status_code == 200
        data = resp.json()
        assert "allowed_extensions" in data


# --- WebSocket Status ---

class TestWebSocketEndpoints:
    """Test WebSocket status endpoint."""

    async def test_ws_status(self, async_client):
        resp = await async_client.get("/ws/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "active_connections" in data

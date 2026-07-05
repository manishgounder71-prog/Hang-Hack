"""Comprehensive backend tests for Genesis AI API — covering happy paths, error paths, edge cases, and service logic."""
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

    async def test_root_content(self, async_client):
        resp = await async_client.get("/")
        data = resp.json()
        assert data["name"] == "Genesis AI"
        assert "tagline" in data

    async def test_health(self, async_client):
        resp = await async_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["brain"] == "active"

    async def test_health_headers(self, async_client):
        resp = await async_client.get("/health")
        assert resp.headers.get("content-type") == "application/json"


# --- Memory Endpoints ---

class TestMemoriesEndpoints:
    """Test /memories CRUD with happy paths and error cases."""

    async def test_create_memory(self, async_client):
        resp = await async_client.post("/memories?user_id=test_mem", json={
            "content": "Test memory content",
            "content_type": "text",
            "tags": ["test"],
            "importance_score": 0.8,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "stored"

    async def test_create_memory_minimal(self, async_client):
        resp = await async_client.post("/memories?user_id=test_mem", json={
            "content": "Minimal memory",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "stored"

    async def test_create_memory_empty_content(self, async_client):
        resp = await async_client.post("/memories?user_id=test_mem", json={
            "content": "",
        })
        # API accepts empty content; verify it still returns stored status
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "stored"

    async def test_create_memory_missing_content(self, async_client):
        resp = await async_client.post("/memories?user_id=test_mem", json={})
        assert resp.status_code == 422

    async def test_list_memories(self, async_client):
        await async_client.post("/memories?user_id=test_list", json={"content": "M1"})
        await async_client.post("/memories?user_id=test_list", json={"content": "M2"})
        resp = await async_client.get("/memories?user_id=test_list")
        assert resp.status_code == 200
        data = resp.json()
        assert "memories" in data
        assert data["count"] >= 0

    async def test_list_memories_empty(self, async_client):
        resp = await async_client.get("/memories?user_id=nonexistent_user")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["memories"] == []

    async def test_memory_stats(self, async_client):
        resp = await async_client.get("/memories/stats?user_id=test_stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "by_type" in data

    async def test_delete_memory(self, async_client):
        create_resp = await async_client.post("/memories?user_id=test_del", json={
            "content": "To be deleted",
        })
        mem_id = create_resp.json().get("memory_id", "")
        if mem_id:
            resp = await async_client.delete(f"/memories/{mem_id}?user_id=test_del")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "deleted"

    async def test_delete_nonexistent_memory(self, async_client):
        resp = await async_client.delete("/memories/nonexistent-id?user_id=test_del")
        assert resp.status_code == 404


# --- Reflection Endpoints ---

class TestReflectionsEndpoints:
    """Test /reflections endpoints with error cases."""

    async def test_create_reflection(self, async_client):
        resp = await async_client.post("/reflections?user_id=test_ref", json={
            "trigger_event": "Test event",
            "what_worked": "Everything worked well",
            "what_failed": "Nothing failed",
            "improvements": "None needed",
            "patterns": "Consistent behavior",
            "influence_score": 0.7,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "reflection" in data
        assert "id" in data

    async def test_create_reflection_minimal(self, async_client):
        resp = await async_client.post("/reflections?user_id=test_ref", json={
            "trigger_event": "Minimal event",
        })
        assert resp.status_code == 201

    async def test_list_reflections(self, async_client):
        resp = await async_client.get("/reflections?user_id=test_ref")
        assert resp.status_code == 200
        data = resp.json()
        # Returns a list of reflections
        assert isinstance(data, list)

    async def test_list_reflections_empty(self, async_client):
        resp = await async_client.get("/reflections?user_id=nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_reflection_stats(self, async_client):
        resp = await async_client.get("/reflections/stats/summary?user_id=test_ref")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "avg_influence_score" in data

    async def test_delete_reflection(self, async_client):
        create_resp = await async_client.post("/reflections?user_id=test_ref_del", json={
            "trigger_event": "Delete me",
        })
        ref_id = create_resp.json().get("id", "")
        if ref_id:
            resp = await async_client.delete(f"/reflections/{ref_id}?user_id=test_ref_del")
            assert resp.status_code == 200

    async def test_delete_nonexistent_reflection(self, async_client):
        resp = await async_client.delete("/reflections/bad-id?user_id=test_ref")
        assert resp.status_code == 404


# --- Prediction Endpoints ---

class TestPredictionsEndpoints:
    """Test /predictions endpoints with error cases."""

    async def test_create_prediction(self, async_client):
        resp = await async_client.post("/predictions?user_id=test_pred&prediction_type=general")
        assert resp.status_code == 201
        data = resp.json()
        assert "prediction" in data

    async def test_create_prediction_invalid_type(self, async_client):
        resp = await async_client.post("/predictions?user_id=test_pred&prediction_type=invalid_type")
        # API does not validate prediction_type string
        assert resp.status_code == 201
        data = resp.json()
        assert "prediction" in data

    async def test_list_predictions(self, async_client):
        resp = await async_client.get("/predictions?user_id=test_pred")
        assert resp.status_code == 200
        data = resp.json()
        assert "predictions" in data

    async def test_list_predictions_empty(self, async_client):
        resp = await async_client.get("/predictions?user_id=nonexistent_pred")
        assert resp.status_code == 200
        data = resp.json()
        assert data["predictions"] == []

    async def test_prediction_stats(self, async_client):
        resp = await async_client.get("/predictions/stats/summary?user_id=test_pred")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data

    async def test_fulfill_prediction(self, async_client):
        create_resp = await async_client.post("/predictions?user_id=test_pred_ful&prediction_type=general")
        pred_id = create_resp.json().get("prediction", {}).get("id", "")
        if pred_id:
            resp = await async_client.post(f"/predictions/{pred_id}/fulfill?user_id=test_pred_ful")
            assert resp.status_code == 200

    async def test_fulfill_nonexistent_prediction(self, async_client):
        resp = await async_client.post("/predictions/bad-id/fulfill?user_id=test_pred")
        assert resp.status_code == 404


# --- Skill Endpoints ---

class TestSkillsEndpoints:
    """Test /skills endpoints with error cases."""

    async def test_list_skills(self, async_client):
        resp = await async_client.get("/skills?user_id=test_skill")
        assert resp.status_code == 200
        data = resp.json()
        # Returns a list of skills
        assert isinstance(data, list)

    async def test_list_skills_empty(self, async_client):
        resp = await async_client.get("/skills?user_id=nonexistent_skill")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_detect_skills(self, async_client):
        for i in range(3):
            await async_client.post("/memories?user_id=test_skill_detect", json={
                "content": f"Test memory {i} for skill detection",
            })
        resp = await async_client.post("/skills/detect?user_id=test_skill_detect")
        assert resp.status_code == 200
        data = resp.json()
        assert "skill_detected" in data

    async def test_skill_stats(self, async_client):
        resp = await async_client.get("/skills/stats/summary?user_id=test_skill")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "avg_confidence" in data

    async def test_delete_skill(self, async_client):
        resp = await async_client.delete("/skills/bad-id?user_id=test_skill")
        assert resp.status_code == 404

    async def test_update_skill_nonexistent(self, async_client):
        resp = await async_client.put("/skills/bad-id?user_id=test_skill", json={
            "name": "Updated",
            "description": "Updated desc",
            "steps": [],
            "confidence_score": 0.5,
        })
        assert resp.status_code == 404


# --- Dashboard Endpoints ---

class TestDashboardEndpoints:
    """Test /dashboard endpoints."""

    async def test_dashboard(self, async_client):
        resp = await async_client.get("/dashboard?user_id=test_dash")
        assert resp.status_code == 200
        data = resp.json()
        assert "memory_count" in data
        assert "knowledge_nodes" in data
        assert "brain_health" in data
        assert "evolution_level" in data
        assert data["memory_count"] >= 0
        assert "recent_memories" in data
        assert "reflection_count" in data
        assert "prediction_count" in data

    async def test_dashboard_structure(self, async_client):
        resp = await async_client.get("/dashboard?user_id=test_dash")
        data = resp.json()
        assert isinstance(data.get("memory_count"), int)
        assert isinstance(data.get("brain_health"), (int, float))
        assert isinstance(data.get("evolution_level"), int)
        assert isinstance(data.get("weekly_growth"), (int, float))

    async def test_dashboard_empty_user(self, async_client):
        resp = await async_client.get("/dashboard?user_id=brand_new_user")
        assert resp.status_code == 200
        data = resp.json()
        assert data["memory_count"] == 0
        assert data["recent_memories"] == []


# --- Knowledge Graph Endpoints ---

class TestKnowledgeEndpoints:
    """Test /knowledge endpoints."""

    async def test_knowledge_graph(self, async_client):
        resp = await async_client.get("/knowledge/graph?user_id=test_kg")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data

    async def test_knowledge_graph_structure(self, async_client):
        resp = await async_client.get("/knowledge/graph?user_id=test_kg")
        data = resp.json()
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    async def test_knowledge_status(self, async_client):
        resp = await async_client.get("/knowledge/status?user_id=test_kg")
        assert resp.status_code == 200

    async def test_knowledge_search(self, async_client):
        resp = await async_client.get("/knowledge/search?query=test&user_id=test_kg")
        assert resp.status_code == 200

    async def test_knowledge_search_empty(self, async_client):
        resp = await async_client.get("/knowledge/search?query=&user_id=test_kg")
        assert resp.status_code == 200


# --- Upload Endpoints ---

class TestUploadEndpoints:
    """Test /upload endpoints."""

    async def test_supported_types(self, async_client):
        resp = await async_client.get("/upload/supported")
        assert resp.status_code == 200
        data = resp.json()
        assert "allowed_extensions" in data
        assert len(data["allowed_extensions"]) > 0

    async def test_upload_no_file(self, async_client):
        resp = await async_client.post("/upload?user_id=test_up")
        assert resp.status_code == 422


# --- WebSocket Status ---

class TestWebSocketEndpoints:
    """Test WebSocket status endpoint."""

    async def test_ws_status(self, async_client):
        resp = await async_client.get("/ws/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "active_connections" in data
        assert isinstance(data["active_connections"], int)


# --- Chat Endpoints ---

class TestChatEndpoints:
    """Test /chat endpoints."""

    async def test_chat_basic(self, async_client):
        resp = await async_client.post("/chat?user_id=test_chat", json={
            "message": "Hello Genesis",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert len(data["response"]) > 0

    async def test_chat_empty_message(self, async_client):
        resp = await async_client.post("/chat?user_id=test_chat", json={
            "message": "",
        })
        assert resp.status_code in (200, 422)

    async def test_chat_very_long_message(self, async_client):
        long_msg = "test " * 5000
        resp = await async_client.post("/chat?user_id=test_chat", json={
            "message": long_msg,
        })
        assert resp.status_code in (200, 413)


# --- Service Layer Tests ---

class TestReflectionService:
    """Test ReflectionService logic."""

    async def test_generate_reflection(self):
        from app.services.reflection_service import ReflectionService
        svc = ReflectionService()
        result = await svc.generate_reflection(
            trigger_event="test",
            context={"what_worked": "everything", "what_failed": "nothing"},
        )
        assert "what_worked" in result
        assert "what_failed" in result

    async def test_generate_reflection_empty_context(self):
        from app.services.reflection_service import ReflectionService
        svc = ReflectionService()
        result = await svc.generate_reflection(
            trigger_event="test",
            context={},
        )
        assert result is not None


class TestPredictionService:
    """Test PredictionService logic."""

    async def test_generate_prediction(self):
        from app.services.prediction_service import PredictionService
        svc = PredictionService()
        result = await svc.generate_prediction(
            prediction_type="general",
            context={"recent_topics": ["test"]},
        )
        assert "content" in result or "prediction" in result

    async def test_generate_prediction_unknown_type(self):
        from app.services.prediction_service import PredictionService
        svc = PredictionService()
        result = await svc.generate_prediction(
            prediction_type="unknown_type",
            context={},
        )
        assert result is not None


class TestSkillService:
    """Test SkillService logic."""

    async def test_detect_skill_pattern(self):
        from app.services.skill_service import SkillService
        svc = SkillService()
        result = await svc.detect_skill_pattern(
            memories=[
                {"content": "test memory 1", "content_type": "chat_message"},
                {"content": "test memory 2", "content_type": "chat_message"},
                {"content": "test memory 3", "content_type": "chat_message"},
            ],
        )
        assert result is not None


class TestGenesisEngine:
    """Test GenesisEngine logic."""

    @patch("app.services.genesis_engine.rag_store")
    @patch("app.services.genesis_engine.remember_content")
    @patch("app.services.genesis_engine.llm")
    async def test_process_message(self, mock_llm, mock_remember, mock_rag, db_session):
        mock_llm.chat = AsyncMock(return_value="Test response")
        mock_rag.store = AsyncMock(return_value=None)
        mock_rag.query = AsyncMock(return_value=[])
        mock_remember.return_value = {"status": "stored"}

        from app.services.genesis_engine import GenesisEngine
        engine = GenesisEngine()
        result = await engine.process_message("Hello", "test_user", db_session)
        assert result["response"] == "Test response"
        assert "memories_used" in result

    @patch("app.services.genesis_engine.rag_store")
    @patch("app.services.genesis_engine.remember_content")
    @patch("app.services.genesis_engine.llm")
    async def test_process_message_llm_failure(self, mock_llm, mock_remember, mock_rag, db_session):
        mock_llm.chat = AsyncMock(side_effect=Exception("LLM down"))
        mock_rag.store = AsyncMock(return_value=None)
        mock_rag.query = AsyncMock(return_value=[])
        mock_remember.return_value = {"status": "stored"}

        from app.services.genesis_engine import GenesisEngine
        engine = GenesisEngine()
        result = await engine.process_message("Hello", "test_user", db_session)
        assert "response" in result
        assert "LLM" not in result["response"]


# --- Edge Cases ---

class TestEdgeCases:
    """Test edge cases across the API."""

    async def test_invalid_endpoint(self, async_client):
        resp = await async_client.get("/nonexistent")
        assert resp.status_code == 404

    async def test_invalid_method(self, async_client):
        resp = await async_client.put("/health")
        assert resp.status_code == 405

    async def test_malformed_json(self, async_client):
        resp = await async_client.post("/memories?user_id=test", content=b"not json",
                                       headers={"Content-Type": "application/json"})
        assert resp.status_code == 422

    async def test_xss_injection(self, async_client):
        resp = await async_client.post("/memories?user_id=test_xss", json={
            "content": "<script>alert('xss')</script>",
        })
        assert resp.status_code == 201

    async def test_sql_injection_attempt(self, async_client):
        resp = await async_client.post("/memories?user_id=test_sqli", json={
            "content": "'; DROP TABLE memories; --",
        })
        assert resp.status_code == 201

    async def test_unicode_content(self, async_client):
        resp = await async_client.post("/memories?user_id=test_unicode", json={
            "content": "你好世界 🌍",
        })
        assert resp.status_code == 201


# --- Settings Endpoints ---

class TestSettingsEndpoints:
    """Test /settings endpoints."""

    async def test_get_settings(self, async_client):
        resp = await async_client.get("/settings?user_id=test_set")
        assert resp.status_code == 200
        data = resp.json()
        # Settings response contains preference fields (not user_id)
        assert isinstance(data, dict)
        assert "memory_aware_responses" in data or "memory_aware" in data

    async def test_update_settings(self, async_client):
        resp = await async_client.put("/settings?user_id=test_set", json={
            "user_id": "test_set",
            "memory_aware": True,
            "auto_reflect": False,
        })
        assert resp.status_code == 200

    async def test_reset_settings(self, async_client):
        resp = await async_client.post("/settings/reset?user_id=test_set")
        assert resp.status_code == 200

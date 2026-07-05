"""Test fixtures for Genesis AI backend."""
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["AUTH_ENABLED"] = "False"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.database import get_session
from app.models.memory import Base
from app.main import app
from unittest.mock import AsyncMock, patch, MagicMock

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_session():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_session] = override_get_session
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def mock_redis_cache():
    with patch("app.core.cache.cache.get", new_callable=AsyncMock) as mock_get, \
         patch("app.core.cache.cache.set", new_callable=AsyncMock) as mock_set, \
         patch("app.core.cache.cache.initialize", new_callable=AsyncMock, return_value=True) as mock_init, \
         patch("app.core.cache.cache.close", new_callable=AsyncMock) as mock_close, \
         patch("app.core.cache.cache.invalidate_dashboard", new_callable=AsyncMock) as mock_inv_dash, \
         patch("app.core.cache.cache.invalidate_memories", new_callable=AsyncMock) as mock_inv_mem, \
         patch("app.core.cache.cache.get_memories", new_callable=AsyncMock, return_value=None) as mock_get_mems, \
         patch("app.core.cache.cache.cache_memories", new_callable=AsyncMock) as mock_cache_mems:
        mock_get.return_value = None
        yield


@pytest_asyncio.fixture(autouse=True)
async def mock_cognee_calls():
    with patch("app.core.cognee_client.remember_content", new_callable=AsyncMock) as mock_remember, \
         patch("app.core.cognee_client.recall_memories", new_callable=AsyncMock) as mock_recall, \
         patch("app.core.cognee_client.improve_memories", new_callable=AsyncMock) as mock_improve, \
         patch("app.core.cognee_client.forget_dataset", new_callable=AsyncMock) as mock_forget, \
         patch("app.core.cognee_client.get_knowledge_graph", new_callable=AsyncMock) as mock_graph, \
         patch("app.core.cognee_client.get_cognee_status", new_callable=AsyncMock) as mock_status, \
         patch("app.core.cognee_client.get_memory_stats", new_callable=AsyncMock) as mock_stats:

        mock_remember.return_value = {"cognee_id": "test-cognee-id", "content": "test", "dataset": "test", "stored": True}
        mock_recall.return_value = []
        mock_improve.return_value = {"status": "improved", "result": "mock"}
        mock_forget.return_value = {"status": "forgotten", "dataset": "test", "result": "mock"}
        mock_graph.return_value = {"nodes": [], "edges": [], "source": "cognee", "count": 0}
        mock_status.return_value = {"available": True, "mode": "live", "dataset": "test"}
        mock_stats.return_value = {"memory_count": 0, "knowledge_nodes": 0, "relationships": 0, "recent_memories": []}
        yield


@pytest_asyncio.fixture(autouse=True)
async def mock_llm_client():
    with patch("app.core.llm.LLMClient.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = (
            '{"what_worked": "worked", "what_failed": "failed", "improvements": "improve", '
            '"patterns": "pattern", "influence_score": 0.8, "prediction": "predict", '
            '"prediction_type": "general", "confidence": 0.9, "reasoning": "reason", '
            '"skill_detected": true, "name": "skill", "description": "desc", '
            '"steps": [{"step": 1}]}'
        )
        yield


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session

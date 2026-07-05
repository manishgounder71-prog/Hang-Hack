"""Seed script — Pre-populates the database with sample Genesis AI data.
Run this after `docker compose up` to show judges a working system immediately.

Usage:
    python backend/seed_data.py

This requires a running database and optionally a Cognee API key.
It will create sample memories, reflections, predictions, and skills
that demonstrate the full Genesis AI feature set.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import select as sa_select
from app.core.database import get_session, init_db
from app.models.memory import User, Memory, Reflection, Prediction, Skill


DEMO_MEMORIES = [
    {"content": "Started building Genesis AI for the WeMakeDevs x Cognee Hackathon. Tech stack: FastAPI, Next.js, PostgreSQL, Redis, and Cognee for persistent memory.", "content_type": "project", "tags": ["hackathon", "genesis", "cognee"], "importance_score": 1.0},
    {"content": "Integrated Cognee remember/recall lifecycle into the memory system. Every chat message is now stored persistently with semantic search.", "content_type": "achievement", "tags": ["cognee", "integration", "memory"], "importance_score": 0.95},
    {"content": "Built the Three.js 3D knowledge graph visualization with force-directed layout, particle flows, and interactive node selection.", "content_type": "achievement", "tags": ["threejs", "visualization", "3d"], "importance_score": 0.9},
    {"content": "Implemented real-time WebSocket updates. When memories are created, all connected clients get instant stats_updated events.", "content_type": "achievement", "tags": ["websocket", "realtime"], "importance_score": 0.85},
    {"content": "Added Redis caching layer with CacheService class. Dashboard data cached at 60s, memories at 120s, with cache invalidation on mutations.", "content_type": "project", "tags": ["redis", "caching", "performance"], "importance_score": 0.8},
    {"content": "Created the multi-agent system with independent Memory, Reflection, Prediction, Knowledge Graph, and Learning agents communicating through an event bus.", "content_type": "project", "tags": ["agents", "architecture", "event-bus"], "importance_score": 0.95},
    {"content": "Designed the glassmorphism UI with Framer Motion animations, noise texture backgrounds, and gradient orbs for the dark theme.", "content_type": "project", "tags": ["ui", "design", "animations"], "importance_score": 0.75},
    {"content": "File upload system supports PDF, DOCX, PPTX, CSV, and code files. Text is extracted and stored in Cognee memory automatically.", "content_type": "feature", "tags": ["upload", "files", "parsing"], "importance_score": 0.8},
    {"content": "Wrote 20+ test cases covering all API endpoints including auth, memories, reflections, predictions, skills, dashboard, knowledge graph, and upload.", "content_type": "milestone", "tags": ["testing", "quality"], "importance_score": 0.7},
    {"content": "Dockerized the entire stack with docker-compose: PostgreSQL with pgvector, Redis 7, FastAPI backend, and Next.js frontend.", "content_type": "project", "tags": ["docker", "deployment", "infrastructure"], "importance_score": 0.85},
    {"content": "Learned how to integrate Cognee's cognify() for automatic knowledge graph construction from stored memories.", "content_type": "learning", "tags": ["cognee", "learning"], "importance_score": 0.65},
    {"content": "Discovered that force-directed layout O(n²) repulsion calculations can be slow with 100+ nodes. Optimized by limiting iterations to 50.", "content_type": "reflection", "tags": ["optimization", "performance"], "importance_score": 0.6},
    {"content": "The SSE streaming chat works by reading the response body with a ReadableStream reader and parsing SSE data: lines.", "content_type": "learning", "tags": ["streaming", "sse"], "importance_score": 0.6},
    {"content": "Session management in FastAPI requires proper async patterns — using async with for database sessions and yield in dependency injection.", "content_type": "learning", "tags": ["fastapi", "async"], "importance_score": 0.55},
    {"content": "Optimized the entire project — dynamic imports, DB indexes, code deduplication, Docker build improvements, and removed legacy auth system.", "content_type": "milestone", "tags": ["optimization", "performance", "cleanup"], "importance_score": 0.75},
]

DEMO_REFLECTIONS = [
    {"trigger_event": "Cognee integration completed", "what_worked": "Cognee's API is well-documented and the remember/recall pattern is intuitive. The dual persistence with SQLAlchemy provides a good fallback.", "what_failed": "Initial setup required understanding both graph and vector concepts. Error handling for Cognee downtime needed careful implementation.", "influence_score": 0.85},
    {"trigger_event": "3D visualization built", "what_worked": "React Three Fiber made Three.js integration straightforward. The force layout algorithm produces organic-looking graphs.", "what_failed": "Performance with large graphs is a concern. Need LOD (level of detail) for 200+ nodes.", "influence_score": 0.72},
    {"trigger_event": "WebSocket implementation", "what_worked": "FastAPI WebSocket support is solid. The connection manager pattern with broadcast and personal messaging is clean.", "what_failed": "Reconnection logic was tricky — exponential backoff with jitter was needed to prevent thundering herd.", "influence_score": 0.78},
    {"trigger_event": "Hackathon project planning", "what_worked": "Starting with a clear architecture diagram saved time. The multi-agent system design was well thought out.", "what_failed": "Scope creep was a challenge — had to cut several planned features to focus on core functionality.", "influence_score": 0.65},
]

DEMO_PREDICTIONS = [
    {"content": "User will explore AI agent orchestration patterns within the next week", "prediction_type": "learning", "confidence": 0.82, "fulfilled": True},
    {"content": "The project will need vector search optimization for memory retrieval at scale", "prediction_type": "technology", "confidence": 0.75, "fulfilled": False},
    {"content": "A new skill for 'FastAPI async pattern implementation' will be detected", "prediction_type": "skill", "confidence": 0.68, "fulfilled": True},
    {"content": "User may be interested in Pydantic v2 migration patterns soon", "prediction_type": "general", "confidence": 0.6, "fulfilled": False},
    {"content": "Knowledge graph will grow to 50+ nodes within the next 3 days of active use", "prediction_type": "project", "confidence": 0.7, "fulfilled": False},
]

DEMO_SKILLS = [
    {"name": "FastAPI Async Pattern", "description": "Reusable pattern for implementing async endpoints with proper session management, error handling, and response serialization.", "steps": ["Define Pydantic schemas with ConfigDict", "Create async router with dependency injection", "Implement CRUD with proper try/except/finally", "Add response_model for auto-serialization"], "confidence_score": 0.85, "usage_count": 12},
    {"name": "Cognee Memory Lifecycle", "description": "End-to-end pattern for integrating Cognee's remember/recall/improve/forget APIs with dual persistence to SQLAlchemy.", "steps": ["Initialize Cognee client with API key", "Store content via remember() with metadata", "Query via recall() with semantic search", "Dual-write to SQLAlchemy for relational queries", "Handle Cognee downtime with graceful fallback"], "confidence_score": 0.92, "usage_count": 8},
    {"name": "Three.js Data Visualization", "description": "Pattern for embedding interactive Three.js 3D visualizations in React with force-directed layouts and OrbitControls.", "steps": ["Set up Canvas with React Three Fiber", "Create force layout simulation in useMemo", "Build interactive NodeSphere components", "Add edge tubes with ParticleFlow animations", "Wire OrbitControls for user interaction"], "confidence_score": 0.78, "usage_count": 5},
    {"name": "Real-time WebSocket Updates", "description": "Pattern for broadcasting real-time updates from FastAPI backend to React frontend via WebSocket with auto-reconnect.", "steps": ["Create WebSocket endpoint with ConnectionManager", "Implement broadcast/personal messaging methods", "Build useWebSocket hook with exponential backoff", "Wire stats_updated events to trigger refetches"], "confidence_score": 0.81, "usage_count": 6},
]

USER_ID = "default"
USER_EMAIL = "demo@genesis-ai.dev"
USER_USERNAME = "genesis_demo"


async def seed():
    print("[Seed] Seeding Genesis AI database with demo data...\n")

    await init_db()

    async for session in get_session():
        # Check if already seeded
        existing = await session.execute(
            sa_select(Memory).where(Memory.user_id == USER_ID).limit(1)
        )
        if existing.scalar_one_or_none():
            print("  [Skip] Database already seeded. Skipping.")
            print("\n[OK] Seed complete - database already contains demo data.\n")
            return

        # Insert memories
        print(f"  [Write] Creating {len(DEMO_MEMORIES)} memories...")
        for m in DEMO_MEMORIES:
            session.add(Memory(
                user_id=USER_ID,
                content=m["content"],
                content_type=m["content_type"],
                tags=m["tags"],
                importance_score=m["importance_score"],
            ))

        # Insert reflections
        print(f"  [Search] Creating {len(DEMO_REFLECTIONS)} reflections...")
        for r in DEMO_REFLECTIONS:
            session.add(Reflection(
                user_id=USER_ID,
                trigger_event=r["trigger_event"],
                what_worked=r["what_worked"],
                what_failed=r["what_failed"],
                influence_score=r["influence_score"],
            ))

        # Insert predictions
        print(f"  [Predict] Creating {len(DEMO_PREDICTIONS)} predictions...")
        for p in DEMO_PREDICTIONS:
            session.add(Prediction(
                user_id=USER_ID,
                content=p["content"],
                prediction_type=p["prediction_type"],
                confidence=p["confidence"],
                is_fulfilled=1 if p["fulfilled"] else 0,
            ))

        # Insert skills
        print(f"  [Build] Creating {len(DEMO_SKILLS)} skills...")
        for s in DEMO_SKILLS:
            session.add(Skill(
                user_id=USER_ID,
                name=s["name"],
                description=s["description"],
                steps=s["steps"],
                confidence_score=s["confidence_score"],
                usage_count=s["usage_count"],
            ))

        await session.flush()
        print("\n[OK] Seed complete! Demo data populated successfully.\n")
        print(f"   • {len(DEMO_MEMORIES)} memories")
        print(f"   • {len(DEMO_REFLECTIONS)} reflections")
        print(f"   • {len(DEMO_PREDICTIONS)} predictions")
        print(f"   • {len(DEMO_SKILLS)} skills")
        print("\n   Open http://localhost:3000 to see the dashboard ready to go!")

    print("\n[Info] To seed Cognee as well (requires API key):")
    print("   python scripts/seed_cognee.py")


if __name__ == "__main__":
    asyncio.run(seed())

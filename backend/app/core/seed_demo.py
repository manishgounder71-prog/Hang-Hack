"""Demo seed script — pre-populates Genesis with impressive demo data for judge walkthrough."""
import asyncio
import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory, Skill, Reflection, Prediction, KnowledgeNode
from app.core.rag import rag_store

logger = logging.getLogger(__name__)

DEMO_USER = "demo"

DEMO_CONVERSATION = [
    ("user", "I'm planning a next-generation web application called Project Helios using Svelte."),
    ("assistant", "Project Helios sounds exciting! A Svelte-based web app gives you great performance and developer experience. What problem are you solving? I've noted this project in my memory for future reference."),
    ("user", "We're building a real-time collaborative design tool. Think Figma but for UI developers, with code export."),
    ("assistant", "That's a great concept. Real-time collaboration with Svelte's reactivity model is a natural fit. I see this has architectural similarities to the internship management system you built previously — both need auth, real-time sync, and role-based access. Would you like me to pull in patterns from that earlier project?"),
    ("user", "Yes! That internship system had a great auth module. Let me reuse that pattern."),
    ("assistant", "Perfect. I'll reference the auth patterns from your internship management system. Key things to carry forward: JWT-based auth with refresh tokens, role-based access control with 3 tiers (admin, manager, user), and the WebSocket-based session management. I'm storing this relationship between your projects in the knowledge graph."),
    ("user", "We chose PostgreSQL with vector search for our design asset database."),
    ("assistant", "PostgreSQL with pgvector is solid for storing design assets with similarity search — your designers can search by visual similarity. I've added this to Project Helios's tech stack in the knowledge graph. Connected it to Svelte, real-time collaboration, JWT auth, and the internship system reference."),
    ("user", "How do you think I should handle real-time conflict resolution for simultaneous editing?"),
    ("assistant", "Based on your past projects and common patterns in collaborative tools, I recommend Operational Transform (OT) over CRDT for your use case — you already have a central server with PostgreSQL, so OT is simpler to implement. However, if you expect offline editing support, CRDT would be better. The knowledge graph shows you've used WebSocket-based sync before, so either approach builds on existing infrastructure."),
    ("user", "Let's go with OT. Start scaffolding the backend structure."),
    ("assistant", "Great choice. I'm creating a skill pattern from this conversation — 'Svelte Real-Time App Scaffold' — so next time you start a similar project, I can generate the boilerplate automatically. Knowledge graph, database schema, and project structure are being logged now."),
    ("user", "I'm switching to Kubernetes for deployment instead of Docker Compose."),
    ("assistant", "Good Move! Kubernetes gives you better scaling for a real-time collaborative tool. I'm updating Project Helios's deployment config in the knowledge graph. Noted: you prefer K8s for production-grade apps. I'll remember this for future project recommendations."),
    ("user", "I need to hire a freelancer who knows Svelte and real-time systems."),
    ("assistant", "Based on your memory, I know you need: Svelte expertise, WebSocket/real-time experience, OT algorithm familiarity, PostgreSQL knowledge. I've stored this hiring profile. When you come back, I'll help you draft the job description with the exact tech stack requirements."),
]

DEMO_MEMORIES_TOO = [
    "I built an internship management system with FastAPI, SQLAlchemy, and React last quarter. It had JWT auth, role-based access, and WebSocket notifications.",
    "My preferred stack is Svelte for frontend, FastAPI for backend, PostgreSQL for data, and Redis for caching.",
    "I won a hackathon last year with a real-time collaborative whiteboard app.",
    "I contribute to open source — mainly Svelte ecosystem projects and Python async tooling.",
    "I've deployed production apps on both AWS ECS and DigitalOcean App Platform.",
    "I value clean architecture, thorough testing, and good developer experience.",
    "I'm learning Rust for systems programming in my spare time.",
    "I previously built a SolarTracker IoT system with Raspberry Pi and Python.",
]

DEMO_SKILLS = [
    {
        "name": "Svelte Real-Time App Scaffold",
        "description": "Scaffolds a Svelte + FastAPI real-time collaborative application with auth, WebSocket, and PostgreSQL",
        "steps": ["Initialize SvelteKit with TypeScript", "Set up FastAPI backend with WebSocket support", "Configure JWT auth with refresh tokens", "Set up PostgreSQL with SQLAlchemy async", "Create real-time sync layer with OT"],
        "confidence_score": 0.85,
        "use_count": 2,
        "category": "web-development",
    },
    {
        "name": "Full-Stack Auth Module",
        "description": "JWT-based authentication with refresh tokens, role-based access control, and session management",
        "steps": ["Implement JWT token generation with RS256", "Create refresh token rotation", "Set up role-based middleware", "Add rate limiting to auth endpoints", "Implement session invalidation"],
        "confidence_score": 0.92,
        "use_count": 4,
        "category": "backend",
    },
    {
        "name": "Real-Time Collaboration Setup",
        "description": "WebSocket-based real-time sync with Operational Transform for collaborative editing",
        "steps": ["Set up WebSocket connections with FastAPI", "Implement OT algorithm for text operations", "Add presence detection", "Handle conflict resolution", "Create version history with diffs"],
        "confidence_score": 0.78,
        "use_count": 1,
        "category": "realtime",
    },
]

DEMO_REFLECTIONS = [
    {
        "trigger_event": "Project Helios architecture discussion",
        "what_worked": "Successfully cross-referenced internship management system patterns for Project Helios. Auth module reuse identified and recommended.",
        "what_failed": "Initial response about CRDT vs OT was too technical — user wanted a clear recommendation, not a comparison. Could have been more decisive.",
        "improvements": "Lead with a recommendation, then explain alternatives. Use the knowledge graph to find analogous past decisions faster.",
        "patterns": "User prefers concrete recommendations over options. User reuses proven patterns from past projects.",
        "influence_score": 0.85,
    },
    {
        "trigger_event": "Tech stack discussion",
        "what_worked": "Correctly identified user's preferred stack and applied it to the new project context. Knowledge graph linked SolarTracker IoT and internship system to Helios.",
        "what_failed": "Didn't proactively surface the Kubernetes preference from earlier in the conversation when discussing deployment.",
        "improvements": "Cache the most recent architectural decisions per project and surface them before the user asks.",
        "patterns": "User has consistent tech stack preferences. User documents decisions in conversations that should be captured as project metadata.",
        "influence_score": 0.72,
    },
]

DEMO_PREDICTIONS = [
    {
        "prediction_type": "project",
        "content": "Project Helios will need a real-time sync benchmark suite within 2 weeks of starting development.",
        "confidence": 0.88,
        "reasoning": "Previous projects followed a test-first pattern. Real-time sync is the riskiest component — user will validate it early.",
        "is_fulfilled": False,
    },
    {
        "prediction_type": "skill",
        "content": "User will develop expertise in Kubernetes deployment within 3 months based on the Helios infrastructure choice.",
        "confidence": 0.75,
        "reasoning": "Switching from Docker Compose to Kubernetes indicates a learning investment. Past behavior shows deep-dive learning pattern.",
        "is_fulfilled": False,
    },
    {
        "prediction_type": "learning",
        "content": "User will explore CRDT libraries within 6 months when offline editing becomes a requirement for Helios.",
        "confidence": 0.65,
        "reasoning": "Chose OT over CRDT for now, but collaborative tools inevitably need offline support as they mature.",
        "is_fulfilled": False,
    },
]

DEMO_KNOWLEDGE_NODES = [
    {"label": "Project Helios", "node_type": "project", "importance": 0.95},
    {"label": "Svelte", "node_type": "technology", "importance": 0.9},
    {"label": "FastAPI", "node_type": "technology", "importance": 0.85},
    {"label": "PostgreSQL", "node_type": "technology", "importance": 0.8},
    {"label": "Operational Transform", "node_type": "concept", "importance": 0.7},
    {"label": "Kubernetes", "node_type": "technology", "importance": 0.75},
    {"label": "WebSocket", "node_type": "concept", "importance": 0.7},
    {"label": "JWT Auth", "node_type": "concept", "importance": 0.65},
    {"label": "Internship System", "node_type": "project", "importance": 0.8},
    {"label": "SolarTracker IoT", "node_type": "project", "importance": 0.6},
    {"label": "Rust", "node_type": "language", "importance": 0.5},
    {"label": "Real-Time Sync", "node_type": "concept", "importance": 0.7},
]


async def seed_demo_data(session: AsyncSession):
    existing = await session.execute(select(Memory).where(Memory.user_id == DEMO_USER).limit(1))
    if existing.scalar_one_or_none():
        logger.info("Demo data already seeded — skipping")
        return {"status": "already_seeded"}

    for role, content in DEMO_CONVERSATION:
        mem = Memory(
            user_id=DEMO_USER,
            content=content,
            content_type="chat_message" if role == "user" else "chat_response",
            importance_score=0.8 if role == "user" else 0.6,
            metadata={"direction": role, "demo": True},
        )
        session.add(mem)
    await session.flush()

    for content in DEMO_MEMORIES_TOO:
        mem = Memory(
            user_id=DEMO_USER,
            content=content,
            content_type="chat_message",
            importance_score=0.5,
            metadata={"direction": "user", "demo": True},
        )
        session.add(mem)
    await session.flush()

    for skill_data in DEMO_SKILLS:
        skill = Skill(
            user_id=DEMO_USER,
            name=skill_data["name"],
            description=skill_data["description"],
            steps=skill_data["steps"],
            confidence_score=skill_data["confidence_score"],
            use_count=skill_data["use_count"],
            category=skill_data["category"],
        )
        session.add(skill)

    for ref_data in DEMO_REFLECTIONS:
        ref = Reflection(
            user_id=DEMO_USER,
            trigger_event=ref_data["trigger_event"],
            what_worked=ref_data["what_worked"],
            what_failed=ref_data["what_failed"],
            improvements=ref_data["improvements"],
            patterns=ref_data["patterns"],
            influence_score=ref_data["influence_score"],
            metadata={"demo": True},
        )
        session.add(ref)

    for pred_data in DEMO_PREDICTIONS:
        pred = Prediction(
            user_id=DEMO_USER,
            prediction_type=pred_data["prediction_type"],
            content=pred_data["content"],
            confidence=pred_data["confidence"],
            reasoning=pred_data["reasoning"],
            is_fulfilled=pred_data["is_fulfilled"],
        )
        session.add(pred)

    for node_data in DEMO_KNOWLEDGE_NODES:
        node = KnowledgeNode(
            user_id=DEMO_USER,
            label=node_data["label"],
            node_type=node_data["node_type"],
            importance=node_data["importance"],
        )
        session.add(node)

    await session.commit()
    logger.info(f"Demo data seeded for user '{DEMO_USER}'")

    for role, content in DEMO_CONVERSATION:
        try:
            await rag_store.store(content, user_id=DEMO_USER, session=session)
        except Exception:
            pass
    for content in DEMO_MEMORIES_TOO:
        try:
            await rag_store.store(content, user_id=DEMO_USER, session=session)
        except Exception:
            pass

    return {
        "status": "seeded",
        "stats": {
            "memories": len(DEMO_CONVERSATION) + len(DEMO_MEMORIES_TOO),
            "skills": len(DEMO_SKILLS),
            "reflections": len(DEMO_REFLECTIONS),
            "predictions": len(DEMO_PREDICTIONS),
            "knowledge_nodes": len(DEMO_KNOWLEDGE_NODES),
        },
    }

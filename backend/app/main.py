from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import chat, memories, reflections, predictions, skills, knowledge, dashboard, upload, websocket
from app.api import settings as settings_router
from app.agents.event_bus import event_bus
from app.agents.memory_agent import MemoryAgent
from app.agents.reflection_agent import ReflectionAgent
from app.agents.prediction_agent import PredictionAgent
from app.agents.knowledge_agent import KnowledgeGraphAgent
from app.agents.learning_agent import LearningAgent
from app.core.cache import cache
from app.core.cognee_client import init_cognee
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register agents
    event_bus.subscribe("memory", MemoryAgent())
    event_bus.subscribe("reflection", ReflectionAgent())
    event_bus.subscribe("prediction", PredictionAgent())
    event_bus.subscribe("knowledge", KnowledgeGraphAgent())
    event_bus.subscribe("learning", LearningAgent())
    # Initialize Cognee
    try:
        result = await init_cognee()
        print(f"Cognee init: {result.get('status', 'unknown')}")
    except Exception as e:
        print(f"Cognee init skipped: {e}")
    # Initialize database
    try:
        await init_db()
        print("Database initialized")
    except Exception as e:
        print(f"DB init skipped: {e}")
    # Initialize Redis cache
    try:
        ok = await cache.initialize()
        if ok:
            print("Redis cache initialized")
        else:
            print("Redis cache unavailable — running without")
    except Exception as e:
        print(f"Cache init skipped: {e}")
    yield
    # Cleanup cache on shutdown
    await cache.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat.router)
app.include_router(memories.router)
app.include_router(reflections.router)
app.include_router(predictions.router)
app.include_router(skills.router)
app.include_router(knowledge.router)
app.include_router(dashboard.router)
app.include_router(upload.router)
app.include_router(websocket.router)
app.include_router(settings_router.router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "evolving",
        "tagline": "The AI That Evolves Because It Remembers",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "brain": "active"}

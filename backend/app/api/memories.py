from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.memory import MemoryCreate, MemoryResponse
from app.core.cognee_client import remember_content, recall_memories, improve_memories, forget_dataset
from app.core.database import get_session
from app.core.cache import cache
from app.api.websocket import manager
from app.models.memory import Memory

router = APIRouter(prefix="/memories", tags=["memories"])


@router.post("", status_code=201)
async def create_memory(
    memory: MemoryCreate,
    user_id: str = Query("default"),
    session: AsyncSession = Depends(get_session),
):
    # Persist to Cognee
    cognee_result = await remember_content(
        content=memory.content,
        content_type=memory.content_type,
        user_id=user_id,
        metadata={"tags": memory.tags, "importance": memory.importance_score},
    )

    # Dual persist to SQLAlchemy
    db_memory = Memory(
        user_id=user_id,
        content=memory.content,
        content_type=memory.content_type,
        importance_score=memory.importance_score,
        tags=memory.tags,
        cognee_id=cognee_result.get("cognee_id"),
    )
    session.add(db_memory)

    # Invalidate caches for this user (dashboard + memories)
    await cache.invalidate_dashboard(user_id)
    await cache.invalidate_memories(user_id)

    # Broadcast real-time update via WebSocket
    await manager.broadcast({
        "type": "stats_updated",
        "entity": "memory",
        "action": "created",
        "user_id": user_id,
    })

    return {
        "status": "stored",
        "id": cognee_result.get("cognee_id"),
        "content": memory.content[:100],
        "mode": cognee_result.get("mode", "live"),
    }


@router.get("")
async def get_memories(
    query: str = Query(""),
    user_id: str = Query("default"),
    limit: int = Query(10),
    session: AsyncSession = Depends(get_session),
    force_refresh: bool = Query(False),
):
    # Check cache for DB results (skip for Cognee-backed semantic search)
    if not query and not force_refresh:
        cached = await cache.get_memories(user_id, query, limit)
        if cached is not None:
            return {"memories": cached, "count": len(cached), "source": "cache"}

    # Try Cognee recall first for semantic queries
    if query:
        cognee_results = await recall_memories(query, user_id=user_id, limit=limit)
        if cognee_results:
            return {"memories": cognee_results, "count": len(cognee_results), "source": "cognee"}

    # Fallback to SQLAlchemy
    stmt = (
        select(Memory)
        .where(Memory.user_id == user_id)
        .order_by(Memory.created_at.desc())
        .limit(limit)
    )
    if query:
        stmt = stmt.where(Memory.content.ilike(f"%{query}%"))

    result = await session.execute(stmt)
    memories = result.scalars().all()

    serialized = [
        {
            "id": m.id,
            "content": m.content,
            "content_type": m.content_type,
            "importance_score": m.importance_score,
            "emotional_weight": m.emotional_weight,
            "tags": m.tags,
            "entities": m.entities,
            "cognee_id": m.cognee_id,
            "created_at": str(m.created_at),
        }
        for m in memories
    ]

    # Cache for non-query results only
    if not query:
        await cache.cache_memories(user_id, query, limit, serialized, ttl=120)

    return {"memories": serialized, "count": len(serialized), "source": "database"}


@router.get("/stats")
async def memory_stats(
    user_id: str = Query("default"),
    session: AsyncSession = Depends(get_session),
    force_refresh: bool = Query(False),
):
    # Check cache
    if not force_refresh:
        cached = await cache.get_memory_stats(user_id)
        if cached is not None:
            return cached

    count_result = await session.execute(
        select(func.count(Memory.id)).where(Memory.user_id == user_id)
    )
    total = count_result.scalar() or 0

    type_result = await session.execute(
        select(Memory.content_type, func.count(Memory.id))
        .where(Memory.user_id == user_id)
        .group_by(Memory.content_type)
    )
    by_type = {row[0]: row[1] for row in type_result.all()}

    data = {"total": total, "by_type": by_type}

    # Cache for 2 minutes
    await cache.cache_memory_stats(user_id, data, ttl=120)
    return data


@router.get("/{memory_id}")
async def get_memory(
    memory_id: str,
    session: AsyncSession = Depends(get_session),
):
    # Try cache
    cache_key = f"memories:single:{memory_id}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached

    result = await session.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    data = {
        "id": memory.id,
        "content": memory.content,
        "content_type": memory.content_type,
        "importance_score": memory.importance_score,
        "emotional_weight": memory.emotional_weight,
        "tags": memory.tags,
        "entities": memory.entities,
        "cognee_id": memory.cognee_id,
        "created_at": str(memory.created_at),
        "metadata": memory.meta_data,
    }

    # Cache single memory for 5 minutes
    await cache.set(cache_key, data, ttl=300)
    return data


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    user_id: str = Query("default"),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Memory).where(Memory.id == memory_id))
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    await session.delete(memory)

    # Invalidate caches
    await cache.delete(f"memories:single:{memory_id}")
    await cache.invalidate_memories(user_id)
    await cache.invalidate_dashboard(user_id)

    # Broadcast real-time update via WebSocket
    await manager.broadcast({
        "type": "stats_updated",
        "entity": "memory",
        "action": "deleted",
        "user_id": user_id,
    })

    return {"status": "deleted", "id": memory_id}


@router.post("/improve")
async def improve(
    user_id: str = Query("default"),
):
    result = await improve_memories(user_id=user_id)
    # Invalidate dashboard cache after improvement
    await cache.invalidate_dashboard(user_id)
    return result


@router.post("/forget")
async def forget(
    dataset: str = Query(...),
    user_id: str = Query("default"),
):
    result = await forget_dataset(dataset, user_id=user_id)
    # Invalidate all caches for this user after forget
    await cache.invalidate_dashboard(user_id)
    await cache.invalidate_memories(user_id)
    return result



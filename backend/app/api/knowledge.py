from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.cognee_client import get_knowledge_graph, search_graph, recall_memories, improve_memories, cognee_cognify, get_cognee_status
from app.models.memory import KnowledgeNode

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/graph")
async def knowledge_graph(
    user_id: str = Query("default"),
    session: AsyncSession = Depends(get_session),
):
    # Try Cognee first for the real knowledge graph
    cognee_graph = await get_knowledge_graph(user_id=user_id)

    if cognee_graph.get("nodes"):
        return cognee_graph

    # Fallback: Build graph from SQLAlchemy DB
    db_nodes = await session.execute(
        select(KnowledgeNode).where(KnowledgeNode.user_id == user_id)
    )
    db_nodes = db_nodes.scalars().all()

    # Also get memories for entity nodes
    from app.models.memory import Memory
    memories = await session.execute(
        select(Memory).where(Memory.user_id == user_id).order_by(Memory.created_at.desc()).limit(100)
    )
    memories = memories.scalars().all()

    nodes = []
    edges = []
    seen_ids = set()

    for node in db_nodes:
        if node.id not in seen_ids:
            seen_ids.add(node.id)
            nodes.append({
                "id": node.id,
                "label": node.label,
                "type": node.node_type,
                "importance": node.importance,
                "properties": node.properties,
            })

    for mem in memories:
        if mem.id not in seen_ids:
            seen_ids.add(mem.id)
            nodes.append({
                "id": mem.id,
                "label": mem.content[:50],
                "type": "memory",
                "importance": mem.importance_score,
                "content_type": mem.content_type,
                "created_at": str(mem.created_at),
            })

        entities = mem.entities or []
        for ent in entities:
            ent_id = f"entity_{ent}"
            if ent_id not in seen_ids:
                seen_ids.add(ent_id)
                nodes.append({
                    "id": ent_id,
                    "label": ent,
                    "type": "entity",
                    "importance": 0.5,
                })
            edges.append({
                "source": mem.id,
                "target": ent_id,
                "label": "contains",
            })

    return {"nodes": nodes, "edges": edges, "count": len(nodes)}


@router.get("/search")
async def search(
    query: str,
    user_id: str = Query("default"),
):
    results = await search_graph(query, user_id=user_id)
    return results


@router.get("/status")
async def knowledge_status(user_id: str = Query("default")):
    return await get_cognee_status()


@router.post("/cognify")
async def cognify(user_id: str = Query("default")):
    """Run Cognee cognify() to build/update the knowledge graph from stored memories."""
    result = await cognee_cognify(user_id=user_id)
    return result


@router.post("/improve")
async def improve_knowledge(user_id: str = Query("default")):
    """Run Cognee improve() to enrich, prune, and re-weight the knowledge graph."""
    result = await improve_memories(user_id=user_id)
    return result

from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.cognee_client import get_knowledge_graph, search_graph, recall_memories, improve_memories, cognee_cognify, get_cognee_status
from app.core.utils import extract_entities_from_text
from app.models.memory import KnowledgeNode

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/graph")
async def knowledge_graph(
    user_id: str = Query("default"),
    session: AsyncSession = Depends(get_session),
):
    cognee_graph = await get_knowledge_graph(user_id=user_id)

    if cognee_graph.get("nodes"):
        return cognee_graph

    from app.models.memory import Memory
    db_nodes = await session.execute(
        select(KnowledgeNode).where(KnowledgeNode.user_id == user_id)
    )
    db_nodes = db_nodes.scalars().all()

    memories = await session.execute(
        select(Memory).where(Memory.user_id == user_id).order_by(Memory.created_at.asc()).limit(100)
    )
    memories = memories.scalars().all()

    nodes = []
    edges = []
    seen_ids = set()
    entity_to_memories = defaultdict(list)
    memory_list = []

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
        mid = mem.id
        short_label = (mem.content[:60] + "...") if len(mem.content) > 60 else mem.content

        if mid not in seen_ids:
            seen_ids.add(mid)
            nodes.append({
                "id": mid,
                "label": short_label,
                "type": "memory",
                "importance": mem.importance_score,
                "content_type": mem.content_type,
                "created_at": str(mem.created_at),
            })

        memory_list.append(mem)
        extracted = mem.entities or extract_entities_from_text(mem.content)
        ent_ids = []

        for ent in extracted:
            ent_id = f"entity_{ent.lower().replace(' ', '_')}"
            ent_ids.append(ent_id)
            if ent_id not in seen_ids:
                seen_ids.add(ent_id)
                nodes.append({
                    "id": ent_id,
                    "label": ent,
                    "type": "entity",
                    "importance": 0.6,
                })
            edges.append({
                "source": mid,
                "target": ent_id,
                "label": "mentions",
            })
            entity_to_memories[ent_id].append(mid)

        if not extracted:
            edges.append({
                "source": mid,
                "target": f"user_{mem.user_id}",
                "label": "from",
            })

    # Connect entities that appear in the same memories
    for ent_id, mem_ids in entity_to_memories.items():
        for i in range(len(mem_ids) - 1):
            edges.append({
                "source": mem_ids[i],
                "target": mem_ids[i + 1],
                "label": "related",
            })

    # Connect consecutive Q&A pairs (user → assistant)
    for i in range(len(memory_list) - 1):
        if memory_list[i].content_type == "chat_message" and memory_list[i + 1].content_type == "chat_response":
            edges.append({
                "source": memory_list[i].id,
                "target": memory_list[i + 1].id,
                "label": "responds_to",
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

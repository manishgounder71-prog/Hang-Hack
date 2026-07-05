import re
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.cognee_client import get_knowledge_graph, search_graph, recall_memories, improve_memories, cognee_cognify, get_cognee_status
from app.models.memory import KnowledgeNode

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

TECH_KEYWORDS = {
    "python", "react", "typescript", "javascript", "docker", "fastapi", "postgresql",
    "sqlalchemy", "nextjs", "node", "api", "rest", "graphql", "redis", "aws", "git",
    "linux", "mongodb", "css", "html", "svelte", "vue", "angular", "tensorflow",
    "pytorch", "rag", "llm", "ai", "ml", "cognee", "genesis", "swiftcart", "helios",
    "solartracker", "kubernetes", "ci/cd", "oauth", "jwt", "websocket",
}


STOP_WORDS = {
    "i", "the", "this", "that", "what", "when", "where", "why", "how", "my",
    "me", "we", "it", "so", "to", "is", "in", "of", "for", "on", "a", "an",
    "be", "has", "have", "do", "does", "did", "will", "would", "can", "could",
    "should", "may", "might", "shall", "am", "are", "was", "were", "been",
    "being", "not", "no", "or", "and", "but", "if", "as", "at", "by", "from",
    "with", "about", "into", "through", "during", "before", "after", "above",
    "below", "let", "based", "however", "there", "their", "they", "them",
    "set", "get", "use", "using", "used", "make", "making", "made",
    "need", "needs", "needed", "like", "look", "looks", "looking",
}


def _extract_entities(text: str) -> list[str]:
    sentences = re.split(r"[.!?]+", text)
    result = set()

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        lower_sent = sent.lower()
        tech_in_sent = {w for w in re.findall(r"[a-zA-Z0-9+#/]+", lower_sent) if w in TECH_KEYWORDS}
        for t in tech_in_sent:
            idx = lower_sent.index(t)
            if idx == 0 or (idx > 0 and lower_sent[idx - 1] in (" ", "-", "/")):
                original = sent[idx:idx + len(t)]
                if t == "helios":
                    result.add("Project Helios")
                else:
                    result.add(original if original[0].isupper() else t.capitalize())

        multi_word = re.findall(r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)*", sent)
        for mw in multi_word:
            mw = mw.strip()
            if len(mw) <= 1:
                continue
            first_is_sentence_start = sent.startswith(mw)
            if first_is_sentence_start and mw.lower() not in TECH_KEYWORDS:
                if mw.split()[0].lower() in STOP_WORDS:
                    continue
                if len(mw.split()) == 1:
                    continue
            if mw.lower() not in STOP_WORDS:
                result.add(mw)

    return list(result)[:5]


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
        extracted = mem.entities or _extract_entities(mem.content)
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

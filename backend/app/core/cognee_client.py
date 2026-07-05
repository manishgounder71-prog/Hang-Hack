import asyncio
import logging
import os
from typing import Optional

# Enable mock embeddings globally to prevent Windows symlink and credential errors
os.environ["MOCK_EMBEDDING"] = "true"

from app.core.config import settings
from app.core.utils import extract_entities_from_text, infer_relationships

logger = logging.getLogger(__name__)

try:
    import cognee
    HAS_COGNEE = True
    # Force Cognee to use 'openai' LLM provider and default model internally to avoid conflicts with 'groq' in .env
    from cognee.infrastructure.llm import get_llm_config
    llm_config = get_llm_config()
    llm_config.llm_provider = "openai"
    llm_config.llm_model = "gpt-4o-mini"
except ImportError:
    HAS_COGNEE = False
    logger.warning("Cognee not installed - running in fallback mode")

COGNEE_DATASET = settings.COGNEE_DATASET


def _compute_cognee_enabled() -> bool:
    """Determine whether Cognee LLM features should be enabled based on current provider."""
    return True


def set_cognee_enabled(provider: str) -> None:
    """Update Cognee LLM provider at runtime when the LLM provider changes."""
    global COGNEE_ENABLED
    COGNEE_ENABLED = True
    if HAS_COGNEE:
        try:
            from cognee.infrastructure.llm import get_llm_config
            llm_config = get_llm_config()
            prov = provider.lower() if provider else "openai"
            
            if prov == "groq":
                llm_config.llm_provider = "openai"
                model_name = settings.LLM_MODEL or "llama-3.3-70b-versatile"
                if not model_name.startswith("openai/"):
                    llm_config.llm_model = f"openai/{model_name}"
                else:
                    llm_config.llm_model = model_name
                llm_config.llm_endpoint = "https://api.groq.com/openai/v1"
                if settings.LLM_API_KEY:
                    llm_config.llm_api_key = settings.LLM_API_KEY
                    cognee.config.openai_api_key = settings.LLM_API_KEY
            else:
                llm_config.llm_provider = prov
                if prov == "openai":
                    llm_config.llm_model = settings.LLM_MODEL or "gpt-4o-mini"
                    if settings.LLM_API_KEY:
                        cognee.config.openai_api_key = settings.LLM_API_KEY
                else:
                    llm_config.llm_model = settings.LLM_MODEL
                    if settings.LLM_API_KEY:
                        os.environ[f"{prov.upper()}_API_KEY"] = settings.LLM_API_KEY
            logger.info(f"Cognee LLM provider dynamically updated to: {prov} (internal: {llm_config.llm_provider}, model: {llm_config.llm_model})")
        except Exception as e:
            logger.error(f"Failed to dynamically configure Cognee LLM config: {e}")


# Always enable Cognee when present
COGNEE_ENABLED = True
COGNEE_FAILURES = 0
MAX_COGNEE_FAILURES = 3

def handle_cognee_failure(e: Exception):
    global COGNEE_FAILURES, COGNEE_ENABLED
    COGNEE_FAILURES += 1
    logger.warning(f"Cognee failure ({COGNEE_FAILURES}/{MAX_COGNEE_FAILURES}): {e}")
    if COGNEE_FAILURES >= MAX_COGNEE_FAILURES:
        logger.error("Circuit breaker triggered: Disabling Cognee memory system to avoid latency.")
        COGNEE_ENABLED = False

def record_cognee_success():
    global COGNEE_FAILURES
    COGNEE_FAILURES = 0



async def init_cognee():
    if not HAS_COGNEE:
        logger.info("Cognee unavailable - using fallback memory system")
        return {"status": "cognee_not_available", "mode": "fallback"}
    try:
        if settings.COGNEE_API_KEY:
            cognee.config.api_key = settings.COGNEE_API_KEY
        if settings.COGNEE_API_URL:
            cognee.config.api_url = settings.COGNEE_API_URL
        
        # Configure Cognee to use dynamic provider/model
        from cognee.infrastructure.llm import get_llm_config
        llm_config = get_llm_config()
        provider = settings.LLM_PROVIDER.lower() if settings.LLM_PROVIDER else "openai"
        
        if provider == "groq":
            llm_config.llm_provider = "openai"
            model_name = settings.LLM_MODEL or "llama-3.3-70b-versatile"
            if not model_name.startswith("openai/"):
                llm_config.llm_model = f"openai/{model_name}"
            else:
                llm_config.llm_model = model_name
            llm_config.llm_endpoint = "https://api.groq.com/openai/v1"
            if settings.LLM_API_KEY:
                llm_config.llm_api_key = settings.LLM_API_KEY
                cognee.config.openai_api_key = settings.LLM_API_KEY
        else:
            llm_config.llm_provider = provider
            llm_config.llm_model = settings.LLM_MODEL or "gpt-4o-mini"
            if settings.LLM_API_KEY:
                if provider == "openai":
                    cognee.config.openai_api_key = settings.LLM_API_KEY
                else:
                    os.environ[f"{provider.upper()}_API_KEY"] = settings.LLM_API_KEY
                    
        logger.info(f"Cognee configured successfully (provider={provider}, model={llm_config.llm_model}, endpoint={llm_config.llm_endpoint})")
        return {"status": "initialized"}
    except Exception as e:
        logger.error(f"Cognee config failed: {e}")
        return {"status": "init_failed", "error": str(e)}


def _dataset_name(user_id: str, dataset: Optional[str] = None) -> str:
    if dataset:
        return dataset
    return f"{COGNEE_DATASET}_{user_id}" if user_id else COGNEE_DATASET


async def remember_content(
    content: str,
    content_type: str = "text",
    user_id: str = "",
    metadata: dict = None,
    dataset: str = None,
    file_path: str = None,
):
    """Store content in Cognee with metadata. Supports text, files, and URLs."""
    global COGNEE_ENABLED
    ds = _dataset_name(user_id, dataset)

    if HAS_COGNEE and COGNEE_ENABLED:
        try:
            # Ingest raw data (supports text and file paths)
            await asyncio.wait_for(
                cognee.add(file_path if file_path else content, dataset_name=ds),
                timeout=3.0
            )
            # Build the knowledge graph structure
            await asyncio.wait_for(cognee.cognify(ds), timeout=4.0)
            return {"cognee_id": ds, "content": content[:200], "dataset": ds, "stored": True}
        except Exception as e:
            logger.error(f"Cognee remember/cognify failed: {e}")
            if "AuthenticationError" in str(e) or "API key" in str(e):
                logger.warning("Disabling Cognee due to authentication failure.")
                COGNEE_ENABLED = False

    return {"cognee_id": None, "content": content[:200], "dataset": ds, "stored": True, "mode": "fallback"}


async def recall_memories(
    query: str,
    user_id: str = "",
    limit: int = 10,
    dataset: str = None,
    filters: dict = None,
):
    """Query Cognee memory using semantic + graph traversal."""
    global COGNEE_ENABLED
    ds = _dataset_name(user_id, dataset)
    results = None

    if HAS_COGNEE and COGNEE_ENABLED:
        try:
            results = await asyncio.wait_for(
                cognee.search(query_text=query, datasets=[ds]),
                timeout=3.0
            )
            if results:
                serialized_results = []
                for r in results:
                    if hasattr(r, "model_dump"):
                        serialized_results.append(r.model_dump())
                    elif hasattr(r, "__dict__"):
                        serialized_results.append(r.__dict__)
                    else:
                        serialized_results.append(r)
                return serialized_results[:limit]
        except Exception as e:
            logger.error(f"Cognee search failed: {e}")
            if "AuthenticationError" in str(e) or "API key" in str(e):
                logger.warning("Disabling Cognee due to authentication failure.")
                COGNEE_ENABLED = False

    # Fallback to local SQL keyword search if Cognee search returns nothing or is disabled
    try:
        from app.core.database import async_session_factory
        from app.models.memory import Memory
        from sqlalchemy import select, or_
        
        async with async_session_factory() as session:
            stmt = select(Memory).where(Memory.user_id == user_id)
            
            # Extract keywords > 2 chars
            words = [w.strip(".,!?;:()\"'").lower() for w in query.split()]
            keywords = [w for w in words if len(w) > 2 and w not in ("what", "with", "this", "that", "your", "have", "here", "from", "past", "response")]
            
            if keywords:
                filters_list = [Memory.content.ilike(f"%{kw}%") for kw in keywords]
                stmt = stmt.where(or_(*filters_list))
                
            stmt = stmt.order_by(Memory.created_at.desc()).limit(limit)
            db_res = await session.execute(stmt)
            db_mems = db_res.scalars().all()
            
            fallback_results = [
                {
                    "id": m.id,
                    "content": m.content,
                    "content_type": m.content_type,
                    "importance_score": m.importance_score,
                    "created_at": str(m.created_at),
                    "source": "sql_fallback"
                }
                for m in db_mems
                if m.content != query # Skip the query itself
            ]
            return fallback_results
    except Exception as db_err:
        logger.error(f"SQL fallback search failed: {db_err}")

    return []


async def improve_memories(user_id: str = "", dataset: str = None):
    """Run Cognee memify to build and enrich the knowledge graph."""
    global COGNEE_ENABLED
    ds = _dataset_name(user_id, dataset)

    if HAS_COGNEE and COGNEE_ENABLED:
        try:
            result = await asyncio.wait_for(cognee.memify(dataset=ds), timeout=10.0)
            return {"status": "improved", "result": str(result)[:200]}
        except Exception as e:
            logger.error(f"Cognee memify failed: {e}")
            if "AuthenticationError" in str(e) or "API key" in str(e):
                logger.warning("Disabling Cognee due to authentication failure.")
                COGNEE_ENABLED = False
            return {"status": "failed", "error": str(e)}

    return {"status": "cognee_not_available", "mode": "fallback"}


async def memify_content(user_id: str = "", dataset: str = None):
    """Alias for improve - runs post-ingestion enrichment."""
    return await improve_memories(user_id, dataset)


async def forget_dataset(dataset_name: str, user_id: str = ""):
    """Surgically prune or delete a dataset from Cognee."""
    global COGNEE_ENABLED
    ds = _dataset_name(user_id, dataset_name)

    if HAS_COGNEE and COGNEE_ENABLED:
        try:
            await asyncio.wait_for(cognee.datasets.delete_dataset(ds), timeout=5.0)
            return {"status": "forgotten", "dataset": ds, "result": "deleted"}
        except Exception as e:
            logger.error(f"Cognee delete_dataset failed: {e}")
            if "AuthenticationError" in str(e) or "API key" in str(e):
                logger.warning("Disabling Cognee due to authentication failure.")
                COGNEE_ENABLED = False
            return {"status": "failed", "error": str(e)}

    return {"status": "cognee_not_available", "mode": "fallback"}


async def get_knowledge_graph(user_id: str = "", dataset: str = None, depth: int = 2):
    """Get the full knowledge graph from Cognee with nodes and edges.

    Queries Cognee's native graph engine database directly using get_graph_engine()
    to retrieve the nodes and edges, ensuring a true native knowledge graph.
    """
    global COGNEE_ENABLED
    ds = _dataset_name(user_id, dataset)

    if HAS_COGNEE and COGNEE_ENABLED:
        try:
            # Retrieve the native graph engine
            from cognee.infrastructure.databases.graph import get_graph_engine
            graph_engine = await get_graph_engine()
            
            # Fetch native graph data
            raw_nodes, raw_edges = await asyncio.wait_for(
                graph_engine.get_graph_data(),
                timeout=4.0
            )

            if raw_nodes:
                nodes: list[dict] = []
                edges: list[dict] = []
                seen_ids: set[str] = set()

                for node_id, props in raw_nodes:
                    if node_id not in seen_ids:
                        seen_ids.add(node_id)
                        label = props.get("name") or props.get("label") or node_id
                        node_type = props.get("type") or "concept"
                        importance = float(props.get("importance", 0.6))
                        
                        nodes.append({
                            "id": node_id,
                            "label": label,
                            "type": node_type.lower(),
                            "importance": importance,
                            "source": "cognee",
                        })

                for source_id, target_id, rel_name, props in raw_edges:
                    edges.append({
                        "source": source_id,
                        "target": target_id,
                        "label": rel_name or "connected_to",
                    })

                logger.info(f"Retrieved native Cognee knowledge graph: {len(nodes)} nodes, {len(edges)} edges")
                return {"nodes": nodes, "edges": edges, "count": len(nodes), "source": "cognee"}

            # Retrieve all memories from Cognee for this dataset (heuristic fallback)
            all_results = await asyncio.wait_for(
                cognee.search(query_text="", datasets=[ds]),
                timeout=3.0
            )

            if all_results and len(all_results) > 0:
                nodes: list[dict] = []
                edges: list[dict] = []
                seen_ids: set[str] = set()

                for result in all_results:
                    # Normalize the result to a dict
                    if hasattr(result, "model_dump"):
                        item = result.model_dump()
                    elif hasattr(result, "__dict__"):
                        item = result.__dict__
                    elif isinstance(result, dict):
                        item = result
                    else:
                        continue

                    mem_id = str(item.get("id", str(hash(str(item)))))
                    raw_content = item.get("content") or item.get("text") or ""
                    content = str(raw_content)[:100]
                    content_type = str(item.get("content_type", item.get("type", "memory")))

                    # Safely extract tags from metadata (which may be dict, list, or other)
                    metadata_raw = item.get("metadata", {})
                    if isinstance(metadata_raw, dict):
                        tags_raw = metadata_raw.get("tags", [])
                    else:
                        tags_raw = item.get("tags", [])
                    if isinstance(tags_raw, str):
                        tags_raw = [tags_raw]
                    if not isinstance(tags_raw, list):
                        tags_raw = []

                    # Extract entities from content (capitalized words)
                    entities = extract_entities_from_text(content)

                    # Add any tags as entities too
                    for tag in tags_raw:
                        tag_str = str(tag).strip()
                        if tag_str and len(tag_str) > 1:
                            entities.add(tag_str.capitalize())

                    # Ensure at least one entity connection for isolated nodes
                    if not entities and len(content) > 0:
                        first_word = content.split()[0].strip(".,!?;:'\"")
                        if first_word and len(first_word) > 1:
                            entities.add(first_word.capitalize())

                    # Add memory node
                    if mem_id not in seen_ids:
                        seen_ids.add(mem_id)
                        nodes.append({
                            "id": mem_id,
                            "label": content[:50] + ("..." if len(content) > 50 else ""),
                            "type": content_type,
                            "importance": min(1.0, max(0.1, len(content) / 200)),
                            "source": "cognee",
                        })

                    # Add entity nodes and edges
                    for entity in sorted(entities):
                        ent_id = f"entity:{entity.lower().replace(' ', '_')}"
                        if ent_id not in seen_ids:
                            seen_ids.add(ent_id)
                            nodes.append({
                                "id": ent_id,
                                "label": entity,
                                "type": "entity",
                                "importance": 0.6,
                                "source": "cognee",
                            })
                        edges.append({
                            "source": mem_id,
                            "target": ent_id,
                            "label": "contains",
                        })

                # Infer cross-entity relationships (entities that co-occur in memories)
                if len(nodes) > 1:
                    inferred = infer_relationships(nodes, edges)
                    edges.extend(inferred)

                if nodes:
                    logger.info(f"Built Cognee knowledge graph: {len(nodes)} nodes, {len(edges)} edges")
                    return {"nodes": nodes, "edges": edges, "count": len(nodes), "source": "cognee"}

        except (AttributeError, TypeError, KeyError) as e:
            # Cognee search API may return results in unexpected formats
            logger.info(f"Cognee graph extraction format issue ({e}) — falling back to SQLAlchemy")
        except Exception as e:
            logger.error(f"Cognee knowledge graph extraction failed: {e}")
            if "AuthenticationError" in str(e) or "API key" in str(e):
                logger.warning("Disabling Cognee due to authentication failure.")
                COGNEE_ENABLED = False

    return {"nodes": [], "edges": [], "source": "fallback", "count": 0}


async def search_graph(query: str, user_id: str = "", dataset: str = None):
    """Search across the knowledge graph with semantic + graph traversal."""
    global COGNEE_ENABLED
    ds = _dataset_name(user_id, dataset)

    if HAS_COGNEE and COGNEE_ENABLED:
        try:
            result = await asyncio.wait_for(
                cognee.search(query_text=query, datasets=[ds]),
                timeout=3.0
            )
            serialized = []
            if result:
                for r in result:
                    if hasattr(r, "model_dump"):
                        serialized.append(r.model_dump())
                    elif hasattr(r, "__dict__"):
                        serialized.append(r.__dict__)
                    else:
                        serialized.append(r)
            return {"results": serialized, "source": "cognee"}
        except Exception as e:
            logger.error(f"Cognee search failed: {e}")
            if "AuthenticationError" in str(e) or "API key" in str(e):
                logger.warning("Disabling Cognee due to authentication failure.")
                COGNEE_ENABLED = False

    return {"results": [], "source": "fallback"}


async def get_cognee_status():
    """Check Cognee health and configuration."""
    if not HAS_COGNEE:
        return {"available": False, "mode": "fallback"}
    try:
        return {"available": True, "mode": "live", "dataset": COGNEE_DATASET}
    except Exception as e:
        return {"available": False, "mode": "error", "error": str(e)}


async def cognee_cognify(user_id: str = "", dataset: str = None):
    """Run Cognee cognify() to build the knowledge graph from stored memories."""
    return await get_knowledge_graph(user_id=user_id, dataset=dataset)


async def get_memory_stats(user_id: str = ""):
    """Get memory statistics from Cognee for the dashboard."""
    global COGNEE_ENABLED
    if HAS_COGNEE and COGNEE_ENABLED:
        try:
            all_memories = await asyncio.wait_for(
                cognee.search(query_text="", datasets=[_dataset_name(user_id)]),
                timeout=1.5
            )
            record_cognee_success()
            memory_count = len(all_memories) if all_memories else 0
            recent = []
            if all_memories:
                for m in all_memories[:5]:
                    if hasattr(m, "model_dump"):
                        recent.append(m.model_dump())
                    elif hasattr(m, "__dict__"):
                        recent.append(m.__dict__)
                    else:
                        recent.append(m)
            return {
                "memory_count": memory_count,
                "knowledge_nodes": 0,
                "relationships": 0,
                "recent_memories": recent,
            }
        except Exception as e:
            handle_cognee_failure(e)
    return {"memory_count": 0, "knowledge_nodes": 0, "relationships": 0, "recent_memories": []}

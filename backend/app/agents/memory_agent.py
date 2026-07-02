"""Memory Agent — Cognee lifecycle management with caching and enrichment."""
import time
import json
from typing import Any

from app.core.utils import extract_entities_from_text


class MemoryAgent:
    """Manages the full Cognee memory lifecycle with intelligent caching,
    deduplication, importance scoring, and entity extraction."""

    def __init__(self):
        self.name = "Memory Agent"
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_ttl = 30  # seconds
        self._process_count = 0
        self._total_processed = 0

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def process(self, event: dict) -> dict:
        self._process_count += 1
        action = event.get("action", "store")

        # Route to handler
        handlers = {
            "store": self._store_memory,
            "batch_store": self._batch_store,
            "recall": self._recall_memory,
            "search": self._recall_memory,
            "improve": self._improve_memories,
            "forget": self._forget_dataset,
            "stats": self._get_stats,
            "deduplicate": self._deduplicate,
            "enrich": self._enrich_memory,
        }
        handler = handlers.get(action)
        if handler is None:
            return {"agent": self.name, "status": "unknown_action", "action": action}

        try:
            result = await handler(event)
            self._total_processed += 1
            return {"agent": self.name, "action": action, "status": "ok", **result}
        except Exception as e:
            return {
                "agent": self.name, "action": action, "status": "error",
                "error": str(e),
            }

    # ── Cache helpers ────────────────────────────────────────────────────

    def _cache_get(self, key: str) -> Any | None:
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                return val
            del self._cache[key]
        return None

    def _cache_set(self, key: str, val: Any) -> None:
        self._cache[key] = (time.time(), val)

    def _cache_invalidate(self, prefix: str = "") -> None:
        if not prefix:
            self._cache.clear()
        else:
            self._cache = {k: v for k, v in self._cache.items() if not k.startswith(prefix)}

    # ── Handlers ─────────────────────────────────────────────────────────

    async def _store_memory(self, event: dict) -> dict:
        from app.core.cognee_client import remember_content

        content = event.get("content", "")
        content_type = event.get("content_type", "text")
        user_id = event.get("user_id", "")
        metadata = event.get("metadata") or {}
        tags = event.get("tags", [])

        # Deduplication via content hash
        content_hash = hash(content)
        cache_key = f"stored:{content_hash}"
        cached = self._cache_get(cache_key)
        if cached:
            return {"status": "duplicate", "existing": cached, "source": "cache"}

        # Compute importance score
        importance = self._compute_importance(content, content_type, metadata)

        result = await remember_content(
            content=content,
            content_type=content_type,
            user_id=user_id,
            metadata={**metadata, "importance": importance, "tags": tags},
        )

        self._cache_set(cache_key, result)
        self._cache_invalidate("recall:")  # Invalidate recall cache
        return {
            "status": "stored",
            "result": result,
            "importance": importance,
            "content_preview": content[:120],
        }

    async def _batch_store(self, event: dict) -> dict:
        """Store multiple memories in batch with deduplication."""
        items = event.get("items", [])
        results = []
        for item in items:
            try:
                r = await self._store_memory({
                    **event,
                    "content": item.get("content", ""),
                    "content_type": item.get("content_type", "text"),
                    "metadata": item.get("metadata"),
                    "tags": item.get("tags", []),
                })
                results.append(r)
            except Exception as e:
                results.append({"status": "error", "error": str(e)})
        stored = sum(1 for r in results if r.get("status") == "stored")
        return {"stored": stored, "total": len(items), "results": results}

    async def _recall_memory(self, event: dict) -> dict:
        from app.core.cognee_client import recall_memories

        query = event.get("query", "")
        user_id = event.get("user_id", "")
        limit = event.get("limit", 10)
        threshold = event.get("threshold", 0.0)

        cache_key = f"recall:{user_id}:{query}:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return {"results": cached, "count": len(cached), "source": "cache"}

        results = await recall_memories(query=query, user_id=user_id, limit=limit)

        # Score filter
        if threshold > 0 and results:
            results = [r for r in results if r.get("score", 1) >= threshold]

        self._cache_set(cache_key, results)
        return {"results": results, "count": len(results), "source": "cognee"}

    async def _improve_memories(self, event: dict) -> dict:
        from app.core.cognee_client import improve_memories

        user_id = event.get("user_id", "")
        result = await improve_memories(user_id=user_id)

        self._cache_invalidate()
        return {"result": result, "message": "Memory enrichment complete"}

    async def _forget_dataset(self, event: dict) -> dict:
        from app.core.cognee_client import forget_dataset

        dataset = event.get("dataset", "")
        user_id = event.get("user_id", "")
        result = await forget_dataset(dataset, user_id=user_id)

        self._cache_invalidate()
        return {"result": result, "dataset": dataset}

    async def _deduplicate(self, event: dict) -> dict:
        """Find and merge duplicate memories."""
        from app.core.cognee_client import recall_memories
        user_id = event.get("user_id", "")
        memories = await recall_memories(query="", user_id=user_id, limit=500)
        seen = {}
        duplicates = []
        for mem in memories:
            preview = mem.get("content", "")[:80]
            if preview in seen:
                duplicates.append({"original": seen[preview], "duplicate": mem})
            else:
                seen[preview] = mem
        return {"duplicates_found": len(duplicates), "duplicates": duplicates[:20]}

    async def _enrich_memory(self, event: dict) -> dict:
        """Enrich a memory with extracted entities and metadata."""
        content = event.get("content", "")
        entities = self._extract_entities(content)
        importance = self._compute_importance(content, "text", {})
        return {
            "entities": entities,
            "importance": importance,
            "word_count": len(content.split()),
            "char_count": len(content),
        }

    async def _get_stats(self, event: dict) -> dict:
        return {
            "process_count": self._process_count,
            "total_processed": self._total_processed,
            "cache_size": len(self._cache),
        }

    # ── Intelligence ─────────────────────────────────────────────────────

    def _compute_importance(self, content: str, content_type: str, metadata: dict) -> float:
        """Score content importance from 0.0 to 1.0 based on multiple signals."""
        score = 0.5  # baseline

        # Length signal — longer = more important
        word_count = len(content.split())
        if word_count > 200:
            score += 0.2
        elif word_count > 50:
            score += 0.1

        # Content type signal
        type_boosts = {
            "file": 0.15, "code": 0.1, "project": 0.2,
            "achievement": 0.25, "milestone": 0.3, "reflection": 0.1,
        }
        score += type_boosts.get(content_type, 0)

        # Keyword signal
        important_keywords = ["project", "built", "created", "learned", "won",
                              "launched", "published", "awarded", "patented"]
        if any(kw in content.lower() for kw in important_keywords):
            score += 0.1

        # Explicit score from metadata
        explicit = metadata.get("importance_score")
        if explicit:
            score = (score + float(explicit)) / 2

        return min(1.0, max(0.0, score))

    def _extract_entities(self, content: str) -> list[str]:
        """Simple entity extraction using capitalization patterns."""
        return list(extract_entities_from_text(content))

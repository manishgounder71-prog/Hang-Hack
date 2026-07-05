"""Knowledge Graph Agent — Graph construction, traversal, and inference."""
import time
from typing import Any

from app.core.utils import extract_entities_from_text, infer_relationships


class KnowledgeGraphAgent:
    """Builds and queries a knowledge graph from stored memories with
    relationship inference, path finding, subgraph extraction, and
    intelligent caching."""

    def __init__(self):
        self.name = "Knowledge Graph Agent"
        self._graph_cache: dict[str, Any] = {}
        self._cache_ttl = 60

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def process(self, event: dict) -> dict:
        action = event.get("action", "build_graph")

        handlers = {
            "build_graph": self._build_graph,
            "query_graph": self._query,
            "search": self._search,
            "path": self._find_path,
            "subgraph": self._extract_subgraph,
            "infer": self._infer_relationships,
            "stats": self._get_stats,
            "status": self._get_status,
        }
        handler = handlers.get(action)
        if handler is None:
            return {"agent": self.name, "status": "unknown_action", "action": action}

        try:
            result = await handler(event)
            return {"agent": self.name, "action": action, "status": "ok", **result}
        except Exception as e:
            return {"agent": self.name, "action": action, "status": "error", "error": str(e)}

    # ── Handlers ─────────────────────────────────────────────────────────

    async def _build_graph(self, event: dict) -> dict:
        """Build a knowledge graph from memories with entity extraction."""
        from app.core.cognee_client import get_knowledge_graph

        memories = event.get("memories", [])
        user_id = event.get("user_id", "")

        nodes: list[dict] = []
        edges: list[dict] = []
        seen_entities: set[str] = set()

        for mem in memories:
            mem_id = mem.get("id", "")
            entities = mem.get("entities", extract_entities_from_text(mem.get("content", "")))
            tags = mem.get("tags", [])

            # Add memory node
            nodes.append({
                "id": mem_id,
                "label": (mem.get("content", "")[:40] + "...") if len(mem.get("content", "")) > 40 else mem.get("content", ""),
                "type": "memory",
                "importance": mem.get("importance_score", 0.5),
                "content_type": mem.get("content_type", "text"),
                "created_at": str(mem.get("created_at", "")),
            })

            # Add entity nodes and edges
            all_tags = list(set(entities + tags))

            # Try Cognee knowledge graph if available
            try:
                cognee_result = await get_knowledge_graph(user_id=user_id)
                if cognee_result.get("nodes"):
                    return {"nodes": cognee_result["nodes"], "edges": cognee_result.get("edges", []),
                            "count": len(cognee_result["nodes"]), "source": "cognee"}
            except Exception:
                pass  # Fall back to local construction

            for entity in all_tags:
                entity_id = f"entity:{entity.lower().replace(' ', '_')}"
                if entity_id not in seen_entities:
                    nodes.append({
                        "id": entity_id,
                        "label": entity,
                        "type": "entity",
                        "importance": 0.6,
                    })
                    seen_entities.add(entity_id)
                edges.append({
                    "source": mem_id,
                    "target": entity_id,
                    "label": "mentions",
                })

        # Infer cross-entity relationships
        inferred = self._infer_cross_relationships(nodes, edges)
        edges.extend(inferred)

        graph = {"nodes": nodes, "edges": edges, "count": len(nodes)}
        self._graph_cache[f"graph:{user_id}"] = (time.time(), graph)
        return {**graph, "source": "local"}

    async def _query(self, event: dict) -> dict:
        """Query the knowledge graph with graph traversal."""
        query = event.get("query", "")
        user_id = event.get("user_id", "")

        from app.core.cognee_client import recall_memories
        results = await recall_memories(query=query, user_id=user_id, limit=20)

        return {
            "query": query,
            "results": results,
            "count": len(results),
        }

    async def _search(self, event: dict) -> dict:
        """Full-text and semantic search across the graph."""
        from app.core.cognee_client import recall_memories

        query = event.get("query", "")
        user_id = event.get("user_id", "")

        cache_key = f"search:{user_id}:{query}"
        cached = self._graph_cache.get(cache_key)
        if cached and time.time() - cached[0] < self._cache_ttl:
            return {"results": cached[1], "source": "cache", "query": query}

        results = await recall_memories(query=query, user_id=user_id, limit=20)
        self._graph_cache[cache_key] = (time.time(), results)
        return {"results": results, "count": len(results), "source": "cognee", "query": query}

    async def _find_path(self, event: dict) -> dict:
        """Find shortest path between two nodes in the graph."""
        source = event.get("source", "")
        target = event.get("target", "")

        # Check cache for current graph
        graph = None
        for key, (ts, val) in list(self._graph_cache.items()):
            if key.startswith("graph:") and time.time() - ts < self._cache_ttl:
                graph = val
                break

        if not graph:
            return {"path": [], "message": "No graph available. Build a graph first."}

        # BFS path finding
        nodes = {n["id"]: n for n in graph.get("nodes", [])}
        edges = graph.get("edges", [])
        adj: dict[str, list[str]] = {}

        for e in edges:
            adj.setdefault(e["source"], []).append(e["target"])
            adj.setdefault(e["target"], []).append(e["source"])

        path = self._bfs(source, target, adj)
        path_nodes = [nodes.get(nid, {"id": nid, "label": nid, "type": "unknown"}) for nid in path] if path else []

        return {
            "path": path,
            "path_nodes": path_nodes,
            "length": len(path) - 1 if path else -1,
            "found": bool(path),
        }

    async def _extract_subgraph(self, event: dict) -> dict:
        """Extract a subgraph around a specific node."""
        center = event.get("node_id", "")
        depth = event.get("depth", 2)

        graph = None
        for key, (ts, val) in list(self._graph_cache.items()):
            if key.startswith("graph:") and time.time() - ts < self._cache_ttl:
                graph = val
                break

        if not graph:
            return {"subgraph": None, "message": "No graph available"}

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        adj: dict[str, list[str]] = {}
        for e in edges:
            adj.setdefault(e["source"], []).append(e["target"])
            adj.setdefault(e["target"], []).append(e["source"])

        # BFS to depth
        visited: set[str] = {center}
        queue: list[tuple[str, int]] = [(center, 0)]
        while queue:
            node, d = queue.pop(0)
            if d >= depth:
                continue
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, d + 1))

        sub_nodes = [n for n in nodes if n["id"] in visited]
        sub_edges = [e for e in edges if e["source"] in visited and e["target"] in visited]
        return {"subgraph": {"nodes": sub_nodes, "edges": sub_edges}, "count": len(sub_nodes)}

    async def _infer_relationships(self, event: dict) -> dict:
        """Infer new relationships between nodes based on co-occurrence."""
        graph = None
        for key, (ts, val) in list(self._graph_cache.items()):
            if key.startswith("graph:") and time.time() - ts < self._cache_ttl:
                graph = val
                break

        if not graph:
            return {"inferred": [], "message": "No graph available"}

        inferred = self._infer_cross_relationships(graph.get("nodes", []), graph.get("edges", []))
        return {"inferred": inferred, "count": len(inferred)}

    async def _get_stats(self, event: dict) -> dict:
        return {"cache_size": len(self._graph_cache)}

    async def _get_status(self, event: dict) -> dict:
        from app.core.cognee_client import get_memory_stats
        try:
            stats = await get_memory_stats(event.get("user_id", ""))
            return {"cognee_connected": True, "stats": stats}
        except Exception:
            return {"cognee_connected": False, "message": "Cognee unavailable"}

    # ── Intelligence ─────────────────────────────────────────────────────

    def _infer_cross_relationships(self, nodes: list[dict], edges: list[dict]) -> list[dict]:
        """Infer relationships based on shared connections."""
        return infer_relationships(nodes, edges)

    def _bfs(self, start: str, target: str, adj: dict[str, list[str]]) -> list[str]:
        """Breadth-first search to find shortest path."""
        if start not in adj or target not in adj:
            return []
        visited: set[str] = {start}
        queue: list[tuple[str, list[str]]] = [(start, [start])]
        while queue:
            node, path = queue.pop(0)
            if node == target:
                return path
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return []

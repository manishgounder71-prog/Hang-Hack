"""
Shared utility functions for Genesis AI.

Consolidates entity extraction and relationship inference logic that was
previously duplicated across cognee_client.py, memory_agent.py, and
knowledge_agent.py.
"""


def extract_entities_from_text(text: str) -> set[str]:
    """Extract likely entity names from text based on capitalization patterns.

    Finds capitalized words that aren't common stop words or all-caps noise.
    Returns a deduplicated set of entity names.
    """
    words = text.split()
    entities: set[str] = set()
    skip_words = {
        "the", "this", "that", "what", "when", "where", "which", "with", "from",
        "into", "over", "upon", "they", "them", "their", "have", "been", "were",
        "been", "more", "some", "there", "here", "also", "very", "just", "like",
        "about", "would", "could", "should", "because", "after", "before", "then",
        "than", "such", "each", "both", "most", "your", "will", "make", "made",
        "said", "used", "using", "based", "built", "added", "created",
    }
    for w in words:
        clean = w.strip(".,!?;:'\"()[]{}")
        if (clean and clean[0].isupper() and len(clean) > 2
                and clean.lower() not in skip_words
                and not clean.isupper()  # Skip ALL CAPS (often noise)
                and not clean.isdigit()):
            entities.add(clean)
    return entities


def infer_relationships(nodes: list[dict], edges: list[dict]) -> list[dict]:
    """Infer relationships between entity nodes that share common connections.

    Two nodes are "related" if they share at least 2 common neighbors.
    Only adds edges between nodes not already directly connected.
    """
    inferred = []
    # Build adjacency map
    adj: dict[str, set[str]] = {}
    for e in edges:
        adj.setdefault(e["source"], set()).add(e["target"])
        adj.setdefault(e["target"], set()).add(e["source"])

    node_ids = list(adj.keys())
    for i in range(len(node_ids)):
        for j in range(i + 1, len(node_ids)):
            shared = adj[node_ids[i]] & adj[node_ids[j]]
            if len(shared) >= 2:
                if node_ids[j] not in adj.get(node_ids[i], set()):
                    inferred.append({
                        "source": node_ids[i],
                        "target": node_ids[j],
                        "label": f"related ({len(shared)} shared)",
                    })
    return inferred

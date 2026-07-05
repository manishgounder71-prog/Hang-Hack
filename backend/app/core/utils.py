import re


def extract_entities_from_text(text: str) -> set:
    words = re.findall(r'\b[A-Z][a-z]+\b', text)
    return set(words)


def infer_relationships(nodes: list[dict], edges: list[dict]) -> list[dict]:
    inferred = []
    entity_nodes = [n for n in nodes if n.get("type") == "entity"]
    for i, e1 in enumerate(entity_nodes):
        for e2 in entity_nodes[i + 1:]:
            e1_connections = {e["source"] for e in edges if e["target"] == e1["id"]}
            e2_connections = {e["source"] for e in edges if e["target"] == e2["id"]}
            shared = e1_connections & e2_connections
            if shared:
                inferred.append({
                    "source": e1["id"],
                    "target": e2["id"],
                    "label": "co_occurs_with",
                })
    return inferred

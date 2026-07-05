import re

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


def extract_entities_from_text(text: str, max_entities: int = 5) -> list[str]:
    if not text:
        return []
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
                    result.add(original if original and original[0].isupper() else t.capitalize())

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

    return list(result)[:max_entities]


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

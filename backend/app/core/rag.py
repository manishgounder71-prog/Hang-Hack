import json
import math
import logging
from collections import Counter
from datetime import datetime

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "because", "but", "and", "or", "if", "while", "that", "this", "these",
    "those", "it", "its", "you", "your", "i", "me", "my", "we", "our",
    "he", "him", "his", "she", "her", "they", "them", "their", "what",
    "which", "who", "whom", "about", "up", "down", "also", "well", "any",
    "hi", "hello", "hey", "thanks", "thank", "yes", "no", "ok", "okay",
    "please", "sure", "right", "got", "get", "let", "like", "want", "know",
    "think", "say", "see", "come", "go", "make", "take", "give", "use",
    "find", "tell", "ask", "try", "leave", "call", "help", "need", "feel",
}

NGRAM_MIN = 2
NGRAM_MAX = 3
VECTOR_DIM = 1024


def _hash_feature(text: str, dim: int = VECTOR_DIM) -> int:
    return abs(hash(text)) % dim


def _text_to_vector(text: str) -> list[float]:
    cleaned = text.lower()
    for ch in '.,!?;:"\'()[]{}-_=+<>/\\@#$%^&*~`|':
        cleaned = cleaned.replace(ch, " ")
    words = [w for w in cleaned.split() if w not in STOPWORDS and len(w) > 1]

    features: list[str] = []
    for w in words:
        for n in range(NGRAM_MIN, NGRAM_MAX + 1):
            for i in range(len(w) - n + 1):
                features.append(w[i:i+n])

    if not features:
        return [0.0] * VECTOR_DIM

    counts = Counter(features)
    max_count = max(counts.values()) if counts else 1

    vec = [0.0] * dim
    for feat, count in counts.items():
        idx = _hash_feature(feat, dim)
        tf = 0.5 + 0.5 * (count / max_count)
        vec[idx] += tf

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(av * bv for av, bv in zip(a, b))


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS rag_vectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    content_type TEXT DEFAULT 'chat_message',
    session_id TEXT DEFAULT '',
    vector TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""
CREATE_INDEX_SQL = "CREATE INDEX IF NOT EXISTS idx_rag_user ON rag_vectors(user_id)"


class RagStore:
    def __init__(self):
        self._table_checked = False

    async def _ensure_table(self, session: AsyncSession):
        if self._table_checked:
            return
        try:
            await session.execute(sa_text(CREATE_TABLE_SQL))
            await session.execute(sa_text(CREATE_INDEX_SQL))
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.warning(f"RAG table creation error: {e}")
        self._table_checked = True

    async def store(self, content: str, user_id: str = "default",
                    content_type: str = "chat_message", session_id: str = "",
                    session: AsyncSession = None):
        await self._ensure_table(session)
        vec = json.dumps(_text_to_vector(content))
        try:
            await session.execute(
                sa_text("""INSERT INTO rag_vectors (user_id, content, content_type, session_id, vector)
                           VALUES (:uid, :content, :ctype, :sid, :vec)"""),
                {"uid": user_id, "content": content, "ctype": content_type,
                 "sid": session_id, "vec": vec},
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"RAG store error: {e}")

    async def query(self, query_text: str, user_id: str = "default",
                    limit: int = 3, min_similarity: float = 0.15,
                    session: AsyncSession = None) -> list[dict]:
        await self._ensure_table(session)
        query_vec = _text_to_vector(query_text)

        try:
            result = await session.execute(
                sa_text("""SELECT id, user_id, content, content_type, session_id, vector, created_at
                           FROM rag_vectors
                           WHERE user_id = :uid AND content_type = 'chat_message' AND vector IS NOT NULL
                           ORDER BY created_at DESC LIMIT 100"""),
                {"uid": user_id},
            )
            rows = result.fetchall()
        except Exception as e:
            logger.error(f"RAG query error: {e}")
            return []

        candidates = []
        for row in rows:
            try:
                vec = json.loads(row.vector)
            except (json.JSONDecodeError, TypeError, AttributeError):
                continue
            if not isinstance(vec, list) or len(vec) != VECTOR_DIM:
                continue
            sim = cosine_similarity(query_vec, vec)
            candidates.append((sim, row))

        candidates.sort(key=lambda x: -x[0])

        results = []
        seen = set()
        for sim, row in candidates:
            if len(results) >= limit:
                break
            if sim < min_similarity:
                continue
            content = str(row.content)[:300]
            if content in seen:
                continue
            seen.add(content)
            results.append({
                "id": row.id,
                "content": content,
                "content_type": str(row.content_type or "chat_message"),
                "session_id": str(row.session_id or ""),
                "similarity": round(sim, 3),
                "created_at": str(row.created_at) if row.created_at else "",
            })

        return results


rag_store = RagStore()

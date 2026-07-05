import json
import asyncio
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.cognee_client import remember_content
from app.core.rag import rag_store
from app.core.llm import llm
from app.models.memory import Memory, Reflection
from app.services.reflection_service import ReflectionService

logger = logging.getLogger(__name__)


def _limit_content(content: str, max_chars: int = 10000) -> str:
    return content[:max_chars] if len(content) > max_chars else content


def _build_system_prompt() -> str:
    return """You are Genesis AI, a helpful AI assistant. Answer naturally and concisely.
Use the conversation history and any provided context to answer. Never mention memory, recall, or past conversations explicitly."""


def _build_context(history: str, rag_results: list) -> str:
    context_lines = ""
    if rag_results:
        context_lines = "\nRelevant past context:\n" + "\n".join(
            f"- {r['content'][:200]}" for r in rag_results
        )
    return f"""Conversation history:
{history}{context_lines}

Respond naturally."""


class GenesisEngine:
    async def _store_and_prepare(
        self, message: str, user_id: str, session: AsyncSession
    ) -> tuple[str, list]:
        await remember_content(
            content=message, content_type="chat_message", user_id=user_id,
            metadata={"direction": "user"},
        )
        db_memory = Memory(
            user_id=user_id, content=message, content_type="chat_message",
            metadata={"direction": "user"},
        )
        session.add(db_memory)
        await session.flush()

        await rag_store.store(message, user_id=user_id, session=session)

        history_stmt = (
            select(Memory)
            .where(Memory.user_id == user_id, Memory.id != db_memory.id)
            .order_by(Memory.created_at.desc())
            .limit(8)
        )
        history_result = await session.execute(history_stmt)
        history_mems = list(reversed(history_result.scalars().all()))
        history_formatted = "\n".join([
            f"{'User' if m.content_type == 'chat_message' else 'Assistant'}: {m.content}"
            for m in history_mems
        ])

        rag_results = await rag_store.query(
            message, user_id=user_id, limit=3, session=session
        )

        return history_formatted, rag_results

    async def _store_response(
        self, content: str, user_id: str, streamed: bool = False
    ) -> None:
        await remember_content(
            content=content, content_type="chat_response",
            user_id=user_id, metadata={"direction": "assistant", "streamed": streamed},
        )

    async def _generate_reflection(
        self, message: str, user_id: str, session: AsyncSession
    ) -> None:
        try:
            svc = ReflectionService()
            result = await svc.generate_reflection(
                trigger_event="chat_response",
                context={"what_worked": message, "what_failed": ""},
            )
            db_reflection = Reflection(
                user_id=user_id,
                trigger_event="chat_response",
                what_worked=result.get("what_worked", ""),
                what_failed=result.get("what_failed", ""),
                improvements=result.get("improvements", ""),
                patterns=result.get("patterns", ""),
                influence_score=result.get("influence_score", 0.5),
            )
            session.add(db_reflection)
        except Exception as e:
            logger.warning(f"Reflection generation failed (non-critical): {e}")

    async def process_message(self, message: str, user_id: str, session: AsyncSession) -> dict:
        message = _limit_content(message)
        history_formatted, rag_results = await self._store_and_prepare(message, user_id, session)
        response = await self._generate_response(message, history_formatted, rag_results)

        response_text = response.get("response", "")
        db_memory = Memory(
            user_id=user_id, content=response_text,
            content_type="chat_response", metadata={"direction": "assistant"},
        )
        session.add(db_memory)
        await self._store_response(response_text, user_id)
        await self._generate_reflection(message, user_id, session)

        return response

    async def stream_chat(self, message: str, user_id: str, session: AsyncSession) -> AsyncGenerator[str, None]:
        message = _limit_content(message)
        history_formatted, rag_results = await self._store_and_prepare(message, user_id, session)

        system = _build_system_prompt()
        context = _build_context(history_formatted, rag_results)
        user_prompt = f"User: {message}\n\n{context}"

        full_response = ""
        try:
            async for chunk in llm.chat_stream(system, user_prompt):
                full_response += chunk
                yield f"data: {json.dumps({'token': chunk, 'done': False})}\n\n"
        except AttributeError:
            content = await llm.chat(system, user_prompt)
            for word in content.split(" "):
                full_response += word + " "
                yield f"data: {json.dumps({'token': word + ' ', 'done': False})}\n\n"
                await asyncio.sleep(0.02)
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            fallback = f"Here's my response: {message[:200]}"
            for word in fallback.split(" "):
                full_response += word + " "
                yield f"data: {json.dumps({'token': word + ' ', 'done': False})}\n\n"
                await asyncio.sleep(0.02)

        db_memory = Memory(
            user_id=user_id, content=full_response,
            content_type="chat_response", metadata={"direction": "assistant", "streamed": True},
        )
        session.add(db_memory)
        await self._store_response(full_response, user_id, streamed=True)
        await self._generate_reflection(message, user_id, session)

        yield f"data: {json.dumps({'done': True})}\n\n"

    async def _generate_response(self, message: str, history: str,
                                  rag_results: list) -> dict:
        system = _build_system_prompt()
        context = _build_context(history, rag_results)
        user_prompt = f"User: {message}\n\n{context}"

        try:
            content = await llm.chat(system, user_prompt)
        except Exception as e:
            logger.error(f"LLM chat failed: {e}", exc_info=True)
            content = f"Here's my response to: {message}"

        return {
            "response": content,
            "memories_used": [str(r["id"]) for r in rag_results],
            "memories_count": len(rag_results),
            "reasoning_path": [],
        }

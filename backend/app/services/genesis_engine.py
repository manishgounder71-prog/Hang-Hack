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


class GenesisEngine:
    async def process_message(self, message: str, user_id: str, session: AsyncSession) -> dict:
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

        response = await self._generate_response(
            message, history_formatted, rag_results
        )

        await remember_content(
            content=response.get("response", ""), content_type="chat_response",
            user_id=user_id, metadata={"direction": "assistant"},
        )
        response_memory = Memory(
            user_id=user_id, content=response.get("response", ""),
            content_type="chat_response", metadata={"direction": "assistant"},
        )
        session.add(response_memory)

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
        except Exception:
            pass

        return response

    async def stream_chat(self, message: str, user_id: str, session: AsyncSession) -> AsyncGenerator[str, None]:
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

        system = """You are Genesis AI, a helpful AI assistant. Answer naturally and concisely.
Use the conversation history and any provided context to answer. Never mention memory, recall, or past conversations explicitly."""

        context_lines = ""
        if rag_results:
            context_lines = "\nRelevant past context:\n" + "\n".join(
                f"- {r['content'][:200]}" for r in rag_results
            )

        user = f"""User: {message}

Conversation history:
{history_formatted}{context_lines}

Respond naturally."""

        full_response = ""
        try:
            async for chunk in llm.chat_stream(system, user):
                full_response += chunk
                yield f"data: {json.dumps({'token': chunk, 'done': False})}\n\n"
        except AttributeError:
            content = await llm.chat(system, user)
            for word in content.split(" "):
                full_response += word + " "
                yield f"data: {json.dumps({'token': word + ' ', 'done': False})}\n\n"
                await asyncio.sleep(0.02)
        except Exception as e:
            logger.error(f"Stream error: {e}")
            fallback = f"Here's my response: {message[:200]}"
            for word in fallback.split(" "):
                full_response += word + " "
                yield f"data: {json.dumps({'token': word + ' ', 'done': False})}\n\n"
                await asyncio.sleep(0.02)

        await remember_content(
            content=full_response, content_type="chat_response", user_id=user_id,
            metadata={"direction": "assistant", "streamed": True},
        )
        response_memory = Memory(
            user_id=user_id, content=full_response, content_type="chat_response",
            metadata={"direction": "assistant", "streamed": True},
        )
        session.add(response_memory)

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
        except Exception:
            pass

        yield f"data: {json.dumps({'done': True})}\n\n"

    async def _generate_response(self, message: str, history: str,
                                  rag_results: list) -> dict:
        system = """You are Genesis AI, a helpful AI assistant. Answer naturally and concisely.
Use the conversation history and any provided context to answer. Never mention memory, recall, or past conversations explicitly."""

        context_lines = ""
        if rag_results:
            context_lines = "\nRelevant past context:\n" + "\n".join(
                f"- {r['content'][:200]}" for r in rag_results
            )

        user = f"""User: {message}

Conversation history:
{history}{context_lines}

Respond naturally."""

        try:
            content = await llm.chat(system, user)
        except Exception as e:
            logger.error(f"LLM chat failed: {e}", exc_info=True)
            content = f"Here's my response to: {message}"

        return {
            "response": content,
            "memories_used": [str(r["id"]) for r in rag_results],
            "memories_count": len(rag_results),
            "reasoning_path": [],
        }

import json
import asyncio
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.cognee_client import recall_memories, remember_content
from app.core.llm import llm
from app.models.memory import Memory

logger = logging.getLogger(__name__)


class GenesisEngine:
    async def process_message(self, message: str, user_id: str, session: AsyncSession) -> dict:
        relevant_memories = await recall_memories(message, user_id=user_id, limit=10)

        await remember_content(
            content=message, content_type="chat_message", user_id=user_id,
            metadata={"direction": "user"},
        )
        db_memory = Memory(
            user_id=user_id, content=message, content_type="chat_message",
            metadata={"direction": "user"},
        )
        session.add(db_memory)

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

        response = await self._generate_response(message, relevant_memories[:5], history_formatted, user_id)

        await remember_content(
            content=response.get("response", ""), content_type="chat_response", user_id=user_id,
            metadata={"direction": "assistant"},
        )
        response_memory = Memory(
            user_id=user_id, content=response.get("response", ""), content_type="chat_response",
            metadata={"direction": "assistant"},
        )
        session.add(response_memory)

        return response

    async def stream_chat(self, message: str, user_id: str, session: AsyncSession) -> AsyncGenerator[str, None]:
        relevant_memories = await recall_memories(message, user_id=user_id, limit=5)

        await remember_content(
            content=message, content_type="chat_message", user_id=user_id,
            metadata={"direction": "user"},
        )
        db_memory = Memory(
            user_id=user_id, content=message, content_type="chat_message",
            metadata={"direction": "user"},
        )
        session.add(db_memory)

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

        system = """You are Genesis AI, a helpful AI assistant with persistent memory. Help the user with their questions.
If you have genuinely relevant memories from past conversations, use them to provide better answers.
Otherwise just answer normally without mentioning memory."""

        memories_json = json.dumps([{k: str(v) for k, v in m.items() if isinstance(v, (str, int, float, bool))} for m in relevant_memories], default=str)[:2000]
        user = f"""User: {message}

Recent conversation:
{history_formatted}

Past memories: {memories_json}

Respond helpfully. Only mention past memories if they are directly relevant."""

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

        yield f"data: {json.dumps({'done': True})}\n\n"

    async def _generate_response(self, message: str, memories: list, history: str, user_id: str) -> dict:
        system = """You are Genesis AI, a helpful AI assistant with persistent memory. Help the user with their questions.
Answer concisely. Only reference past memories if they are genuinely relevant to the current question."""

        memories_json = json.dumps(memories, default=str)[:2000]

        user = f"""User: {message}

Recent conversation:
{history}

Past memories: {memories_json}

Respond helpfully."""

        try:
            content = await llm.chat(system, user)
        except Exception as e:
            logger.error(f"LLM chat failed: {e}", exc_info=True)
            content = f"Here's my response to: {message}"

        return {
            "response": content,
            "memories_used": [],
            "memories_count": len(memories),
            "reasoning_path": [],
        }

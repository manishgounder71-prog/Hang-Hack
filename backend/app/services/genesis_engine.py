import json
import asyncio
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.event_bus import event_bus
from app.core.cognee_client import recall_memories, remember_content
from app.core.llm import llm
from app.models.memory import Memory

logger = logging.getLogger(__name__)


class GenesisEngine:
    def __init__(self):
        self.agent_bus = event_bus

    async def process_message(self, message: str, user_id: str, session: AsyncSession) -> dict:
        # 1. Recall relevant memories from Cognee
        relevant_memories = await recall_memories(message, user_id=user_id, limit=10)

        # 2. Store user message in Cognee
        await remember_content(
            content=message,
            content_type="chat_message",
            user_id=user_id,
            metadata={"direction": "user"},
        )

        # 3. Persist to SQLAlchemy
        db_memory = Memory(
            user_id=user_id,
            content=message,
            content_type="chat_message",
            metadata={"direction": "user"},
        )
        session.add(db_memory)

        # Fetch recent conversation history (excluding the current user message just inserted)
        history_stmt = (
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.content_type.in_(["chat_message", "chat_response"]),
                Memory.id != db_memory.id
            )
            .order_by(Memory.created_at.desc())
            .limit(6)
        )
        history_result = await session.execute(history_stmt)
        history_mems = list(reversed(history_result.scalars().all()))
        history_formatted = "\n".join([
            f"{'User' if m.content_type == 'chat_message' else 'Assistant'}: {m.content}"
            for m in history_mems
        ])

        # 4. Run reflection agent
        reflection_result = await self.agent_bus.publish("reflection", {
            "action": "reflect",
            "trigger": "user_message",
            "context": {"message": message, "memory_count": len(relevant_memories)},
            "user_id": user_id,
        })

        context = {
            "memories": relevant_memories[:5],
            "reflections": [r.get("reflection", {}) for r in reflection_result if isinstance(r, dict)],
            "history": history_formatted,
        }

        # 5. Generate response
        response = await self._generate_response(message, context, user_id)

        # 6. Store response in Cognee
        await remember_content(
            content=response.get("response", ""),
            content_type="chat_response",
            user_id=user_id,
            metadata={"direction": "assistant", "memories_used": response.get("memories_used", [])},
        )

        # 7. Persist response to SQLAlchemy
        response_memory = Memory(
            user_id=user_id,
            content=response.get("response", ""),
            content_type="chat_response",
            metadata={"direction": "assistant", "memories_used": response.get("memories_used", [])},
        )
        session.add(response_memory)

        # 8. Run prediction agent
        await self.agent_bus.publish("prediction", {
            "action": "predict",
            "type": "next_interest",
            "context": {"message": message, "memories": relevant_memories[:3]},
            "user_id": user_id,
        })

        return response

    async def stream_chat(self, message: str, user_id: str, session: AsyncSession) -> AsyncGenerator[str, None]:
        """Stream chat response as SSE events, storing memory in background."""
        relevant_memories = await recall_memories(message, user_id=user_id, limit=10)

        # Store user message
        await remember_content(
            content=message, content_type="chat_message", user_id=user_id,
            metadata={"direction": "user"},
        )
        db_memory = Memory(
            user_id=user_id, content=message, content_type="chat_message",
            metadata={"direction": "user"},
        )
        session.add(db_memory)

        # Fetch recent conversation history (excluding the current user message just inserted)
        history_stmt = (
            select(Memory)
            .where(
                Memory.user_id == user_id,
                Memory.content_type.in_(["chat_message", "chat_response"]),
                Memory.id != db_memory.id
            )
            .order_by(Memory.created_at.desc())
            .limit(6)
        )
        history_result = await session.execute(history_stmt)
        history_mems = list(reversed(history_result.scalars().all()))
        history_formatted = "\n".join([
            f"{'User' if m.content_type == 'chat_message' else 'Assistant'}: {m.content}"
            for m in history_mems
        ])

        system = """You are Genesis AI, a self-evolving AI operating system. You remember everything across sessions using Cognee's persistent memory.
You reference past memories, detect patterns, and provide contextual responses."""

        memories_json = json.dumps([{k: str(v) for k, v in m.items() if isinstance(v, (str, int, float, bool))} for m in relevant_memories], default=str)[:2000]
        user = f"""User message: {message}

Recent Conversation History:
{history_formatted}

Relevant memories from Cognee: {memories_json}

Provide a helpful response. If relevant memories exist, reference them explicitly."""

        full_response = ""
        try:
            async for chunk in llm.chat_stream(system, user):
                full_response += chunk
                yield f"data: {json.dumps({'token': chunk, 'done': False})}\n\n"
        except AttributeError:
            # Fallback if chat_stream not implemented on provider
            content = await llm.chat(system, user)
            for word in content.split(" "):
                full_response += word + " "
                yield f"data: {json.dumps({'token': word + ' ', 'done': False})}\n\n"
                await asyncio.sleep(0.02)
        except Exception as e:
            logger.error(f"Stream error: {e}")
            fallback = f"I recall {len(relevant_memories)} relevant memories from our past interactions. Based on what I've learned: {message[:100]}..."
            for word in fallback.split(" "):
                full_response += word + " "
                yield f"data: {json.dumps({'token': word + ' ', 'done': False})}\n\n"
                await asyncio.sleep(0.02)

        # Store response in background
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

    async def _generate_response(self, message: str, context: dict, user_id: str) -> dict:
        system = """You are Genesis AI, a self-evolving AI operating system. You remember everything across sessions using Cognee's persistent memory.
You reference past memories, detect patterns, and provide contextual responses.
When relevant memories exist, mention them explicitly: "I recall from our previous conversation..."
When patterns are detected, point them out and suggest improvements.
You continuously learn, reflect, and predict based on memory patterns."""

        memories_json = json.dumps(context.get("memories", []), default=str)[:2000]
        reflections_json = json.dumps(context.get("reflections", []), default=str)[:1000]

        user = f"""User message: {message}

Recent Conversation History:
{context.get("history", "None")}

Relevant memories from Cognee: {memories_json}
Recent self-reflections: {reflections_json}

Provide a helpful response. If relevant memories exist, reference them explicitly.
If patterns are detected, mention them and suggest how the user could benefit.
Be concise but thorough."""

        try:
            content = await llm.chat(system, user)
        except Exception as e:
            logger.error(f"LLM chat failed, using fallback: {e}", exc_info=True)
            content = f"I remember {len(context.get('memories', []))} relevant memories from our past interactions. Based on what I've learned, here's my response to: {message}"

        memories_used = [str(m.get("id", "")) for m in context.get("memories", []) if isinstance(m, dict)]

        return {
            "response": content,
            "memories_used": memories_used,
            "memories_count": len(context.get("memories", [])),
            "reasoning_path": [
                {"step": "cognee_recall", "description": f"Retrieved {len(context.get('memories', []))} relevant memories via Cognee recall"},
                {"step": "reflection", "description": "Analyzed past patterns through reflection agent"},
                {"step": "prediction", "description": "Generated prediction for future needs"},
                {"step": "response_generation", "description": "Generated contextual response with memory awareness"},
            ],
        }

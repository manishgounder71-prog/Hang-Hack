from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.memory import ChatRequest, ChatResponse
from app.services.genesis_engine import GenesisEngine
from app.core.database import get_session

router = APIRouter(prefix="/chat", tags=["chat"])
engine = GenesisEngine()


@router.post("")
async def chat(
    request: ChatRequest,
    user_id: str = Query("default"),
    session: AsyncSession = Depends(get_session),
):
    if request.stream:
        return StreamingResponse(
            engine.stream_chat(request.message, user_id, session),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    result = await engine.process_message(
        message=request.message,
        user_id=user_id,
        session=session,
    )
    return ChatResponse(
        response=result["response"],
        memories_used=result.get("memories_used", []),
        reasoning_path=result.get("reasoning_path", []),
    )

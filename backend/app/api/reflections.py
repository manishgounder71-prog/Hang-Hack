from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.memory import ReflectionCreate, ReflectionResponse
from app.services.reflection_service import ReflectionService
from app.core.database import get_session
from app.core.cognee_client import remember_content, recall_memories
from app.models.memory import Reflection

router = APIRouter(prefix="/reflections", tags=["reflections"])
service = ReflectionService()


@router.post("", response_model=dict, status_code=201)
async def create_reflection(
    reflection: ReflectionCreate,
    user_id: str = Query("default"),
    session: AsyncSession = Depends(get_session),
):
    # Generate reflection via AI
    result = await service.generate_reflection(
        trigger_event=reflection.trigger_event,
        context={
            "what_worked": reflection.what_worked,
            "what_failed": reflection.what_failed,
        },
    )

    # Persist to SQLAlchemy
    db_reflection = Reflection(
        user_id=user_id,
        trigger_event=reflection.trigger_event,
        what_worked=result.get("what_worked", ""),
        what_failed=result.get("what_failed", ""),
        improvements=result.get("improvements", ""),
        patterns=result.get("patterns", ""),
        influence_score=result.get("influence_score", 0.5),
    )
    session.add(db_reflection)

    # Persist to Cognee
    await remember_content(
        content=str(result),
        content_type="reflection",
        user_id=user_id,
        metadata={"trigger_event": reflection.trigger_event},
    )

    return {
        "reflection": result,
        "id": db_reflection.id,
    }


@router.get("", response_model=list[ReflectionResponse])
async def list_reflections(
    user_id: str = Query("default"),
    limit: int = Query(20),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Reflection)
        .where(Reflection.user_id == user_id)
        .order_by(Reflection.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{reflection_id}", response_model=ReflectionResponse)
async def get_reflection(
    reflection_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Reflection).where(Reflection.id == reflection_id))
    ref = result.scalar_one_or_none()
    if not ref:
        raise HTTPException(status_code=404, detail="Reflection not found")
    return ref


@router.delete("/{reflection_id}")
async def delete_reflection(
    reflection_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Reflection).where(Reflection.id == reflection_id))
    ref = result.scalar_one_or_none()
    if not ref:
        raise HTTPException(status_code=404, detail="Reflection not found")

    await session.delete(ref)
    return {"status": "deleted", "id": reflection_id}


@router.get("/stats/summary")
async def reflection_stats(
    user_id: str = Query("default"),
    session: AsyncSession = Depends(get_session),
):
    count_result = await session.execute(
        select(func.count(Reflection.id)).where(Reflection.user_id == user_id)
    )
    total = count_result.scalar() or 0

    avg_influence = await session.execute(
        select(func.avg(Reflection.influence_score)).where(Reflection.user_id == user_id)
    )
    avg_influence = float(avg_influence.scalar() or 0)

    return {
        "total": total,
        "avg_influence_score": round(avg_influence, 2),
    }

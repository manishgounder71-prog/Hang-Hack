"""Demo endpoint — seeds the database with impressive demo data for judge walkthrough."""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.seed_demo import seed_demo_data
from app.models.memory import Memory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/seed")
async def seed_demo(session: AsyncSession = Depends(get_session)):
    result = await seed_demo_data(session)
    return result


@router.get("/status")
async def demo_status(session: AsyncSession = Depends(get_session)):
    from sqlalchemy import select, func
    count = await session.execute(select(func.count(Memory.id)).where(Memory.user_id == "demo"))
    count = count.scalar()
    return {"seeded": count > 0, "memory_count": count}

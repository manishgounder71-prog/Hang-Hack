from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.memory import SkillCreate, SkillResponse
from app.services.skill_service import SkillService
from app.core.database import get_session
from app.core.cognee_client import recall_memories, remember_content
from app.models.memory import Skill

router = APIRouter(prefix="/skills", tags=["skills"])
service = SkillService()


@router.post("/detect")
async def detect_skills(
    user_id: str = Query("default"),
    session: AsyncSession = Depends(get_session),
):
    memories = await recall_memories("", user_id=user_id, limit=50)
    skill = await service.detect_skill_pattern(memories)

    if skill:
        # Persist detected skill to SQLAlchemy
        db_skill = Skill(
            user_id=user_id,
            name=skill.get("name", "Detected Skill"),
            description=skill.get("description", ""),
            steps=skill.get("steps", []),
            confidence_score=skill.get("confidence", 0.5),
            category=skill.get("category", "general"),
        )
        session.add(db_skill)

        # Also store in Cognee
        await remember_content(
            content=str(skill),
            content_type="skill",
            user_id=user_id,
            metadata={"skill_name": skill.get("name")},
        )

    return {"skill_detected": skill is not None, "skill": skill}


@router.get("", response_model=list[SkillResponse])
async def list_skills(
    user_id: str = Query("default"),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Skill).where(Skill.user_id == user_id).order_by(Skill.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    update: SkillCreate,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    skill.name = update.name
    skill.description = update.description
    skill.steps = update.steps
    skill.use_count = (skill.use_count or 0) + 1
    return skill


@router.delete("/{skill_id}")
async def delete_skill(
    skill_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    await session.delete(skill)
    return {"status": "deleted", "id": skill_id}


@router.get("/stats/summary")
async def skill_stats(
    user_id: str = Query("default"),
    session: AsyncSession = Depends(get_session),
):
    count_result = await session.execute(
        select(func.count(Skill.id)).where(Skill.user_id == user_id)
    )
    total = count_result.scalar() or 0

    avg_conf = await session.execute(
        select(func.avg(Skill.confidence_score)).where(Skill.user_id == user_id)
    )
    avg_confidence = float(avg_conf.scalar() or 0)

    total_uses = await session.execute(
        select(func.sum(Skill.use_count)).where(Skill.user_id == user_id)
    )
    total_uses = int(total_uses.scalar() or 0)

    return {
        "total": total,
        "avg_confidence": round(avg_confidence, 2),
        "total_uses": total_uses,
    }

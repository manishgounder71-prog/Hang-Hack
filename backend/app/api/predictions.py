from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.prediction_service import PredictionService
from app.core.database import get_session
from app.core.cognee_client import recall_memories, remember_content
from app.models.memory import Prediction

router = APIRouter(prefix="/predictions", tags=["predictions"])
service = PredictionService()


@router.post("", status_code=201)
async def create_prediction(
    prediction_type: str = Query("general"),
    user_id: str = Query("default"),
    session: AsyncSession = Depends(get_session),
):
    memories = await recall_memories("", user_id=user_id, limit=20)

    result = await service.generate_prediction(
        prediction_type=prediction_type,
        context={"memories": memories},
    )

    # Persist to SQLAlchemy
    db_prediction = Prediction(
        user_id=user_id,
        prediction_type=prediction_type,
        content=result.get("content", ""),
        confidence=result.get("confidence", 0.5),
        reasoning=result.get("reasoning", ""),
        influencing_memories=result.get("influencing_memories", []),
    )
    session.add(db_prediction)

    # Persist to Cognee
    await remember_content(
        content=str(result),
        content_type="prediction",
        user_id=user_id,
        metadata={"prediction_type": prediction_type},
    )

    return {
        "prediction": result,
        "id": db_prediction.id,
    }


@router.get("")
async def list_predictions(
    user_id: str = Query("default"),
    limit: int = Query(20),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Prediction)
        .where(Prediction.user_id == user_id)
        .order_by(Prediction.created_at.desc())
        .limit(limit)
    )
    predictions = result.scalars().all()

    return {
        "predictions": [
            {
                "id": p.id,
                "prediction_type": p.prediction_type,
                "content": p.content,
                "confidence": p.confidence,
                "reasoning": p.reasoning,
                "influencing_memories": p.influencing_memories,
                "is_fulfilled": p.is_fulfilled,
                "created_at": str(p.created_at),
            }
            for p in predictions
        ],
        "count": len(predictions),
    }


@router.get("/{prediction_id}")
async def get_prediction(
    prediction_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Prediction).where(Prediction.id == prediction_id))
    pred = result.scalar_one_or_none()
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")

    return {
        "id": pred.id,
        "prediction_type": pred.prediction_type,
        "content": pred.content,
        "confidence": pred.confidence,
        "reasoning": pred.reasoning,
        "influencing_memories": pred.influencing_memories,
        "is_fulfilled": pred.is_fulfilled,
        "created_at": str(pred.created_at),
    }


@router.post("/{prediction_id}/fulfill")
async def fulfill_prediction(
    prediction_id: str,
    fulfilled: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Prediction).where(Prediction.id == prediction_id))
    pred = result.scalar_one_or_none()
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")

    pred.is_fulfilled = 1 if fulfilled else 0
    return {"status": "updated", "id": prediction_id, "fulfilled": fulfilled}


@router.delete("/{prediction_id}")
async def delete_prediction(
    prediction_id: str,
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Prediction).where(Prediction.id == prediction_id))
    pred = result.scalar_one_or_none()
    if not pred:
        raise HTTPException(status_code=404, detail="Prediction not found")

    await session.delete(pred)
    return {"status": "deleted", "id": prediction_id}


@router.get("/stats/summary")
async def prediction_stats(
    user_id: str = Query("default"),
    session: AsyncSession = Depends(get_session),
):
    count_result = await session.execute(
        select(func.count(Prediction.id)).where(Prediction.user_id == user_id)
    )
    total = count_result.scalar() or 0

    avg_conf = await session.execute(
        select(func.avg(Prediction.confidence)).where(Prediction.user_id == user_id)
    )
    avg_confidence = float(avg_conf.scalar() or 0)

    fulfilled_result = await session.execute(
        select(func.count(Prediction.id))
        .where(Prediction.user_id == user_id, Prediction.is_fulfilled == 1)
    )
    fulfilled = fulfilled_result.scalar() or 0

    return {
        "total": total,
        "avg_confidence": round(avg_confidence, 2),
        "fulfilled": fulfilled,
        "accuracy_rate": round(fulfilled / total, 2) if total > 0 else 0,
    }

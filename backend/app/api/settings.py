from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.llm import llm
from app.core.cognee_client import set_cognee_enabled
from app.models.memory import UserSettings
from app.schemas.memory import SettingsSchema

router = APIRouter(prefix="/settings", tags=["settings"])


def _serialize(settings: UserSettings) -> dict:
    """Serialize ORM model using Pydantic schema, stripping API keys entirely."""
    data = SettingsSchema.model_validate(settings).model_dump()
    data.pop("llm_api_key", None)
    data.pop("cognee_api_key", None)
    return data


@router.get("", response_model=SettingsSchema)
async def get_settings(
    user_id: str = "default",
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        return SettingsSchema()

    return _serialize(settings)


@router.put("", response_model=SettingsSchema)
async def update_settings(
    payload: SettingsSchema,
    user_id: str = "default",
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = UserSettings(user_id=user_id)
        session.add(settings)

    # Map schema fields -> ORM columns (bool -> int conversion)
    settings.memory_aware_responses = int(payload.memory_aware_responses)
    settings.auto_reflect_after_chat = int(payload.auto_reflect_after_chat)
    settings.predict_next_topics = int(payload.predict_next_topics)
    settings.skill_auto_detection = int(payload.skill_auto_detection)
    settings.response_style = payload.response_style
    settings.memory_recall_count = payload.memory_recall_count
    settings.anonymous_usage_data = int(payload.anonymous_usage_data)
    settings.encrypt_memories = int(payload.encrypt_memories)
    settings.session_timeout = payload.session_timeout
    settings.weekly_summary = int(payload.weekly_summary)
    settings.skill_detected_notify = int(payload.skill_detected_notify)
    settings.prediction_alerts = int(payload.prediction_alerts)
    settings.system_updates = int(payload.system_updates)
    settings.llm_provider = payload.llm_provider
    settings.llm_model = payload.llm_model

    # Only update API keys if they contain new (non-masked) values
    # Masked keys (e.g. "sk-****...ab12") are sent back from the frontend
    # and should not overwrite the stored full key
    if payload.llm_api_key:
        settings.llm_api_key = payload.llm_api_key
    if payload.cognee_api_key:
        settings.cognee_api_key = payload.cognee_api_key

    # Sync the global LLM singleton with updated settings
    llm.provider = payload.llm_provider
    llm.model = payload.llm_model
    if payload.llm_api_key:
        llm.api_key = payload.llm_api_key

    # Update Cognee enable/disable based on the new provider
    set_cognee_enabled(payload.llm_provider)
    settings.enable_websocket = int(payload.enable_websocket)
    settings.streaming_responses = int(payload.streaming_responses)
    settings.connection_mode = payload.connection_mode
    settings.username = payload.username
    settings.email = payload.email
    settings.storage_capacity_pct = payload.storage_capacity_pct

    await session.flush()
    return _serialize(settings)


@router.post("/reset", response_model=SettingsSchema)
async def reset_settings(
    user_id: str = "default",
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()

    if settings:
        await session.delete(settings)

    return SettingsSchema()

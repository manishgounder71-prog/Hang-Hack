from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any, List
from datetime import datetime


class MemoryCreate(BaseModel):
    content: str
    content_type: str = "text"
    tags: List[str] = []
    importance_score: float = 0.5


class MemoryResponse(BaseModel):
    id: str
    content: str
    content_type: str
    importance_score: float
    emotional_weight: float
    tags: List[str]
    entities: List[str]
    cognee_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillCreate(BaseModel):
    name: str
    description: str = ""
    steps: list = []


class SkillResponse(BaseModel):
    id: str
    name: str
    description: str
    steps: list
    confidence_score: float
    use_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReflectionCreate(BaseModel):
    trigger_event: str
    what_worked: str = ""
    what_failed: str = ""
    improvements: str = ""
    patterns: str = ""


class ReflectionResponse(BaseModel):
    id: str
    trigger_event: str
    what_worked: str
    what_failed: str
    improvements: str
    patterns: str
    influence_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PredictionResponse(BaseModel):
    id: str
    prediction_type: str
    content: str
    confidence: float
    reasoning: str
    influencing_memories: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    message: str
    stream: bool = False

    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("message cannot be empty")
        return v


class ChatResponse(BaseModel):
    response: str
    memories_used: List[str] = []
    skills_used: List[str] = []
    reflections_used: List[str] = []
    reasoning_path: List[dict] = []


class UploadResponse(BaseModel):
    filename: str
    content_type: str
    memories_created: int
    status: str


class SettingsSchema(BaseModel):
    # AI Behavior
    memory_aware_responses: bool = True
    auto_reflect_after_chat: bool = True
    predict_next_topics: bool = True
    skill_auto_detection: bool = False
    response_style: str = "balanced"
    memory_recall_count: int = 10

    # Privacy & Security
    anonymous_usage_data: bool = False
    encrypt_memories: bool = True
    session_timeout: str = "24 hours"

    # Notifications
    weekly_summary: bool = True
    skill_detected_notify: bool = True
    prediction_alerts: bool = False
    system_updates: bool = True

    # API Config
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_api_key: str = ""
    cognee_api_key: str = ""

    # WebSocket & Streaming
    enable_websocket: bool = True
    streaming_responses: bool = True
    connection_mode: str = "auto"

    # Profile
    username: str = ""
    email: str = ""

    # Storage
    storage_capacity_pct: int = 34

    model_config = ConfigDict(from_attributes=True)

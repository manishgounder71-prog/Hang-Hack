from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    preferences = Column(JSON, default=dict)
    digital_twin = Column(JSON, default=dict)

    memories = relationship("Memory", back_populates="user", lazy="selectin")
    skills = relationship("Skill", back_populates="user", lazy="selectin")
    reflections = relationship("Reflection", back_populates="user", lazy="selectin")
    predictions = relationship("Prediction", back_populates="user", lazy="selectin")


class Memory(Base):
    __tablename__ = "memories"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    content_type = Column(String, default="text")
    importance_score = Column(Float, default=0.5)
    emotional_weight = Column(Float, default=0.0)
    tags = Column(JSON, default=list)
    entities = Column(JSON, default=list)
    relationships = Column(JSON, default=list)
    embedding = Column(JSON, default=list)
    cognee_id = Column(String, nullable=True)
    meta_data = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="memories")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    steps = Column(JSON, default=list)
    templates = Column(JSON, default=list)
    best_practices = Column(JSON, default=list)
    code_snippets = Column(JSON, default=list)
    mistakes = Column(JSON, default=list)
    learning_history = Column(JSON, default=list)
    confidence_score = Column(Float, default=0.0)
    use_count = Column(Integer, default=0)
    category = Column(String, default="general")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="skills")


class Reflection(Base):
    __tablename__ = "reflections"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    trigger_event = Column(String, nullable=False)
    what_worked = Column(Text, default="")
    what_failed = Column(Text, default="")
    improvements = Column(Text, default="")
    patterns = Column(Text, default="")
    influence_score = Column(Float, default=0.5)
    meta_data = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="reflections")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    prediction_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    reasoning = Column(Text, default="")
    influencing_memories = Column(JSON, default=list)
    is_fulfilled = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="predictions")


class KnowledgeNode(Base):
    __tablename__ = "knowledge_nodes"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    label = Column(String, nullable=False)
    node_type = Column(String, default="concept")
    properties = Column(JSON, default=dict)
    importance = Column(Float, default=0.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="knowledge_nodes")


User.knowledge_nodes = relationship("KnowledgeNode", back_populates="user", lazy="selectin")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    # AI Behavior
    memory_aware_responses = Column(Integer, default=1)
    auto_reflect_after_chat = Column(Integer, default=1)
    predict_next_topics = Column(Integer, default=1)
    skill_auto_detection = Column(Integer, default=0)
    response_style = Column(String, default="balanced")
    memory_recall_count = Column(Integer, default=10)

    # Privacy & Security
    anonymous_usage_data = Column(Integer, default=0)
    encrypt_memories = Column(Integer, default=1)
    session_timeout = Column(String, default="24 hours")

    # Notifications
    weekly_summary = Column(Integer, default=1)
    skill_detected_notify = Column(Integer, default=1)
    prediction_alerts = Column(Integer, default=0)
    system_updates = Column(Integer, default=1)

    # API Config
    llm_provider = Column(String, default="openai")
    llm_model = Column(String, default="gpt-4o-mini")
    llm_api_key = Column(String, default="")
    cognee_api_key = Column(String, default="")

    # WebSocket & Streaming
    enable_websocket = Column(Integer, default=1)
    streaming_responses = Column(Integer, default=1)
    connection_mode = Column(String, default="auto")

    # Profile
    username = Column(String, default="")
    email = Column(String, default="")

    # Storage
    storage_capacity_pct = Column(Integer, default=34)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")

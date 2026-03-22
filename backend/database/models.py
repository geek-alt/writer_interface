import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from backend.database.connection import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    fandom = Column(String, nullable=False)
    config_json = Column(Text, nullable=False)
    world_json = Column(Text)
    outline_json = Column(Text)
    status = Column(String, default="active")
    current_chapter = Column(Integer, default=0)
    total_chapters = Column(Integer)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    def __repr__(self):
        return f"<Project id={self.id!r} name={self.name!r} status={self.status!r}>"


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (
        UniqueConstraint("project_id", "chapter_number", name="uq_chapter"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False, default="")
    summary = Column(Text)
    word_count = Column(Integer, default=0)
    status = Column(String, default="pending_review")
    quality_score = Column(Integer, default=0)
    consistency_issues = Column(Text)
    generation_params = Column(Text)
    character_updates_json = Column(Text)
    world_updates_json = Column(Text)
    mc_progression_json = Column(Text)
    generation_time_seconds = Column(Float)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    def __repr__(self):
        return (
            f"<Chapter #{self.chapter_number} project={self.project_id!r} "
            f"status={self.status!r}>"
        )


class CharacterState(Base):
    __tablename__ = "character_states"
    __table_args__ = (
        UniqueConstraint("project_id", "chapter_number", "character_name", name="uq_char_state"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    character_name = Column(String, nullable=False)
    character_type = Column(String, default="canon")
    relationship_to_mc = Column(Float, default=0.0)
    romance_progress = Column(Float, default=0.0)
    romance_eligible = Column(Boolean, default=False)
    current_status = Column(String)
    location = Column(String)
    abilities_json = Column(Text)
    active_effects_json = Column(Text)
    internal_state = Column(Text)
    notes = Column(Text)

    def __repr__(self):
        return (
            f"<CharacterState {self.character_name!r} ch={self.chapter_number} "
            f"rel={self.relationship_to_mc}>"
        )


class GenerationQueue(Base):
    __tablename__ = "generation_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    status = Column(String, default="queued")
    priority = Column(Integer, default=5)
    attempts = Column(Integer, default=0)
    feedback = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, default=_now)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    def __repr__(self):
        return (
            f"<Queue ch={self.chapter_number} status={self.status!r} "
            f"attempts={self.attempts}>"
        )


class WorldEvent(Base):
    __tablename__ = "world_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer)
    event_name = Column(String, nullable=False)
    event_type = Column(String)
    description = Column(Text)
    characters_involved_json = Column(Text)
    consequences_json = Column(Text)
    prevented = Column(Boolean, default=False)

    def __repr__(self):
        return (
            f"<WorldEvent {self.event_name!r} ch={self.chapter_number} "
            f"prevented={self.prevented}>"
        )


class MCProgression(Base):
    __tablename__ = "mc_progression"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    iq_moment = Column(Boolean, default=False)
    eq_moment = Column(Boolean, default=False)
    abilities_learned_json = Column(Text)
    abilities_mastered_json = Column(Text)
    relationships_changed_json = Column(Text)
    key_decisions_json = Column(Text)
    power_level_estimate = Column(Integer, default=50)

    def __repr__(self):
        return f"<MCProgression ch={self.chapter_number} iq={self.iq_moment} eq={self.eq_moment}>"


Index("ix_chapters_project_status", Chapter.project_id, Chapter.status)
Index("ix_char_states_project_chapter", CharacterState.project_id, CharacterState.chapter_number)
Index("ix_queue_project_status", GenerationQueue.project_id, GenerationQueue.status)
Index("ix_world_events_project", WorldEvent.project_id, WorldEvent.chapter_number)

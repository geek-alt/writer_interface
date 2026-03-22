import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal
from backend.database.models import (
    Chapter,
    CharacterState,
    GenerationQueue,
    MCProgression,
    Project,
    WorldEvent,
)


def _db():
    """Use as: with _db() as db: ..."""
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return _ctx()


def create_project(
    id: str,
    name: str,
    fandom: str,
    config_json: str,
    total_chapters: int = 0,
) -> Project:
    with _db() as db:
        project = Project(
            id=id,
            name=name,
            fandom=fandom,
            config_json=config_json,
            total_chapters=total_chapters,
        )
        db.add(project)
        db.flush()
        db.refresh(project)
        return project


def get_project(project_id: str) -> Optional[Project]:
    with _db() as db:
        return db.query(Project).filter(Project.id == project_id).first()


def list_projects() -> list[Project]:
    with _db() as db:
        return db.query(Project).order_by(Project.updated_at.desc()).all()


def update_project(project_id: str, **kwargs) -> Optional[Project]:
    with _db() as db:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        project.updated_at = datetime.utcnow()
        db.flush()
        db.refresh(project)
        return project


def delete_project(project_id: str) -> bool:
    with _db() as db:
        n = db.query(Project).filter(Project.id == project_id).delete()
        return n > 0


def upsert_chapter(
    project_id: str,
    chapter_number: int,
    title: str,
    content: str,
    summary: str = "",
    word_count: int = 0,
    status: str = "pending_review",
    quality_score: int = 0,
    consistency_issues: Optional[list] = None,
    generation_params: Optional[dict] = None,
    character_updates: Optional[dict] = None,
    world_updates: Optional[dict] = None,
    mc_progression: Optional[dict] = None,
    generation_time_seconds: float = 0.0,
) -> Chapter:
    with _db() as db:
        ch = (
            db.query(Chapter)
            .filter(Chapter.project_id == project_id, Chapter.chapter_number == chapter_number)
            .first()
        )
        data = dict(
            title=title,
            content=content,
            summary=summary,
            word_count=word_count,
            status=status,
            quality_score=quality_score,
            consistency_issues=json.dumps(consistency_issues or []),
            generation_params=json.dumps(generation_params or {}),
            character_updates_json=json.dumps(character_updates or {}),
            world_updates_json=json.dumps(world_updates or {}),
            mc_progression_json=json.dumps(mc_progression or {}),
            generation_time_seconds=generation_time_seconds,
            updated_at=datetime.utcnow(),
        )
        if ch:
            for k, v in data.items():
                setattr(ch, k, v)
        else:
            ch = Chapter(project_id=project_id, chapter_number=chapter_number, **data)
            db.add(ch)
        db.flush()
        db.refresh(ch)
        return ch


def get_chapter(project_id: str, chapter_number: int) -> Optional[Chapter]:
    with _db() as db:
        return (
            db.query(Chapter)
            .filter(Chapter.project_id == project_id, Chapter.chapter_number == chapter_number)
            .first()
        )


def get_chapters_by_project(
    project_id: str,
    include_content: bool = True,
    page: int = 1,
    limit: int = 50,
) -> tuple[list[Chapter], int]:
    """Returns (chapters, total_count). Content omitted when include_content=False."""
    with _db() as db:
        q = db.query(Chapter).filter(Chapter.project_id == project_id)
        total = q.count()
        chapters = q.order_by(Chapter.chapter_number).offset((page - 1) * limit).limit(limit).all()
        if not include_content:
            for ch in chapters:
                ch.content = ""
        return chapters, total


def update_chapter_status(project_id: str, chapter_number: int, status: str) -> bool:
    with _db() as db:
        n = (
            db.query(Chapter)
            .filter(Chapter.project_id == project_id, Chapter.chapter_number == chapter_number)
            .update({"status": status, "updated_at": datetime.utcnow()})
        )
        return n > 0


def delete_chapter(project_id: str, chapter_number: int) -> bool:
    with _db() as db:
        n = (
            db.query(Chapter)
            .filter(Chapter.project_id == project_id, Chapter.chapter_number == chapter_number)
            .delete()
        )
        return n > 0


def upsert_character_state(
    project_id: str,
    chapter_number: int,
    character_name: str,
    character_type: str = "canon",
    **kwargs,
) -> CharacterState:
    with _db() as db:
        cs = (
            db.query(CharacterState)
            .filter(
                CharacterState.project_id == project_id,
                CharacterState.chapter_number == chapter_number,
                CharacterState.character_name == character_name,
            )
            .first()
        )
        if cs:
            for k, v in kwargs.items():
                if hasattr(cs, k):
                    setattr(cs, k, v)
        else:
            cs = CharacterState(
                project_id=project_id,
                chapter_number=chapter_number,
                character_name=character_name,
                character_type=character_type,
                **kwargs,
            )
            db.add(cs)
        db.flush()
        db.refresh(cs)
        return cs


def get_latest_character_states(project_id: str) -> list[CharacterState]:
    """Returns the most recent state snapshot for each character."""
    with _db() as db:
        from sqlalchemy import func

        subq = (
            db.query(
                CharacterState.character_name,
                func.max(CharacterState.chapter_number).label("max_ch"),
            )
            .filter(CharacterState.project_id == project_id)
            .group_by(CharacterState.character_name)
            .subquery()
        )
        return (
            db.query(CharacterState)
            .join(
                subq,
                (CharacterState.character_name == subq.c.character_name)
                & (CharacterState.chapter_number == subq.c.max_ch),
            )
            .filter(CharacterState.project_id == project_id)
            .all()
        )


def get_character_history(project_id: str, character_name: str) -> list[CharacterState]:
    with _db() as db:
        return (
            db.query(CharacterState)
            .filter(
                CharacterState.project_id == project_id,
                CharacterState.character_name == character_name,
            )
            .order_by(CharacterState.chapter_number)
            .all()
        )


def add_to_queue(
    project_id: str,
    chapter_number: int,
    priority: int = 5,
    feedback: Optional[str] = None,
) -> GenerationQueue:
    with _db() as db:
        item = GenerationQueue(
            project_id=project_id,
            chapter_number=chapter_number,
            priority=priority,
            feedback=feedback,
        )
        db.add(item)
        db.flush()
        db.refresh(item)
        return item


def get_next_queued(project_id: str) -> Optional[GenerationQueue]:
    with _db() as db:
        return (
            db.query(GenerationQueue)
            .filter(
                GenerationQueue.project_id == project_id,
                GenerationQueue.status == "queued",
            )
            .order_by(GenerationQueue.priority, GenerationQueue.created_at)
            .first()
        )


def update_queue_status(
    queue_id: int,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    with _db() as db:
        item = db.query(GenerationQueue).filter(GenerationQueue.id == queue_id).first()
        if not item:
            return
        item.status = status
        if status == "processing":
            item.started_at = datetime.utcnow()
            item.attempts += 1
        elif status in ("completed", "failed"):
            item.completed_at = datetime.utcnow()
        if error_message:
            item.error_message = error_message


def recover_stuck_queue_items(project_id: str, stuck_after_minutes: int = 20) -> int:
    """
    Reset queue items stuck in 'processing' state.
    Called at application startup and periodically.
    Returns count of recovered items.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=stuck_after_minutes)
    with _db() as db:
        n = (
            db.query(GenerationQueue)
            .filter(
                GenerationQueue.project_id == project_id,
                GenerationQueue.status == "processing",
                GenerationQueue.started_at < cutoff,
            )
            .update({"status": "queued", "error_message": "Recovered from stuck state"})
        )
        return n


def clear_queue_for_project(project_id: str) -> int:
    with _db() as db:
        return (
            db.query(GenerationQueue)
            .filter(
                GenerationQueue.project_id == project_id,
                GenerationQueue.status == "queued",
            )
            .delete()
        )


def get_queue_status(project_id: str) -> dict:
    with _db() as db:
        rows = (
            db.query(GenerationQueue.status, GenerationQueue.status)
            .filter(GenerationQueue.project_id == project_id)
            .all()
        )
        from collections import Counter

        counts = Counter(r[0] for r in rows)
        return dict(counts)


def add_world_event(
    project_id: str,
    event_name: str,
    chapter_number: Optional[int] = None,
    event_type: str = "original",
    description: str = "",
    characters_involved: Optional[list] = None,
    consequences: Optional[list] = None,
    prevented: bool = False,
) -> WorldEvent:
    with _db() as db:
        ev = WorldEvent(
            project_id=project_id,
            event_name=event_name,
            chapter_number=chapter_number,
            event_type=event_type,
            description=description,
            characters_involved_json=json.dumps(characters_involved or []),
            consequences_json=json.dumps(consequences or []),
            prevented=prevented,
        )
        db.add(ev)
        db.flush()
        db.refresh(ev)
        return ev


def get_events_for_project(project_id: str) -> list[WorldEvent]:
    with _db() as db:
        return (
            db.query(WorldEvent)
            .filter(WorldEvent.project_id == project_id)
            .order_by(WorldEvent.chapter_number)
            .all()
        )


def upsert_mc_progression(
    project_id: str,
    chapter_number: int,
    **kwargs,
) -> MCProgression:
    with _db() as db:
        mp = (
            db.query(MCProgression)
            .filter(
                MCProgression.project_id == project_id,
                MCProgression.chapter_number == chapter_number,
            )
            .first()
        )
        if mp:
            for k, v in kwargs.items():
                if hasattr(mp, k):
                    setattr(mp, k, v)
        else:
            mp = MCProgression(project_id=project_id, chapter_number=chapter_number, **kwargs)
            db.add(mp)
        db.flush()
        db.refresh(mp)
        return mp


def get_mc_progression(project_id: str) -> list[MCProgression]:
    with _db() as db:
        return (
            db.query(MCProgression)
            .filter(MCProgression.project_id == project_id)
            .order_by(MCProgression.chapter_number)
            .all()
        )

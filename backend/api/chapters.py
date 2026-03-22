import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.state_manager import StateManager
from backend.database.crud import add_to_queue, get_chapters_by_project, update_chapter_status

router = APIRouter()
logger = logging.getLogger(__name__)


def _raise_api_error(exc: Exception) -> None:
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, ConnectionError):
        raise HTTPException(503, "LM Studio is not running. Please start it and load a model.") from exc
    if isinstance(exc, ValueError):
        raise HTTPException(422, str(exc)) from exc
    logger.exception("Unexpected error in chapters router")
    raise HTTPException(500, "An internal error occurred. Check novelforge.log for details.") from exc


class GenerateRequest(BaseModel):
    start_chapter: int
    end_chapter: int
    wait_for_approval: bool = True


class ReviewRequest(BaseModel):
    approved: bool
    feedback: str | None = None


class EditRequest(BaseModel):
    content: str


@router.post("/{project_id}/generate")
async def queue_generation(project_id: str, body: GenerateRequest):
    try:
        if body.start_chapter > body.end_chapter:
            raise HTTPException(400, "start_chapter must be <= end_chapter")
        for ch_num in range(body.start_chapter, body.end_chapter + 1):
            await asyncio.to_thread(add_to_queue, project_id, ch_num)
        return {
            "queued": body.end_chapter - body.start_chapter + 1,
            "project_id": project_id,
            "message": "Connect via WebSocket /ws/generate/{project_id} to start generation",
        }
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.get("/{project_id}")
async def list_chapters(
    project_id: str,
    page: int = 1,
    limit: int = 50,
    include_content: bool = False,
):
    try:
        chapters, total = await asyncio.to_thread(
            get_chapters_by_project, project_id, include_content, page, limit
        )
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "chapters": [
                {
                    "id": ch.id,
                    "chapter_number": ch.chapter_number,
                    "title": ch.title,
                    "word_count": ch.word_count,
                    "status": ch.status,
                    "quality_score": ch.quality_score,
                    "content": ch.content if include_content else None,
                }
                for ch in chapters
            ],
        }
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.get("/{project_id}/{chapter_num}")
async def get_chapter(project_id: str, chapter_num: int):
    try:
        sm = StateManager()
        ch = await sm.load_chapter(project_id, chapter_num)
        if not ch:
            raise HTTPException(404, f"Chapter {chapter_num} not found in project {project_id!r}")
        return ch
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.patch("/{project_id}/{chapter_num}")
async def edit_chapter(project_id: str, chapter_num: int, body: EditRequest):
    try:
        sm = StateManager()
        ch = await sm.load_chapter(project_id, chapter_num)
        if not ch:
            raise HTTPException(404, "Chapter not found")
        ch["content"] = body.content
        ch["word_count"] = len(body.content.split())
        ch["edited_manually"] = True
        await sm.save_chapter(project_id, chapter_num, ch)
        return {"saved": True, "word_count": ch["word_count"]}
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.post("/{project_id}/{chapter_num}/approve")
async def approve_chapter(project_id: str, chapter_num: int):
    try:
        ok = await asyncio.to_thread(update_chapter_status, project_id, chapter_num, "approved")
        if not ok:
            raise HTTPException(404, "Chapter not found")
        return {"status": "approved"}
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.post("/{project_id}/{chapter_num}/reject")
async def reject_chapter(project_id: str, chapter_num: int, body: ReviewRequest):
    try:
        await asyncio.to_thread(update_chapter_status, project_id, chapter_num, "rejected")
        if body.feedback:
            await asyncio.to_thread(add_to_queue, project_id, chapter_num, 1, body.feedback)
        return {"status": "rejected", "queued_for_regen": bool(body.feedback)}
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.delete("/{project_id}/{chapter_num}")
async def delete_chapter_endpoint(project_id: str, chapter_num: int, confirm: bool = False):
    try:
        if not confirm:
            raise HTTPException(400, "Pass ?confirm=true to delete a chapter permanently")
        from backend.database.crud import delete_chapter

        await asyncio.to_thread(delete_chapter, project_id, chapter_num)
        return {"deleted": True}
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)

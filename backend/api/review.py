import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.evaluator import ChapterEvaluator
from backend.core.singleton import llm
from backend.core.state_manager import StateManager
from backend.database.crud import get_chapters_by_project, update_chapter_status

router = APIRouter()
logger = logging.getLogger(__name__)


def _raise_api_error(exc: Exception) -> None:
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, ConnectionError):
        raise HTTPException(503, "LM Studio is not running. Please start it and load a model.") from exc
    if isinstance(exc, ValueError):
        raise HTTPException(422, str(exc)) from exc
    logger.exception("Unexpected error in review router")
    raise HTTPException(500, "An internal error occurred. Check novelforge.log for details.") from exc


class BulkApproveRequest(BaseModel):
    chapter_numbers: list[int]


@router.get("/{project_id}/pending")
async def list_pending(project_id: str):
    try:
        chapters, _ = await asyncio.to_thread(get_chapters_by_project, project_id, False, 1, 200)
        return [
            {
                "chapter_number": ch.chapter_number,
                "title": ch.title,
                "word_count": ch.word_count,
                "quality_score": ch.quality_score,
            }
            for ch in chapters
            if ch.status == "pending_review"
        ]
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.get("/{project_id}/consistency_check/{chapter_num}")
async def consistency_check(project_id: str, chapter_num: int):
    try:
        sm = StateManager()
        ch = await sm.load_chapter(project_id, chapter_num)
        if not ch:
            raise HTTPException(404, "Chapter not found")
        config = await sm.load_config(project_id)
        characters = await sm.load_characters(project_id)
        ev = ChapterEvaluator(llm)
        score, issues = ev.heuristic_score(ch.get("content", ""), config, characters)
        return {"score": score, "issues": issues}
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.post("/{project_id}/bulk_approve")
async def bulk_approve(project_id: str, body: BulkApproveRequest):
    try:
        results = []
        for ch_num in body.chapter_numbers:
            ok = await asyncio.to_thread(update_chapter_status, project_id, ch_num, "approved")
            results.append({"chapter": ch_num, "approved": ok})
        return {"results": results}
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)

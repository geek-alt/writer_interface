import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.state_manager import StateManager
from backend.database.crud import get_character_history

router = APIRouter()
logger = logging.getLogger(__name__)


def _raise_api_error(exc: Exception) -> None:
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, ConnectionError):
        raise HTTPException(503, "LM Studio is not running. Please start it and load a model.") from exc
    if isinstance(exc, ValueError):
        raise HTTPException(422, str(exc)) from exc
    logger.exception("Unexpected error in characters router")
    raise HTTPException(500, "An internal error occurred. Check novelforge.log for details.") from exc


class CharacterUpdateRequest(BaseModel):
    relationship_to_mc: float | None = None
    romance_progress: float | None = None
    current_status: str | None = None
    abilities: list[str] | None = None
    notes: str | None = None


@router.get("/{project_id}")
async def list_characters(project_id: str):
    try:
        sm = StateManager()
        chars = await sm.load_characters(project_id)
        result = {"mc": chars.get("mc", {}), "canon": [], "original": []}
        for category in ("canon", "original"):
            for name, data in chars.get(category, {}).items():
                result[category].append({"name": name, **data})
        return result
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.get("/{project_id}/{character_name}")
async def get_character(project_id: str, character_name: str):
    try:
        sm = StateManager()
        chars = await sm.load_characters(project_id)
        for cat in ("canon", "original"):
            if character_name in chars.get(cat, {}):
                return {"name": character_name, "category": cat, **chars[cat][character_name]}
        if chars.get("mc", {}).get("name") == character_name:
            return {"name": character_name, "category": "mc", **chars["mc"]}
        raise HTTPException(404, f"Character '{character_name}' not found")
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.patch("/{project_id}/{character_name}")
async def update_character(project_id: str, character_name: str, body: CharacterUpdateRequest):
    try:
        sm = StateManager()
        chars = await sm.load_characters(project_id)
        updates = body.model_dump(exclude_none=True)
        for cat in ("canon", "original"):
            if character_name in chars.get(cat, {}):
                chars[cat][character_name].update(updates)
                await sm.save_characters(project_id, chars)
                return {"updated": True}
        raise HTTPException(404, f"Character '{character_name}' not found")
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.post("/{project_id}")
async def add_character(project_id: str, body: dict):
    try:
        name = body.get("name")
        if not name:
            raise HTTPException(400, "name is required")
        sm = StateManager()
        chars = await sm.load_characters(project_id)
        if name in chars.get("original", {}):
            raise HTTPException(409, f"Character '{name}' already exists")
        chars.setdefault("original", {})[name] = {
            "relationship_to_mc": body.get("relationship_to_mc", 0),
            "romance_progress": 0,
            "romance_eligible": body.get("romance_eligible", False),
            "current_status": body.get("current_status", ""),
            "notes": body.get("notes", ""),
        }
        await sm.save_characters(project_id, chars)
        return {"created": True, "name": name}
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.get("/{project_id}/{character_name}/history")
async def character_history(project_id: str, character_name: str):
    try:
        history = await asyncio.to_thread(get_character_history, project_id, character_name)
        return [
            {
                "chapter": h.chapter_number,
                "relationship_to_mc": h.relationship_to_mc,
                "romance_progress": h.romance_progress,
                "current_status": h.current_status,
            }
            for h in history
        ]
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)

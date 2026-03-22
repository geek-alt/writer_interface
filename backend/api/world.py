import asyncio
import logging

from fastapi import APIRouter, HTTPException

from backend.core.state_manager import StateManager
from backend.database.crud import add_world_event, get_events_for_project

router = APIRouter()
logger = logging.getLogger(__name__)


def _raise_api_error(exc: Exception) -> None:
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, ConnectionError):
        raise HTTPException(503, "LM Studio is not running. Please start it and load a model.") from exc
    if isinstance(exc, ValueError):
        raise HTTPException(422, str(exc)) from exc
    logger.exception("Unexpected error in world router")
    raise HTTPException(500, "An internal error occurred. Check novelforge.log for details.") from exc


@router.get("/{project_id}")
async def get_world(project_id: str):
    try:
        sm = StateManager()
        return await sm.load_world_data(project_id)
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.patch("/{project_id}/power_system")
async def update_power_system(project_id: str, body: dict):
    try:
        sm = StateManager()
        world = await sm.load_world_data(project_id)
        world["power_system"] = {**world.get("power_system", {}), **body}
        await sm.save_world_data(project_id, world)
        return {"updated": True}
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.post("/{project_id}/events")
async def create_world_event(project_id: str, body: dict):
    try:
        ev = await asyncio.to_thread(
            add_world_event,
            project_id,
            body.get("event_name", "Unnamed Event"),
            body.get("chapter_number"),
            body.get("event_type", "original"),
            body.get("description", ""),
            body.get("characters_involved", []),
            body.get("consequences", []),
            body.get("prevented", False),
        )
        return {"created": True, "id": ev.id}
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.get("/{project_id}/events")
async def list_world_events(project_id: str):
    try:
        events = await asyncio.to_thread(get_events_for_project, project_id)
        return [
            {
                "id": e.id,
                "event_name": e.event_name,
                "chapter": e.chapter_number,
                "type": e.event_type,
                "prevented": e.prevented,
            }
            for e in events
        ]
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.get("/{project_id}/outline")
async def get_outline(project_id: str):
    try:
        sm = StateManager()
        return await sm.load_outline(project_id)
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.patch("/{project_id}/outline/{chapter_num}")
async def update_outline_beat(project_id: str, chapter_num: int, body: dict):
    try:
        sm = StateManager()
        outline = await sm.load_outline(project_id)
        for ch in outline.get("chapters", []):
            if ch.get("global_number") == chapter_num:
                ch.update(body)
                await sm.save_outline(project_id, outline)
                return {"updated": True}
        raise HTTPException(404, f"Chapter {chapter_num} not found in outline")
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)

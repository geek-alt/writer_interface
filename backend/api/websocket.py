import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.core.ability_progression import AbilityProgressionEngine
from backend.core.chapter_generator import ChapterGenerator
from backend.core.context_builder import ContextBuilder
from backend.core.evaluator import ChapterEvaluator
from backend.core.relationship_engine import RelationshipEngine
from backend.core.singleton import llm
from backend.core.state_manager import StateManager
from backend.core.summarizer import ChapterSummarizer

router = APIRouter()


class ConnectionManager:
    """Tracks active WebSocket connections per project. Supports broadcast."""

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, project_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(project_id, []).append(ws)

    def disconnect(self, project_id: str, ws: WebSocket) -> None:
        conns = self._connections.get(project_id, [])
        if ws in conns:
            conns.remove(ws)
        if not conns:
            self._connections.pop(project_id, None)

    async def send(self, ws: WebSocket, data: dict) -> None:
        try:
            await ws.send_json(data)
        except Exception:  # noqa: BLE001
            pass

    async def broadcast(self, project_id: str, data: dict) -> None:
        for ws in list(self._connections.get(project_id, [])):
            await self.send(ws, data)

    def active_projects(self) -> list[str]:
        return list(self._connections.keys())


manager = ConnectionManager()


def _build_generator() -> ChapterGenerator:
    state = StateManager()
    return ChapterGenerator(
        llm=llm,
        state=state,
        context_builder=ContextBuilder(llm),
        relationship_engine=RelationshipEngine(llm),
        ability_engine=AbilityProgressionEngine(llm),
        evaluator=ChapterEvaluator(llm),
        summarizer=ChapterSummarizer(llm),
    )


@router.websocket("/generate/{project_id}")
async def generation_websocket(websocket: WebSocket, project_id: str):
    await manager.connect(project_id, websocket)
    generator = _build_generator()

    async def send(data: dict) -> None:
        await manager.send(websocket, data)

    try:
        while True:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=600)
            data = json.loads(raw)
            action = data.get("action")

            if action == "ping":
                await send({"type": "pong"})

            elif action == "generate_chapters":
                start = int(data["start_chapter"])
                end = int(data["end_chapter"])
                wait = data.get("wait_for_approval", True)
                current = start

                while current <= end:
                    await send({"type": "chapter_start", "chapter": current})

                    async def progress(update: dict, _ch=current) -> None:
                        await send({"type": "progress", "chapter": _ch, **update})

                    try:
                        result = await generator.generate_chapter(
                            project_id=project_id,
                            chapter_number=current,
                            feedback=data.pop("feedback", None),
                            websocket_callback=progress,
                        )
                        await send(
                            {
                                "type": "chapter_complete",
                                "chapter": current,
                                "title": result.title,
                                "word_count": result.word_count,
                                "quality_score": result.quality_score,
                                "consistency_issues": result.consistency_issues,
                                "character_updates": result.character_updates,
                                "milestones": result.milestones_triggered,
                            }
                        )

                        if wait and current < end:
                            await send(
                                {
                                    "type": "waiting_approval",
                                    "chapter": current,
                                    "message": "Approve chapter to continue, or regenerate with feedback.",
                                }
                            )
                            response_raw = await asyncio.wait_for(
                                websocket.receive_text(), timeout=3600
                            )
                            response = json.loads(response_raw)
                            if response.get("action") == "regenerate":
                                data["feedback"] = response.get("feedback", "")
                                continue

                        current += 1

                    except ConnectionError as e:
                        await send({"type": "lm_studio_error", "error": str(e)})
                        break
                    except Exception as e:  # noqa: BLE001
                        await send({"type": "chapter_error", "chapter": current, "error": str(e)})
                        current += 1

                await send({"type": "batch_complete", "generated": list(range(start, current))})

    except WebSocketDisconnect:
        pass
    except asyncio.TimeoutError:
        await send(
            {
                "type": "timeout",
                "message": "Session timed out after 10 minutes of inactivity.",
            }
        )
    except Exception as e:  # noqa: BLE001
        await send({"type": "fatal_error", "error": str(e)})
    finally:
        manager.disconnect(project_id, websocket)

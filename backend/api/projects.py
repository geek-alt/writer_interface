import asyncio
import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.core.extractor import WorldExtractor
from backend.core.singleton import llm
from backend.core.state_manager import StateManager
from backend.database.crud import get_project, list_projects, update_project
from backend.services.project_service import ProjectService

router = APIRouter()
logger = logging.getLogger(__name__)

creation_jobs = {}

def _raise_api_error(exc: Exception) -> None:
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, ConnectionError):
        raise HTTPException(503, "LM Studio is not running. Please start it and load a model.") from exc
    if isinstance(exc, ValueError):
        raise HTTPException(422, str(exc)) from exc
    logger.exception("Unexpected error in projects router")
    raise HTTPException(500, "An internal error occurred. Check novelforge.log for details.") from exc


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    status: str | None = None


async def _run_creation_task(job_id: str, config_data: dict) -> None:
    try:
        service = ProjectService(llm)
        
        def update_status(msg: str):
            if job_id in creation_jobs:
                creation_jobs[job_id]["message"] = msg
                
        result = await service.create_project_full(config_data, status_callback=update_status)
        creation_jobs[job_id]["status"] = "completed"
        creation_jobs[job_id]["result"] = result
    except Exception as e:
        logger.exception(f"Background task failed for job {job_id}")
        creation_jobs[job_id]["status"] = "error"
        creation_jobs[job_id]["error"] = str(e)


@router.post("")
@router.post("/")
async def create_project_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile | None = File(None),
    config: str | None = Form(None),
):
    """Accept a JSON config file upload OR raw JSON string in form body."""
    try:
        if file:
            raw = await file.read()
            try:
                config_data = json.loads(raw)
            except json.JSONDecodeError as e:
                raise HTTPException(400, "Uploaded file is not valid JSON") from e
        elif config:
            try:
                config_data = json.loads(config)
            except json.JSONDecodeError as e:
                raise HTTPException(400, "config field is not valid JSON") from e
        else:
            raise HTTPException(400, "Provide either a JSON file upload or a config form field")

        config_data = {k: v for k, v in config_data.items() if not k.startswith("_")}

        extractor = WorldExtractor(llm)
        errors = extractor.validate_config(config_data)
        if errors:
            raise HTTPException(422, {"detail": "Config validation failed", "errors": errors})

        job_id = str(uuid.uuid4())
        creation_jobs[job_id] = {
            "status": "running",
            "message": "Initializing...",
            "result": None,
            "error": None
        }
        background_tasks.add_task(_run_creation_task, job_id, config_data)
        return {"job_id": job_id, "status": "running"}
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)

@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in creation_jobs:
        raise HTTPException(404, "Job not found")
    return creation_jobs[job_id]


@router.get("")
@router.get("/")
async def list_projects_endpoint():
    try:
        projects = await asyncio.to_thread(list_projects)
        return [
            {
                "id": p.id,
                "name": p.name,
                "fandom": p.fandom,
                "status": p.status,
                "current_chapter": p.current_chapter,
                "total_chapters": p.total_chapters,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in projects
        ]
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.get("/templates/download")
async def download_template():
    try:
        path = Path("backend/templates/config_template.json")
        if not path.exists():
            raise HTTPException(404, "Template not found")
        return FileResponse(
            str(path),
            filename="novelforge_config_template.json",
            media_type="application/json",
        )
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.get("/templates/fandoms")
async def list_fandoms():
    try:
        fandom_dir = Path("backend/templates/fandoms")
        return [f.stem for f in fandom_dir.glob("*.json")]
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.get("/templates/fandoms/{fandom}")
async def get_fandom_template(fandom: str):
    try:
        path = Path("backend/templates/fandoms") / f"{fandom.lower()}.json"
        if not path.exists():
            raise HTTPException(404, f"No template for fandom '{fandom}'")
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.get("/{project_id}")
async def get_project_endpoint(project_id: str):
    try:
        project = await asyncio.to_thread(get_project, project_id)
        if not project:
            raise HTTPException(404, f"Project {project_id!r} not found")
        state = await StateManager().load_state(project_id)
        return {
            "id": project.id,
            "name": project.name,
            "fandom": project.fandom,
            "status": project.status,
            "current_chapter": project.current_chapter,
            "total_chapters": project.total_chapters,
            "state": state,
        }
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.patch("/{project_id}")
async def update_project_endpoint(project_id: str, body: ProjectUpdateRequest):
    try:
        updates = body.model_dump(exclude_none=True)
        if not updates:
            raise HTTPException(400, "No update fields provided")
        project = await asyncio.to_thread(update_project, project_id, **updates)
        if not project:
            raise HTTPException(404, f"Project {project_id!r} not found")
        return {"updated": True, "id": project_id}
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.delete("/{project_id}")
async def delete_project_endpoint(project_id: str):
    try:
        service = ProjectService(llm)
        await service.delete_project_full(project_id)
        return {"deleted": True}
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.post("/{project_id}/export")
async def export_project(
    project_id: str,
    format: str,
    start_chapter: int = 1,
    end_chapter: int = 999,
):
    try:
        from backend.core.exporter import NovelExporter

        sm = StateManager()
        all_chapters = await sm.load_all_chapters(project_id)
        chapters = [
            ch
            for ch in all_chapters
            if start_chapter <= ch.get("number", 0) <= end_chapter
            and ch.get("status") == "approved"
        ]
        if not chapters:
            raise HTTPException(400, "No approved chapters in the requested range")
        exporter = NovelExporter(sm)
        if format == "docx":
            path = await exporter.export_docx(project_id, chapters)
        elif format == "epub":
            path = await exporter.export_epub(project_id, chapters)
        elif format == "pdf":
            path = await exporter.export_pdf(project_id, chapters)
        else:
            raise HTTPException(400, f"Unknown format '{format}'. Use: docx, epub, pdf")
        return {"download_url": f"/api/projects/{project_id}/export/{path.name}"}
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)


@router.get("/{project_id}/export/{filename}")
async def download_export(project_id: str, filename: str):
    try:
        path = Path("projects") / project_id / "exports" / filename
        if not path.exists():
            raise HTTPException(404, "Export file not found")
        return FileResponse(str(path), filename=filename)
    except Exception as exc:  # noqa: BLE001
        _raise_api_error(exc)

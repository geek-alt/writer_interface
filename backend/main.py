import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api import chapters, characters, projects, review, websocket, world
from backend.config import settings
from backend.core.singleton import llm
from backend.database.connection import init_db
from backend.database.crud import recover_stuck_queue_items

if settings.is_dev:
    from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await llm.initialize()

    from backend.database import models  # noqa: F401
    from backend.database.connection import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        project_ids = db.execute(text("SELECT id FROM projects")).fetchall()
        for (pid,) in project_ids:
            n = await asyncio.to_thread(recover_stuck_queue_items, pid)
            if n:
                print(f"[startup] Recovered {n} stuck queue items for project {pid}")
    finally:
        db.close()

    yield

    await llm.close()


app = FastAPI(
    title="NovelForge API",
    version="3.1",
    description="AI-powered fanfiction generation system",
    lifespan=lifespan,
)

if settings.is_dev:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(chapters.router, prefix="/api/chapters", tags=["Chapters"])
app.include_router(characters.router, prefix="/api/characters", tags=["Characters"])
app.include_router(world.router, prefix="/api/world", tags=["World"])
app.include_router(review.router, prefix="/api/review", tags=["Review"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


@app.get("/api/health", tags=["System"])
async def health():
    lm_status = await llm.check_connection()
    return {"status": "ok", "environment": settings.environment, "lm_studio": lm_status}


@app.get("/api/selftest", tags=["System"])
async def selftest():
    checks = []

    lm = await llm.check_connection()
    checks.append(
        {
            "name": "lm_studio_connection",
            "passed": lm["connected"],
            "message": lm.get("active_model", lm.get("error", "")),
        }
    )

    try:
        import uuid

        from backend.database.crud import create_project, delete_project

        tid = f"selftest-{uuid.uuid4()}"
        await asyncio.to_thread(create_project, tid, "__test__", "__test__", "{}", 0)
        await asyncio.to_thread(delete_project, tid)
        checks.append({"name": "database_write", "passed": True, "message": "Read/write OK"})
    except Exception as e:  # noqa: BLE001
        checks.append({"name": "database_write", "passed": False, "message": str(e)})

    try:
        p = settings.projects_path / "_selftest_"
        p.mkdir(exist_ok=True)
        (p / "test.txt").write_text("ok", encoding="utf-8")
        (p / "test.txt").unlink()
        p.rmdir()
        checks.append(
            {
                "name": "projects_dir_writable",
                "passed": True,
                "message": str(settings.projects_path),
            }
        )
    except Exception as e:  # noqa: BLE001
        checks.append({"name": "projects_dir_writable", "passed": False, "message": str(e)})

    if lm["connected"]:
        try:
            response = await llm.generate(
                [{"role": "user", "content": "Reply with exactly one word: OK"}]
            )
            passed = bool(response.strip())
            checks.append(
                {
                    "name": "llm_round_trip",
                    "passed": passed,
                    "message": response.strip()[:50],
                }
            )
        except Exception as e:  # noqa: BLE001
            checks.append({"name": "llm_round_trip", "passed": False, "message": str(e)})
    else:
        checks.append(
            {
                "name": "llm_round_trip",
                "passed": False,
                "message": "Skipped - LM Studio not connected",
            }
        )

    return {"passed": all(c["passed"] for c in checks), "checks": checks}


dist_path = Path(__file__).parent.parent / "frontend" / "dist"
if dist_path.exists():
    app.mount("/assets", StaticFiles(directory=str(dist_path / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        _ = full_path
        return FileResponse(str(dist_path / "index.html"))

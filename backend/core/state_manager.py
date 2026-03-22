import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import aiofiles

from backend.config import settings


class StateManager:
    PROJECTS_DIR = Path(settings.projects_dir)

    def __init__(self) -> None:
        self.PROJECTS_DIR.mkdir(exist_ok=True)

    def _project_path(self, project_id: str) -> Path:
        return self.PROJECTS_DIR / project_id

    def _chapters_dir(self, project_id: str) -> Path:
        return self._project_path(project_id) / "chapters"

    async def create_project_structure(self, project_id: str, config: dict) -> Path:
        p = self._project_path(project_id)
        p.mkdir(exist_ok=True)
        (p / "chapters").mkdir(exist_ok=True)
        (p / "exports").mkdir(exist_ok=True)
        (p / "backups").mkdir(exist_ok=True)
        await self._write_json(p / "config.json", config)
        await self._write_json(p / "world.json", {})
        await self._write_json(p / "characters.json", {"mc": {}, "canon": {}, "original": {}})
        await self._write_json(p / "outline.json", {"volumes": [], "chapters": []})
        await self._write_json(
            p / "state.json",
            {
                "current_chapter": 0,
                "status": "initialized",
                "last_updated": datetime.utcnow().isoformat(),
            },
        )
        return p

    async def load_config(self, project_id: str) -> dict:
        return await self._read_json(self._project_path(project_id) / "config.json")

    async def save_world_data(self, project_id: str, data: dict) -> None:
        await self._write_json(self._project_path(project_id) / "world.json", data)

    async def load_world_data(self, project_id: str) -> dict:
        return await self._read_json(self._project_path(project_id) / "world.json")

    async def save_characters(self, project_id: str, characters: dict) -> None:
        await self._write_json(self._project_path(project_id) / "characters.json", characters)

    async def load_characters(self, project_id: str) -> dict:
        return await self._read_json(self._project_path(project_id) / "characters.json")

    async def save_outline(self, project_id: str, outline: dict) -> None:
        await self._write_json(self._project_path(project_id) / "outline.json", outline)

    async def load_outline(self, project_id: str) -> dict:
        return await self._read_json(self._project_path(project_id) / "outline.json")

    async def load_state(self, project_id: str) -> dict:
        return await self._read_json(self._project_path(project_id) / "state.json")

    async def update_state(self, project_id: str, updates: dict) -> None:
        path = self._project_path(project_id) / "state.json"
        current = await self._read_json(path)
        current.update(updates)
        current["last_updated"] = datetime.utcnow().isoformat()
        await self._write_json(path, current)

    async def save_chapter(self, project_id: str, chapter_num: int, data: dict) -> None:
        path = self._chapters_dir(project_id) / f"{chapter_num:03d}.json"
        await self._write_json(path, data)
        state = await self.load_state(project_id)
        new_max = max(chapter_num, state.get("current_chapter", 0))
        await self.update_state(project_id, {"current_chapter": new_max})
        # Sync with sqlite tracking
        from backend.database.crud import update_project
        import asyncio
        await asyncio.to_thread(update_project, project_id, current_chapter=new_max)

    async def backup_chapter(self, project_id: str, chapter_num: int) -> None:
        src = self._chapters_dir(project_id) / f"{chapter_num:03d}.json"
        if not src.exists():
            return
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dst = self._project_path(project_id) / "backups" / f"{chapter_num:03d}_{ts}.json"
        shutil.copy2(src, dst)

    async def load_chapter(self, project_id: str, chapter_num: int) -> dict | None:
        path = self._chapters_dir(project_id) / f"{chapter_num:03d}.json"
        if not path.exists():
            return None
        return await self._read_json(path)

    async def load_all_chapters(self, project_id: str) -> list[dict]:
        d = self._chapters_dir(project_id)
        chapters: list[dict] = []
        for fp in sorted(d.glob("*.json")):
            chapters.append(await self._read_json(fp))
        return chapters

    def delete_project(self, project_id: str) -> None:
        p = self._project_path(project_id)
        if p.exists():
            shutil.rmtree(p)

    def get_project_size_mb(self, project_id: str) -> float:
        p = self._project_path(project_id)
        if not p.exists():
            return 0.0
        total = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        return round(total / (1024 * 1024), 2)

    def list_project_ids(self) -> list[str]:
        return [d.name for d in self.PROJECTS_DIR.iterdir() if d.is_dir()]

    async def _write_json(self, path: Path, data: dict) -> None:
        """Atomic write: write to .tmp, then os.replace(). Safe against crashes."""
        tmp = path.with_suffix(".tmp")
        async with aiofiles.open(tmp, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        os.replace(tmp, path)

    async def _read_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            raw = await f.read()
        return json.loads(raw) if raw.strip() else {}

import asyncio
import json
import uuid

from backend.core.extractor import WorldExtractor
from backend.core.llm_client import LMStudioClient
from backend.core.state_manager import StateManager
from backend.database.crud import create_project, delete_project


class ProjectService:
    def __init__(self, llm: LMStudioClient) -> None:
        self.llm = llm
        self.extractor = WorldExtractor(llm)
        self.sm = StateManager()

    async def create_project_full(self, config: dict, status_callback=None) -> dict:
        """
        Full creation pipeline. Rolls back on failure - no half-state projects.
        """
        project_id = str(uuid.uuid4())
        fs_created = False

        if status_callback: status_callback("Initializing project scaffolding...")

        try:
            await self.sm.create_project_structure(project_id, config)
            fs_created = True

            total_chapters = sum(v.get("chapters", 0) for v in config.get("structure", {}).get("volumes", []))
            
            if status_callback: status_callback("Registering project in local database...")
            await asyncio.to_thread(
                create_project,
                project_id,
                config.get("project_name", "Untitled"),
                config.get("fandom", "Unknown"),
                json.dumps(config),
                total_chapters,
            )

            extraction = await self.extractor.extract_complete(config, status_callback=status_callback)

            if status_callback: status_callback("Saving intelligence files...")
            await self.sm.save_world_data(project_id, extraction["world"])
            await self.sm.save_characters(project_id, extraction["characters"])
            outline = self.extractor.build_outline(config, extraction["timeline"])
            await self.sm.save_outline(project_id, outline)

            if status_callback: status_callback("Project initialization successfully finished!")
            return {
                "project_id": project_id,
                "name": config.get("project_name"),
                "fandom": config.get("fandom"),
                "status": "created",
                "extraction_summary": {
                    "canon_characters": len(extraction["characters"].get("canon", {})),
                    "chapters_planned": len(extraction["timeline"]),
                    "volumes": len(config.get("structure", {}).get("volumes", [])),
                },
            }

        except Exception as e:  # noqa: BLE001
            if fs_created:
                self.sm.delete_project(project_id)
            try:
                await asyncio.to_thread(delete_project, project_id)
            except Exception:  # noqa: BLE001
                pass
            raise RuntimeError(f"Project creation failed and was rolled back: {e}") from e

    async def delete_project_full(self, project_id: str) -> None:
        await asyncio.to_thread(delete_project, project_id)
        self.sm.delete_project(project_id)

    async def get_project_summary(self, project_id: str) -> dict:
        from backend.database.crud import get_chapters_by_project, get_latest_character_states

        chapters, total = await asyncio.to_thread(get_chapters_by_project, project_id, False, 1, 200)
        by_status: dict[str, int] = {}
        total_words = 0
        for ch in chapters:
            by_status[ch.status] = by_status.get(ch.status, 0) + 1
            total_words += ch.word_count or 0
        char_states = await asyncio.to_thread(get_latest_character_states, project_id)
        return {
            "total_chapters": total,
            "chapters_by_status": by_status,
            "total_words": total_words,
            "character_count": len(char_states),
        }

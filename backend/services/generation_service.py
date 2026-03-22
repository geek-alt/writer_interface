"""
HTTP-triggered (non-WebSocket) batch generation service.
Handles queue processing and stuck-job recovery.
"""

import asyncio

from backend.core.ability_progression import AbilityProgressionEngine
from backend.core.chapter_generator import ChapterGenerator
from backend.core.context_builder import ContextBuilder
from backend.core.evaluator import ChapterEvaluator
from backend.core.llm_client import LMStudioClient
from backend.core.relationship_engine import RelationshipEngine
from backend.core.state_manager import StateManager
from backend.core.summarizer import ChapterSummarizer
from backend.database.crud import (
    get_next_queued,
    get_queue_status,
    recover_stuck_queue_items,
    update_queue_status,
)


class GenerationService:
    def __init__(self, llm: LMStudioClient) -> None:
        self.llm = llm

    def _build_generator(self) -> ChapterGenerator:
        state = StateManager()
        return ChapterGenerator(
            llm=self.llm,
            state=state,
            context_builder=ContextBuilder(self.llm),
            relationship_engine=RelationshipEngine(self.llm),
            ability_engine=AbilityProgressionEngine(self.llm),
            evaluator=ChapterEvaluator(self.llm),
            summarizer=ChapterSummarizer(self.llm),
        )

    async def process_queue(self, project_id: str, max_chapters: int = 50) -> None:
        """
        Process the queue for a project. Runs in a background task.
        Stops when queue is empty or max_chapters reached.
        Stuck-job recovery runs at the start of every call.
        """
        await asyncio.to_thread(recover_stuck_queue_items, project_id)
        generator = self._build_generator()
        processed = 0

        while processed < max_chapters:
            item = await asyncio.to_thread(get_next_queued, project_id)
            if not item:
                break

            await asyncio.to_thread(update_queue_status, item.id, "processing")
            try:
                await generator.generate_chapter(
                    project_id=project_id,
                    chapter_number=item.chapter_number,
                    feedback=item.feedback,
                )
                await asyncio.to_thread(update_queue_status, item.id, "completed")
            except Exception as e:  # noqa: BLE001
                await asyncio.to_thread(update_queue_status, item.id, "failed", str(e))
            processed += 1

    async def get_queue_status(self, project_id: str) -> dict:
        return await asyncio.to_thread(get_queue_status, project_id)

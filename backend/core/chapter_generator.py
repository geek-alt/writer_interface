from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from backend.core.ability_progression import AbilityProgressionEngine
from backend.core.context_builder import ContextBuilder
from backend.core.evaluator import ChapterEvaluator
from backend.core.llm_client import GenerationConfig, LMStudioClient
from backend.core.relationship_engine import RelationshipEngine
from backend.core.state_manager import StateManager
from backend.core.summarizer import ChapterSummarizer


@dataclass
class GenerationResult:
    chapter_number: int
    title: str
    content: str
    word_count: int
    quality_score: int
    consistency_issues: list[str]
    character_updates: dict
    world_updates: dict
    mc_progression: dict
    milestones_triggered: list[dict]
    generation_time: float


class ChapterGenerator:
    def __init__(
        self,
        llm: LMStudioClient,
        state: StateManager,
        context_builder: ContextBuilder,
        relationship_engine: RelationshipEngine,
        ability_engine: AbilityProgressionEngine,
        evaluator: ChapterEvaluator,
        summarizer: ChapterSummarizer,
    ) -> None:
        self.llm = llm
        self.state = state
        self.context = context_builder
        self.rel_engine = relationship_engine
        self.ability_engine = ability_engine
        self.evaluator = evaluator
        self.summarizer = summarizer

    async def generate_chapter(
        self,
        project_id: str,
        chapter_number: int,
        feedback: Optional[str] = None,
        websocket_callback: Optional[Callable] = None,
    ) -> GenerationResult:
        start = datetime.utcnow()

        async def update(data: dict) -> None:
            if websocket_callback:
                try:
                    await websocket_callback(data)
                except Exception:  # noqa: BLE001
                    pass

        config = await self.state.load_config(project_id)
        world = await self.state.load_world_data(project_id)
        characters = await self.state.load_characters(project_id)
        outline = await self.state.load_outline(project_id)
        prev_chapters = await self.state.load_all_chapters(project_id)

        chapter_outline = next(
            (
                ch
                for ch in outline.get("chapters", [])
                if ch.get("global_number") == chapter_number
                or ch.get("chapter_number") == chapter_number
            ),
            {
                "global_number": chapter_number,
                "title": f"Chapter {chapter_number}",
                "key_beat": "Continue the story",
                "characters_involved": [],
            },
        )

        await update({"status": "building_context", "progress": 10})

        context_messages = await self.context.build(
            config=config,
            world=world,
            characters=characters,
            prev_chapters=prev_chapters,
            current_chapter=chapter_number,
            outline=chapter_outline,
        )

        generation_prompt = self._build_prompt(config, chapter_outline, characters, feedback)
        context_messages.append({"role": "user", "content": generation_prompt})

        await update({"status": "generating", "progress": 15})

        full_text = ""
        chunk_count = 0

        gen_config = GenerationConfig(
            temperature=0.8,
            max_tokens=int(
                config.get("generation_preferences", {}).get("words_per_chapter", 3500) * 1.5
            ),
            frequency_penalty=0.1,
        )

        async for chunk in self.llm.generate_stream(context_messages, gen_config):
            full_text += chunk
            chunk_count += 1
            if chunk_count % 15 == 0:
                await update(
                    {
                        "status": "generating",
                        "progress": min(60, 15 + chunk_count // 3),
                        "preview": full_text[-400:],
                    }
                )

        await update({"status": "analyzing", "progress": 65})

        char_changes = await self.rel_engine.extract_changes(
            full_text, characters, chapter_number, chapter_outline
        )
        characters, milestones = self.rel_engine.apply_changes(
            characters, char_changes, chapter_number
        )
        await self.state.save_characters(project_id, characters)

        await update({"status": "tracking_progression", "progress": 75})

        mc_prog = await self.ability_engine.track_progression(
            full_text, characters.get("mc", {}), chapter_number, config
        )
        characters["mc"] = self.ability_engine.apply_progression(
            characters.get("mc", {}), mc_prog
        )
        await self.state.save_characters(project_id, characters)

        await update({"status": "evaluating", "progress": 85})

        quality_score, issues = self.evaluator.heuristic_score(full_text, config, characters)

        await update({"status": "summarizing", "progress": 90})

        summary = await self.summarizer.summarize_chapter(
            {
                "number": chapter_number,
                "title": chapter_outline.get("title", f"Chapter {chapter_number}"),
                "content": full_text,
            }
        )

        await self.state.backup_chapter(project_id, chapter_number)
        chapter_data = {
            "number": chapter_number,
            "title": chapter_outline.get("title", f"Chapter {chapter_number}"),
            "content": full_text,
            "summary": summary,
            "word_count": len(full_text.split()),
            "status": "pending_review",
            "quality_score": quality_score,
            "consistency_issues": issues,
            "character_updates": char_changes,
            "mc_progression": mc_prog,
            "milestones_triggered": milestones,
            "generated_at": datetime.utcnow().isoformat(),
            "generation_time": (datetime.utcnow() - start).total_seconds(),
        }
        await self.state.save_chapter(project_id, chapter_number, chapter_data)

        result = GenerationResult(
            chapter_number=chapter_number,
            title=chapter_data["title"],
            content=full_text,
            word_count=chapter_data["word_count"],
            quality_score=quality_score,
            consistency_issues=issues,
            character_updates=char_changes,
            world_updates={},
            mc_progression=mc_prog,
            milestones_triggered=milestones,
            generation_time=chapter_data["generation_time"],
        )

        await update(
            {
                "status": "complete",
                "progress": 100,
                "word_count": result.word_count,
                "quality_score": result.quality_score,
            }
        )
        return result

    async def regenerate_chapter(
        self,
        project_id: str,
        chapter_number: int,
        feedback: str,
        websocket_callback: Optional[Callable] = None,
    ) -> GenerationResult:
        """Backup existing, regenerate with feedback."""
        await self.state.backup_chapter(project_id, chapter_number)
        return await self.generate_chapter(
            project_id,
            chapter_number,
            feedback=feedback,
            websocket_callback=websocket_callback,
        )

    def _build_prompt(
        self,
        config: dict,
        outline: dict,
        characters: dict,
        feedback: Optional[str],
    ) -> str:
        _ = config
        mc = characters.get("mc", {})
        mc_name = mc.get("name", "MC")
        parts = [
            f"Write Chapter {outline.get('global_number', '?')}: {outline.get('title', '')}",
            "",
            f"Key plot beat: {outline.get('key_beat', 'Continue the story')}",
            f"Characters to feature: {', '.join(outline.get('characters_involved', []))}",
            f"Relationship goals: {', '.join(outline.get('relationship_developments', []))}",
            f"MC growth: {outline.get('mc_growth', 'Character development')}",
            "",
            "AVOID these common mistakes:",
            f"- Do NOT have {mc_name} explain their inner world to others",
            "- Do NOT use the word 'suddenly' to skip over cause-and-effect",
            "- Do NOT resolve conflict in the same scene it was introduced",
            "- Do NOT end the chapter with the MC going to sleep",
        ]
        if feedback:
            parts += ["", "REGENERATION FEEDBACK - address every point listed:", feedback]
        parts += ["", f"Begin writing Chapter {outline.get('global_number', '?')} now:"]
        return "\n".join(parts)

import asyncio
from pathlib import Path

from backend.core.llm_client import GenerationConfig, LMStudioClient


class ChapterSummarizer:
    def __init__(self, llm: LMStudioClient) -> None:
        self.llm = llm
        self._template: str | None = None

    def _load_template(self) -> str:
        if self._template is None:
            template_path = Path("backend") / "templates" / "prompts" / "summarization.txt"
            try:
                self._template = template_path.read_text(encoding="utf-8")
            except FileNotFoundError:
                self._template = (
                    "Summarize this chapter in 2-4 sentences. "
                    "Name specific characters and events. Be concrete."
                )
        return self._template

    async def summarize_chapter(self, chapter: dict) -> str:
        prompt = (
            f"{self._load_template()}\n\n"
            f"CHAPTER {chapter.get('number')}: {chapter.get('title', '')}\n\n"
            f"{chapter.get('content', '')[:2000]}"
        )
        return await self.llm.generate(
            [{"role": "user", "content": prompt}],
            GenerationConfig(max_tokens=300, temperature=0.3),
        )

    async def batch_summarize(self, chapters: list[dict], concurrency: int = 3) -> list[str]:
        sem = asyncio.Semaphore(concurrency)

        async def limited(ch: dict) -> str:
            async with sem:
                return await self.summarize_chapter(ch)

        return await asyncio.gather(*[limited(ch) for ch in chapters])

    def one_line(self, chapter: dict) -> str:
        summary = chapter.get("summary", "")
        if summary:
            return f"Ch{chapter.get('number', 0)}: {summary[:120]}"
        return f"Ch{chapter.get('number', 0)}: {chapter.get('title', 'Unknown')} (no summary)"

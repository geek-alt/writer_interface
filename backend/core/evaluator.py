from backend.core.llm_client import LMStudioClient
from pathlib import Path


class ChapterEvaluator:
    def __init__(self, llm: LMStudioClient) -> None:
        self.llm = llm
        self._deep_template: str | None = None

    def _load_deep_template(self) -> str:
        if self._deep_template is None:
            path = Path("backend/templates/prompts/evaluation_deep.txt")
            try:
                self._deep_template = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                self._deep_template = (
                    "Evaluate this {fandom} fanfiction chapter.\n\n"
                    "OUTLINE REQUIREMENT: {key_beat}\n"
                    "MC: {mc_name}, IQ={mc_iq}, EQ={mc_eq}\n"
                    "PREVIOUS CHAPTER: {previous_summary}\n\n"
                    "CHAPTER (first 2000 chars):\n{chapter_excerpt}\n\n"
                    "Evaluate for consistency, character voice, outline completion, and pacing."
                )
        return self._deep_template

    def heuristic_score(self, text: str, config: dict, characters: dict) -> tuple[int, list[str]]:
        issues: list[str] = []
        score = 70
        target = config.get("generation_preferences", {}).get("words_per_chapter", 3500)
        words = len(text.split())
        if words < target * 0.5:
            score -= 20
            issues.append(f"Too short: {words} words (target {target})")
        elif words >= target * 0.8:
            score += 10

        if '"' not in text and "\u201c" not in text:
            score -= 5
            issues.append("No dialogue detected - may read as a prose summary")

        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) < 5:
            score -= 10
            issues.append("Fewer than 5 paragraphs - likely underdeveloped")
        elif len(paragraphs) >= 10:
            score += 5

        mc_name = characters.get("mc", {}).get("name", "")
        if mc_name and mc_name not in text:
            score -= 15
            issues.append(f"MC name '{mc_name}' not found in chapter")

        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]
        if len(sentences) > 10:
            first_words = [s.split()[0].lower() for s in sentences if s.split()]
            if first_words:
                most_common = max(set(first_words), key=first_words.count)
                if first_words.count(most_common) / len(first_words) > 0.3:
                    issues.append(f"Repetitive sentence starts ('{most_common}' overused)")
                    score -= 5
        return max(0, min(95, score)), issues

    async def deep_evaluate(
        self,
        text: str,
        config: dict,
        characters: dict,
        outline: dict,
        previous_summary: str = "",
    ) -> tuple[int, list[str]]:
        prompt = self._load_deep_template().format(
            fandom=config.get("fandom"),
            key_beat=outline.get("key_beat", ""),
            mc_name=config.get("main_character", {}).get("name"),
            mc_iq=config.get("main_character", {}).get("iq"),
            mc_eq=config.get("main_character", {}).get("eq"),
            previous_summary=previous_summary or "N/A",
            chapter_excerpt=text[:2000],
        )
        schema = {
            "score": "integer 0-100",
            "issues": ["string"],
            "strengths": ["string"],
            "outline_completion_pct": "integer 0-100",
        }
        result = await self.llm.generate_structured([{"role": "user", "content": prompt}], schema)
        return int(result.get("score", 70)), result.get("issues", [])

from pathlib import Path

from backend.config import settings
from backend.core.llm_client import LMStudioClient, count_tokens


class ContextBuilder:
    def __init__(self, llm: LMStudioClient) -> None:
        self.llm = llm
        self.budget = settings.context_token_budget

    async def build(
        self,
        config: dict,
        world: dict,
        characters: dict,
        prev_chapters: list[dict],
        current_chapter: int,
        outline: dict,
    ) -> list[dict]:
        """
        Token budget allocation:
          30% - system prompt (world rules + character states)
          30% - recent chapters (last 2, full text)
          20% - older chapter summaries
          20% - reserved for generation prompt + response
        """
        messages: list[dict] = []
        budget_system = int(self.budget * 0.30)
        budget_recent = int(self.budget * 0.30)
        budget_summary = int(self.budget * 0.20)

        system = self._build_system_prompt(config, world, current_chapter)
        char_states = self._format_character_states(characters, outline)
        system_full = system + "\n\n" + char_states
        if count_tokens(system_full) > budget_system:
            system_full = system + "\n\n" + char_states[: budget_system * 3]
        messages.append({"role": "system", "content": system_full})

        old_chapters = [ch for ch in prev_chapters if ch.get("number", 0) < current_chapter - 2]
        if old_chapters:
            summaries = [
                f"Ch{ch['number']}: {ch.get('summary') or ch.get('title', 'No summary')}"
                for ch in old_chapters
            ]
            summary_text = "STORY SO FAR:\n" + "\n".join(summaries)
            if count_tokens(summary_text) <= budget_summary:
                messages.append({"role": "system", "content": summary_text})

        recent = sorted(
            [ch for ch in prev_chapters if ch.get("number", 0) >= current_chapter - 2],
            key=lambda x: x.get("number", 0),
        )
        used_recent = 0
        for ch in recent:
            content = ch.get("content", "")
            tokens = count_tokens(content)
            if used_recent + tokens <= budget_recent:
                messages.append(
                    {
                        "role": "assistant",
                        "content": f"Chapter {ch['number']}: {ch.get('title', '')}\n\n{content}",
                    }
                )
                used_recent += tokens

        messages.append(
            {
                "role": "system",
                "content": (
                    "CURRENT CHAPTER OUTLINE:\n"
                    f"Chapter {outline.get('global_number', current_chapter)}: {outline.get('title', '')}\n"
                    f"Key beat: {outline.get('key_beat', '')}\n"
                    f"Characters involved: {', '.join(outline.get('characters_involved', []))}\n"
                    f"Relationship focus: {', '.join(outline.get('relationship_developments', []))}\n"
                    f"MC growth: {outline.get('mc_growth', '')}"
                ),
            }
        )
        return messages

    def _build_system_prompt(self, config: dict, world: dict, chapter_num: int) -> str:
        mc = config.get("main_character", {})
        template_path = Path("backend") / "templates" / "prompts" / "chapter_generation.txt"
        try:
            template = template_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            template = "Write the chapter as specified."
        template = template.replace("{mc_name}", mc.get("name", "MC"))
        template = template.replace(
            "{words_per_chapter}",
            str(config.get("generation_preferences", {}).get("words_per_chapter", 3500)),
        )
        return (
            f"{template}\n\n"
            f"STORY: {config.get('fandom')} - {config.get('project_name')}\n"
            f"Chapter {chapter_num} of {config.get('structure', {}).get('total_chapters', '?')}\n\n"
            f"MC: {mc.get('name')} | IQ {mc.get('iq')} | EQ {mc.get('eq')}\n"
            f"Personality: {mc.get('initial_personality', '')}\n\n"
            "WORLD POWER SYSTEM:\n"
            f"{world.get('power_system', {}).get('mechanics', 'Standard')}\n"
            f"Limitations: {'; '.join(world.get('power_system', {}).get('limitations', []))}"
        )

    def _format_character_states(self, characters: dict, outline: dict) -> str:
        """
        Only include characters whose relationship != 0 OR who appear in the chapter outline.
        This prevents bloating the context with irrelevant NPCs.
        """
        relevant = set(outline.get("characters_involved", []))
        lines = ["CURRENT CHARACTER STATES:"]
        mc = characters.get("mc", {})
        if mc:
            lines.append(f"\n{mc.get('name', 'MC')} (Protagonist):")
            lines.append(f"  Status: {mc.get('current_status', 'Active')}")
            lines.append(f"  Power level: {mc.get('power_level', 50)}/100")
            learned = mc.get("abilities", {}).get("current", [])
            if learned:
                lines.append(f"  Abilities: {', '.join(learned[:8])}")

        merged = {**characters.get("canon", {}), **characters.get("original", {})}
        for name, data in merged.items():
            rel = data.get("relationship_to_mc", 0)
            rom = data.get("romance_progress", 0)
            if rel == 0 and rom == 0 and name not in relevant:
                continue
            rel_label = (
                "Hostile"
                if rel < -30
                else "Cool"
                if rel < 0
                else "Neutral"
                if rel < 30
                else "Friendly"
                if rel < 70
                else "Close"
            )
            lines.append(f"\n{name}:")
            lines.append(f"  Relationship: {rel_label} ({rel:+.0f}/100)")
            if rom > 0:
                lines.append(f"  Romance: {rom:.0f}/100")
            if data.get("current_status"):
                lines.append(f"  Status: {data['current_status']}")
        return "\n".join(lines)

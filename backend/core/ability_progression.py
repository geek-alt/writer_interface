from backend.core.llm_client import LMStudioClient


class AbilityProgressionEngine:
    PROGRESSION_TYPES = {
        "Innovation": "MC derives new techniques from first principles - emphasize creative problem-solving",
        "Bloodline": "MC unlocks hereditary powers through emotional triggers - emphasize dramatic moments",
        "Hardwork": "MC improves through dedicated training - emphasize effort and incremental growth",
        "System": "MC receives guided power upgrades - emphasize system notifications and criteria",
    }

    def __init__(self, llm: LMStudioClient) -> None:
        self.llm = llm

    async def track_progression(
        self,
        chapter_text: str,
        mc_data: dict,
        chapter_number: int,
        config: dict,
    ) -> dict:
        prog_type = config.get("main_character", {}).get("power_progression_type", "Hardwork")
        existing = mc_data.get("abilities", {}).get("current", [])
        excerpt = chapter_text[:3000]

        prompt = (
            f"Progression type: {prog_type} - {self.PROGRESSION_TYPES.get(prog_type, '')}\n\n"
            f"CHAPTER (first 3000 chars):\n{excerpt}\n\n"
            f"MC existing abilities: {existing}\n\n"
            "Be CONSERVATIVE. Most chapters: 0 new abilities. Identify only what explicitly happened:\n"
            "1. New abilities learned or discovered\n"
            "2. Existing abilities improved in mastery\n"
            "3. Abilities actively used in this chapter\n"
            "4. Did MC use strategic thinking (IQ moment)?\n"
            "5. Did MC use emotional intelligence (EQ moment)?\n"
            "6. Power level change (-2 to +5, 0 if no meaningful change)"
        )
        schema = {
            "abilities_learned": [
                {"name": "string", "category": "jutsu|skill|knowledge|stat", "source": "string"}
            ],
            "abilities_improved": [{"name": "string", "new_mastery_level": "integer 1-4"}],
            "abilities_used": ["string"],
            "iq_moment": "boolean",
            "eq_moment": "boolean",
            "power_level_delta": "integer -2 to +5",
        }
        result = await self.llm.generate_structured(
            [{"role": "user", "content": prompt}], schema, max_retries=2
        )
        result["chapter_number"] = chapter_number
        return result

    def apply_progression(self, mc_data: dict, progression: dict) -> dict:
        abilities = mc_data.get("abilities")
        if not isinstance(abilities, dict):
            abilities = {"current": [], "mastery": {}}
            mc_data["abilities"] = abilities

        current = abilities.get("current")
        if not isinstance(current, list):
            current = []
            abilities["current"] = current

        mastery = abilities.get("mastery")
        if not isinstance(mastery, dict):
            mastery = {}
            abilities["mastery"] = mastery

        for ab in progression.get("abilities_learned", []):
            name = ab.get("name")
            if not name:
                continue
            if name not in current:
                current.append(name)
                mastery[name] = 1
        for ab in progression.get("abilities_improved", []):
            name = ab.get("name")
            if not name:
                continue
            mastery[name] = ab.get("new_mastery_level", 2)
        delta = progression.get("power_level_delta", 0)
        mc_data["power_level"] = max(1, min(100, mc_data.get("power_level", 50) + delta))
        return mc_data

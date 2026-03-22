from backend.core.llm_client import LMStudioClient


class RelationshipEngine:
    MILESTONES = {
        20: "initial_positive_impression",
        40: "considered_an_acquaintance",
        60: "genuine_friendship_forming",
        75: "trusted_friend",
        85: "close_confidant",
        95: "unbreakable_bond",
        -20: "growing_distrust",
        -50: "open_hostility",
        -80: "sworn_enemy",
    }
    ROMANCE_MILESTONES = {
        20: "subtle_attraction",
        40: "undeniable_feelings",
        60: "romantic_tension",
        80: "confession_imminent",
        95: "mutual_romance_confirmed",
    }

    def __init__(self, llm: LMStudioClient) -> None:
        self.llm = llm

    async def extract_changes(
        self,
        chapter_text: str,
        characters: dict,
        chapter_number: int,
        outline: dict,
    ) -> dict:
        """
        Smart excerpt: first 1500 chars + last 1500 chars + paragraphs
        containing character names from the outline's characters_involved list.
        This ensures the full chapter is effectively covered.
        """
        involved = set(outline.get("characters_involved", []))
        excerpt = self._smart_excerpt(chapter_text, involved)

        prompt = (
            "Analyze this chapter excerpt for character state changes.\n\n"
            f"EXCERPT:\n{excerpt}\n\n"
            f"CURRENT STATES:\n{self._format_states(characters)}\n\n"
            "Rules:\n"
            "- Max relationship delta per chapter: +-25\n"
            "- Max romance delta per chapter: +15\n"
            "- Only return characters whose state actually changed\n"
            "- Romance delta only applies if romance_eligible is true"
        )
        schema = {
            "changes": [
                {
                    "character_name": "string",
                    "relationship_delta": "integer -25 to +25",
                    "romance_delta": "integer 0 to +15",
                    "status_change": "string or null",
                    "abilities_gained": ["string"],
                    "notes": "string describing what changed and why",
                }
            ]
        }
        result = await self.llm.generate_structured(
            [{"role": "user", "content": prompt}],
            schema,
            max_retries=2,
        )
        return {c["character_name"]: c for c in result.get("changes", [])}

    def apply_changes(
        self,
        characters: dict,
        changes: dict,
        chapter_number: int,
    ) -> tuple[dict, list[dict]]:
        milestones: list[dict] = []
        for category in ("canon", "original"):
            for name, data in characters.get(category, {}).items():
                if name not in changes:
                    continue
                delta = changes[name]
                old_rel = data.get("relationship_to_mc", 0)
                old_rom = data.get("romance_progress", 0)
                new_rel = max(-100, min(100, old_rel + delta.get("relationship_delta", 0)))
                new_rom = max(0, min(100, old_rom + delta.get("romance_delta", 0)))
                data["relationship_to_mc"] = new_rel
                data["romance_progress"] = new_rom

                for threshold, label in self.MILESTONES.items():
                    crossed = (threshold > 0 and old_rel < threshold <= new_rel) or (
                        threshold < 0 and old_rel > threshold >= new_rel
                    )
                    if crossed:
                        milestones.append(
                            {
                                "character": name,
                                "milestone": label,
                                "chapter": chapter_number,
                            }
                        )

                if data.get("romance_eligible"):
                    for threshold, label in self.ROMANCE_MILESTONES.items():
                        if old_rom < threshold <= new_rom:
                            milestones.append(
                                {
                                    "character": name,
                                    "milestone": f"romance_{label}",
                                    "chapter": chapter_number,
                                }
                            )
                if delta.get("status_change"):
                    data["current_status"] = delta["status_change"]
                data.setdefault("mc_interactions", []).append(
                    {"chapter": chapter_number, "notes": delta.get("notes", "")}
                )
        return characters, milestones

    def _smart_excerpt(self, text: str, involved_names: set) -> str:
        """First 1500 + last 1500 + any paragraph containing an involved character name."""
        head = text[:1500]
        tail = text[-1500:]
        extra_paragraphs: list[str] = []
        for para in text.split("\n\n"):
            if any(name in para for name in involved_names):
                if para not in head and para not in tail:
                    extra_paragraphs.append(para[:400])
        extra = "\n\n".join(extra_paragraphs[:5])
        return f"{head}\n\n[...]\n\n{extra}\n\n[...]\n\n{tail}"

    def _format_states(self, chars: dict) -> str:
        lines: list[str] = []
        for cat in ("canon", "original"):
            for name, d in chars.get(cat, {}).items():
                lines.append(
                    f"  {name}: rel={d.get('relationship_to_mc', 0):+.0f}, "
                    f"romance={d.get('romance_progress', 0):.0f}, "
                    f"eligible={d.get('romance_eligible', False)}"
                )
        return "\n".join(lines) or "  (no secondary characters yet)"

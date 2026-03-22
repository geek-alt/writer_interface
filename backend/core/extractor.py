from pathlib import Path
from typing import Any
import json

from backend.core.llm_client import LMStudioClient


class WorldExtractor:
    FANDOM_TEMPLATES = {
        "naruto": "backend/templates/fandoms/naruto.json",
        "marvel": "backend/templates/fandoms/marvel.json",
        "harry_potter": "backend/templates/fandoms/harry_potter.json",
    }
    PROMPT_TEMPLATES = {
        "world": Path("backend/templates/prompts/extraction_world.txt"),
        "mc": Path("backend/templates/prompts/extraction_mc.txt"),
        "canon": Path("backend/templates/prompts/extraction_canon.txt"),
        "timeline": Path("backend/templates/prompts/extraction_timeline.txt"),
    }

    def __init__(self, llm: LMStudioClient) -> None:
        self.llm = llm

    def validate_config(self, config: dict) -> list[str]:
        errors: list[str] = []
        if not config.get("project_name"):
            errors.append("project_name is required")
        if not config.get("fandom"):
            errors.append("fandom is required")
        mc = config.get("main_character", {})
        if not mc.get("name"):
            errors.append("main_character.name is required")
        vols = config.get("structure", {}).get("volumes", [])
        if not vols:
            errors.append("structure.volumes must have at least one entry")
        for i, vol in enumerate(vols):
            if not vol.get("name"):
                errors.append(f"structure.volumes[{i}].name is required")
            if not isinstance(vol.get("chapters"), int) or vol["chapters"] < 1:
                errors.append(f"structure.volumes[{i}].chapters must be a positive integer")
        return errors

    async def extract_complete(self, config: dict, status_callback=None) -> dict[str, Any]:
        """Run full extraction pipeline. Returns world, characters, timeline, constraints."""
        fandom_data = self._load_fandom_template(config.get("fandom", ""))
        
        if status_callback: status_callback("Extracting world lore and mechanics...")
        world_data = await self._extract_world(config, fandom_data)
        
        if status_callback: status_callback("Synthesizing character profiles & dynamics...")
        characters = await self._extract_characters(config, world_data, fandom_data)
        
        if status_callback: status_callback("Plotting chapter-by-chapter story timeline...")
        timeline = await self._build_timeline(config, world_data)
        
        if status_callback: status_callback("Applying core writing constraints...")
        constraints = self._build_constraints(config)
        
        if status_callback: status_callback("Finalizing extraction payload...")
        
        return {
            "world": world_data,
            "characters": characters,
            "timeline": timeline,
            "constraints": constraints,
        }

    def build_outline(self, config: dict, timeline: list[dict]) -> dict:
        """Convert timeline list into structured outline dict for state manager."""
        return {
            "volumes": config.get("structure", {}).get("volumes", []),
            "chapters": timeline,
        }

    def _load_fandom_template(self, fandom: str) -> dict:
        key = fandom.lower().replace(" ", "_")
        template_path = self.FANDOM_TEMPLATES.get(key)
        if template_path:
            try:
                return json.loads(Path(template_path).read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                pass
        return {}

    def _load_prompt_template(self, key: str, fallback: str) -> str:
        path = self.PROMPT_TEMPLATES.get(key)
        if not path:
            return fallback
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return fallback

    async def _extract_world(self, config: dict, fandom_data: dict) -> dict:
        template = self._load_prompt_template(
            "world",
            "Analyze this {fandom} fanfiction configuration and extract world structure.\n\n"
            "CONFIG:\n{config}\n\n"
            "FANDOM CANON DATA:\n{fandom_data}",
        )
        prompt = template.format(
            fandom=config.get("fandom"),
            config=config,
            fandom_data=fandom_data,
        )
        schema = {
            "power_system": {
                "name": "string",
                "mechanics": "string",
                "limitations": ["string"],
                "progression_rules": "string",
                "ranks": ["string"],
            },
            "factions": [{"name": "string", "alignment": "string", "key_members": ["string"]}],
            "locations": [{"name": "string", "significance": "string"}],
            "time_period": {"era": "string", "recent_events": ["string"]},
            "social_structure": {"hierarchy": ["string"], "important_customs": ["string"]},
        }
        return await self.llm.generate_structured([{"role": "user", "content": prompt}], schema)

    async def _extract_characters(self, config: dict, world_data: dict, fandom_data: dict) -> dict:
        mc_config = config.get("main_character", {})
        mc_template = self._load_prompt_template(
            "mc",
            "Create a detailed character sheet for this main character:\n{mc_config}\n\n"
            "World context:\n{time_period}",
        )
        mc_prompt = mc_template.format(
            mc_config=mc_config,
            time_period=world_data.get("time_period", {}),
        )
        mc_schema = {
            "name": "string",
            "age": "number",
            "appearance": "string",
            "personality": {
                "surface": "string",
                "hidden_depths": "string",
                "speech_pattern": "string",
                "iq_manifestation": "string",
                "eq_manifestation": "string",
            },
            "abilities": {"starting": ["string"], "potential": ["string"]},
            "goals": {"stated": ["string"], "hidden": ["string"]},
            "power_level": "number 1-100",
        }
        mc_data = await self.llm.generate_structured([{"role": "user", "content": mc_prompt}], mc_schema)

        canon_template = self._load_prompt_template(
            "canon",
            "For {fandom} at this time: {era}\n\n"
            "Use this fandom data as ground truth:\n{key_characters}",
        )
        canon_prompt = canon_template.format(
            fandom=config.get("fandom"),
            era=world_data.get("time_period", {}).get("era", "unknown"),
            key_characters=fandom_data.get("key_characters", []),
        )
        canon_schema = {
            "characters": [
                {
                    "name": "string",
                    "age": "number",
                    "faction": "string",
                    "rank_or_position": "string",
                    "personality_summary": "string",
                    "initial_attitude_to_strangers": "string",
                    "romance_eligible": "boolean",
                    "relationship_potential": "string",
                    "key_plot_points_ahead": ["string"],
                    "tragedies_to_prevent": ["string"],
                }
            ]
        }
        canon_raw = await self.llm.generate_structured(
            [{"role": "user", "content": canon_prompt}], canon_schema
        )
        canon = {}
        for c in canon_raw.get("characters", []):
            if not isinstance(c, dict):
                continue
            name = c.get("name")
            if not name:
                continue
            canon[name] = {
                **c,
                "relationship_to_mc": 0,
                "romance_progress": 0,
                "current_status": c.get("rank_or_position", c.get("faction", "Unknown")),
                "mc_interactions": [],
            }
        return {"mc": mc_data, "canon": canon, "original": {}}

    async def _build_timeline(self, config: dict, world_data: dict) -> list[dict]:
        timeline: list[dict] = []
        chapter_counter = 1
        timeline_template = self._load_prompt_template(
            "timeline",
            "Create a chapter-by-chapter timeline for \"{volume_name}\" ({chapters} chapters).\n"
            "Arc goals: {arc_goals}\n"
            "World: {time_period}",
        )
        for volume in config.get("structure", {}).get("volumes", []):
            prompt = timeline_template.format(
                volume_name=volume["name"],
                chapters=volume["chapters"],
                arc_goals=volume.get("arc_goals", []),
                time_period=world_data.get("time_period", {}),
            )
            schema = {
                "chapters": [
                    {
                        "title": "string",
                        "key_beat": "string",
                        "characters_involved": ["string"],
                        "relationship_developments": ["string"],
                        "mc_growth": "string",
                        "canon_events": ["string"],
                        "divergence_opportunities": ["string"],
                    }
                ]
            }
            result = await self.llm.generate_structured([{"role": "user", "content": prompt}], schema)
            for ch in result.get("chapters", []):
                ch["global_number"] = chapter_counter
                ch["volume"] = volume["name"]
                timeline.append(ch)
                chapter_counter += 1
        return timeline

    def _build_constraints(self, config: dict) -> dict:
        mc = config.get("main_character", {})
        return {
            "cannot_change": [
                "Fundamental world rules (unless AU specified)",
                "Characters core personalities until MC influence changes them",
                "Power system limitations",
            ],
            "must_maintain": [
                "MC IQ/EQ consistency",
                "Relationship progression cause-and-effect",
                "Timeline continuity",
            ],
            "mc_rules": [
                f"MC IQ {mc.get('iq', 100)} - must plan ahead, not react blindly",
                f"MC EQ {mc.get('eq', 100)} - must read emotional situations accurately",
                f"Knowledge: {mc.get('knowledge_retention', 'Partial')} - governs what MC can foresee",
            ],
        }

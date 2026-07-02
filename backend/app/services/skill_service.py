import json
from app.core.llm import llm


class SkillService:
    async def detect_skill_pattern(self, memories: list) -> dict:
        if len(memories) < 3:
            return None

        prompt = json.dumps(memories, default=str)
        system = "You are a skill detection engine. Identify reusable workflow patterns."
        user = f"""Analyze these memories for repeated workflow patterns.
Memories: {prompt}

If a reusable skill pattern exists, respond in JSON:
{{
  "name": "...",
  "description": "...",
  "steps": ["..."],
  "confidence": 0.0
}}
If no pattern, respond: {{"pattern": false}}"""

        try:
            content = await llm.chat(system, user, {"type": "json_object"})
            result = json.loads(content)
            if result.get("pattern") is False:
                return None
            return result
        except Exception:
            return None

    async def evolve_skill(self, skill_id: str, new_usage: dict) -> dict:
        prompt = json.dumps(new_usage, default=str)
        system = "You are a skill evolution engine. Improve skills based on new usage data."
        user = f"""Given existing skill usage data, suggest how to evolve this skill.
New usage: {prompt}

Return JSON with updated steps, best_practices, and confidence_score."""
        try:
            content = await llm.chat(system, user, {"type": "json_object"})
            return json.loads(content)
        except Exception:
            return {"steps": [], "best_practices": [], "confidence_score": 0.5}

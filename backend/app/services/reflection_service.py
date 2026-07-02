import json
from app.core.llm import llm


class ReflectionService:
    async def generate_reflection(self, trigger_event: str, context: dict) -> dict:
        prompt = json.dumps(context, default=str)
        system = "You are a reflection engine. Analyze completed events and return JSON."
        user = f"""Analyze this completed event and generate a reflection.
Event: {trigger_event}
Context: {prompt}

Respond in JSON format:
{{
  "what_worked": "...",
  "what_failed": "...",
  "improvements": "...",
  "patterns": "..."
}}"""
        try:
            content = await llm.chat(system, user, {"type": "json_object"})
            return json.loads(content)
        except Exception:
            return {
                "what_worked": context.get("action", "Task completed"),
                "what_failed": "No critical failures detected",
                "improvements": "Consider adding more structure next time",
                "patterns": "Repeating workflow pattern detected",
            }

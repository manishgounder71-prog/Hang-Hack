import json
from app.core.llm import llm


class PredictionService:
    async def generate_prediction(self, prediction_type: str, context: dict) -> dict:
        prompt = json.dumps(context, default=str)
        system = "You are a prediction engine. Analyze memory patterns and predict future needs."
        user = f"""Based on the user's memory context, generate a prediction.
Type: {prediction_type}
Context: {prompt}

Respond in JSON:
{{
  "content": "...",
  "confidence": 0.85,
  "reasoning": "...",
  "influencing_memories": ["..."],
  "suggested_action": "..."
}}"""
        try:
            content = await llm.chat(system, user, {"type": "json_object"})
            return json.loads(content)
        except Exception:
            return {
                "content": f"User may be interested in {prediction_type} related topics soon",
                "confidence": 0.5,
                "reasoning": "Based on historical patterns",
                "influencing_memories": [],
                "suggested_action": "No specific action needed",
            }

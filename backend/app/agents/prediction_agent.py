"""Prediction Agent — Future need forecasting with confidence calibration."""
import time
import math
from typing import Any


class PredictionAgent:
    """Generates predictions about future user needs with calibrated confidence
    scoring, temporal reasoning, and multi-type prediction support."""

    def __init__(self):
        self.name = "Prediction Agent"
        self._prediction_history: list[dict] = []
        self._max_history = 200
        self._confidence_baseline = 0.5

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def process(self, event: dict) -> dict:
        action = event.get("action", "predict")

        handlers = {
            "predict": self._predict,
            "predict_batch": self._predict_batch,
            "fulfill": self._mark_fulfilled,
            "calibrate": self._calibrate_confidence,
            "accuracy": self._get_accuracy_stats,
            "history": self._get_history,
        }
        handler = handlers.get(action)
        if handler is None:
            return {"agent": self.name, "status": "unknown_action", "action": action}

        try:
            result = await handler(event)
            return {"agent": self.name, "action": action, "status": "ok", **result}
        except Exception as e:
            return {"agent": self.name, "action": action, "status": "error", "error": str(e)}

    # ── Handlers ─────────────────────────────────────────────────────────

    async def _predict(self, event: dict) -> dict:
        from app.services.prediction_service import PredictionService

        prediction_type = event.get("type", "general")
        context = event.get("context", {})
        memories = event.get("memories", [])
        user_id = event.get("user_id", "")

        service = PredictionService()
        prediction = await service.generate_prediction(
            prediction_type=prediction_type,
            context={**context, "memories": memories[:10]},
        )

        # Calibrate confidence based on historical accuracy
        confidence = prediction.get("confidence", self._confidence_baseline)
        calibrated = self._calibrate_score(confidence, prediction_type)

        # Compute time horizon
        horizon = self._compute_time_horizon(prediction_type, context)

        enriched = {
            **prediction,
            "prediction_type": prediction_type,
            "confidence_calibrated": calibrated,
            "confidence_raw": confidence,
            "time_horizon": horizon,
            "user_id": user_id,
            "created_at": time.time(),
            "fulfilled": False,
        }

        self._prediction_history.append(enriched)
        if len(self._prediction_history) > self._max_history:
            self._prediction_history.pop(0)

        return {
            "prediction": enriched,
            "confidence": calibrated,
            "time_horizon": horizon,
        }

    async def _predict_batch(self, event: dict) -> dict:
        """Generate multiple predictions of different types simultaneously."""
        types = event.get("types", ["general", "technology", "learning", "project"])
        context = event.get("context", {})
        predictions = []

        for ptype in types:
            try:
                r = await self._predict({"type": ptype, "context": context})
                predictions.append(r.get("prediction", {}))
            except Exception:
                continue

        return {
            "predictions": predictions,
            "count": len(predictions),
        }

    async def _mark_fulfilled(self, event: dict) -> dict:
        """Mark a prediction as fulfilled or unfulfilled for accuracy tracking."""
        prediction_id = event.get("prediction_id", "")
        fulfilled = event.get("fulfilled", True)

        for p in self._prediction_history:
            if p.get("id") == prediction_id or p.get("content", "")[:30] == prediction_id:
                p["fulfilled"] = fulfilled
                p["fulfilled_at"] = time.time()
                break

        return {"status": "updated", "prediction_id": prediction_id, "fulfilled": fulfilled}

    async def _calibrate_confidence(self, event: dict) -> dict:
        """Recalibrate confidence based on historical prediction accuracy."""
        if not self._prediction_history:
            return {"baseline": self._confidence_baseline, "message": "No history to calibrate"}

        total = len(self._prediction_history)
        fulfilled = sum(1 for p in self._prediction_history if p.get("fulfilled"))
        accuracy = fulfilled / max(total, 1)

        # Adjust baseline toward accuracy
        self._confidence_baseline = 0.3 + (accuracy * 0.7)

        return {
            "baseline": round(self._confidence_baseline, 3),
            "accuracy": round(accuracy, 3),
            "total": total,
            "fulfilled": fulfilled,
        }

    async def _get_accuracy_stats(self, event: dict) -> dict:
        """Get comprehensive accuracy statistics."""
        if not self._prediction_history:
            return {"accuracy": 0, "total": 0, "by_type": {}}

        total = len(self._prediction_history)
        fulfilled = sum(1 for p in self._prediction_history if p.get("fulfilled"))
        by_type: dict[str, dict] = {}

        for p in self._prediction_history:
            ptype = p.get("prediction_type", "general")
            if ptype not in by_type:
                by_type[ptype] = {"total": 0, "fulfilled": 0}
            by_type[ptype]["total"] += 1
            if p.get("fulfilled"):
                by_type[ptype]["fulfilled"] += 1

        for t, stats in by_type.items():
            stats["accuracy"] = round(stats["fulfilled"] / max(stats["total"], 1), 3)

        return {
            "accuracy": round(fulfilled / max(total, 1), 3),
            "total": total,
            "fulfilled": fulfilled,
            "by_type": by_type,
            "confidence_baseline": round(self._confidence_baseline, 3),
        }

    async def _get_history(self, event: dict) -> dict:
        limit = event.get("limit", 20)
        return {"predictions": self._prediction_history[-limit:], "total": len(self._prediction_history)}

    # ── Intelligence ─────────────────────────────────────────────────────

    def _calibrate_score(self, raw_confidence: float, prediction_type: str) -> float:
        """Adjust confidence score based on prediction type and history."""
        # Type-based adjustment
        type_factors = {
            "general": 0.0,
            "technology": 0.05,
            "learning": 0.02,
            "project": -0.05,
            "deadline": -0.1,
            "burnout": -0.08,
        }
        adjustment = type_factors.get(prediction_type, 0)

        # Blend with historical baseline
        blended = (raw_confidence + self._confidence_baseline) / 2

        return min(0.99, max(0.1, blended + adjustment))

    def _compute_time_horizon(self, prediction_type: str, context: dict) -> str:
        """Estimate how far into the future the prediction applies."""
        horizons = {
            "general": "medium",
            "technology": "long",
            "learning": "medium",
            "project": "short",
            "deadline": "short",
            "burnout": "medium",
        }
        return horizons.get(prediction_type, "medium")

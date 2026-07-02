"""Reflection Agent — Self-analysis with pattern detection and influence scoring."""
import time
import json
from typing import Any
from collections import Counter


class ReflectionAgent:
    """Analyzes completed events and generates structured reflections with
    pattern recognition, influence scoring, and trend detection across
    multiple memory entries."""

    def __init__(self):
        self.name = "Reflection Agent"
        self._reflection_history: list[dict] = []
        self._max_history = 100

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def process(self, event: dict) -> dict:
        action = event.get("action", "reflect")

        handlers = {
            "reflect": self._reflect,
            "reflect_batch": self._reflect_batch,
            "trends": self._analyze_trends,
            "history": self._get_history,
            "insights": self._generate_insights,
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

    async def _reflect(self, event: dict) -> dict:
        from app.services.reflection_service import ReflectionService

        trigger = event.get("trigger", "unknown")
        context = event.get("context", {})
        memories = event.get("memories", [])

        service = ReflectionService()
        reflection = await service.generate_reflection(
            trigger_event=trigger,
            context={**context, "recent_memories": memories[:5]},
        )

        # Compute influence score
        influence = self._compute_influence(reflection)

        # Detect patterns
        patterns = self._detect_patterns(reflection, trigger)

        enriched = {
            **reflection,
            "trigger_event": trigger,
            "influence_score": influence,
            "patterns": patterns,
            "timestamp": time.time(),
        }

        self._reflection_history.append(enriched)
        if len(self._reflection_history) > self._max_history:
            self._reflection_history.pop(0)

        return {"reflection": enriched, "influence_score": influence, "patterns_found": len(patterns)}

    async def _reflect_batch(self, event: dict) -> dict:
        """Generate reflections for multiple events and aggregate patterns."""
        events = event.get("events", [])
        reflections = []
        all_patterns: dict[str, int] = {}

        for ev in events:
            try:
                r = await self._reflect({"trigger": ev.get("trigger"), "context": ev.get("context", {})})
                reflections.append(r.get("reflection", {}))
                for p in r.get("patterns", []):
                    pname = p.get("pattern", "")
                    all_patterns[pname] = all_patterns.get(pname, 0) + 1
            except Exception:
                continue

        top_patterns = sorted(all_patterns.items(), key=lambda x: -x[1])[:5]
        return {
            "reflections": reflections,
            "count": len(reflections),
            "aggregate_patterns": [{"pattern": p, "frequency": f} for p, f in top_patterns],
            "influence_avg": sum(r.get("influence_score", 0) for r in reflections) / max(len(reflections), 1),
        }

    async def _analyze_trends(self, event: dict) -> dict:
        """Analyze patterns across all stored reflections."""
        if not self._reflection_history:
            return {"trends": [], "message": "No reflection history available"}

        # Cluster by pattern
        pattern_clusters: dict[str, list[dict]] = {}
        for r in self._reflection_history:
            for p in r.get("patterns", []):
                pname = p.get("pattern", "unknown")
                if pname not in pattern_clusters:
                    pattern_clusters[pname] = []
                pattern_clusters[pname].append(r)

        trends = []
        for pattern, reflections in pattern_clusters.items():
            avg_influence = sum(r.get("influence_score", 0) for r in reflections) / len(reflections)
            trends.append({
                "pattern": pattern,
                "frequency": len(reflections),
                "avg_influence": round(avg_influence, 2),
                "first_seen": reflections[0].get("timestamp", 0),
                "last_seen": reflections[-1].get("timestamp", 0),
            })

        trends.sort(key=lambda t: -t["frequency"])
        return {"trends": trends[:10], "total_reflections": len(self._reflection_history)}

    async def _get_history(self, event: dict) -> dict:
        limit = event.get("limit", 20)
        return {"history": self._reflection_history[-limit:], "total": len(self._reflection_history)}

    async def _generate_insights(self, event: dict) -> dict:
        """Generate high-level insights from reflection history."""
        if not self._reflection_history:
            return {"insights": [], "message": "Not enough data for insights"}

        # Most common what_worked patterns
        what_worked = [r.get("what_worked", "") for r in self._reflection_history if r.get("what_worked")]
        what_failed = [r.get("what_failed", "") for r in self._reflection_history if r.get("what_failed")]

        top_worked = self._extract_common_phrases(what_worked, 3)
        top_failed = self._extract_common_phrases(what_failed, 3)

        avg_influence = sum(r.get("influence_score", 0) for r in self._reflection_history) / len(self._reflection_history)

        return {
            "insights": [
                {"category": "strengths", "items": top_worked},
                {"category": "weaknesses", "items": top_failed},
                {"category": "avg_influence", "value": round(avg_influence, 2)},
                {"category": "total_reflections", "value": len(self._reflection_history)},
            ],
        }

    # ── Intelligence ─────────────────────────────────────────────────────

    def _compute_influence(self, reflection: dict) -> float:
        """Score a reflection's potential influence from 0.0 to 1.0."""
        score = 0.5

        # Specificity signals
        for field in ["what_worked", "what_failed", "improvements"]:
            text = reflection.get(field, "")
            word_count = len(text.split())
            if word_count > 30:
                score += 0.1
            elif word_count > 10:
                score += 0.05

        # Pattern presence
        if reflection.get("patterns"):
            score += 0.15

        # Actionable improvements
        improvements = reflection.get("improvements", "")
        if len(improvements.split()) > 20:
            score += 0.1

        return min(1.0, max(0.0, score))

    def _detect_patterns(self, reflection: dict, trigger: str) -> list[dict]:
        """Detect recurring patterns in reflections."""
        patterns = []

        # Check for success patterns
        what_worked = (reflection.get("what_worked") or "").lower()
        if any(kw in what_worked for kw in ["automated", "template", "reusable", "modular", "scaffold"]):
            patterns.append({"pattern": "Reusable workflow creation", "category": "strength"})
        if any(kw in what_worked for kw in ["collaboration", "review", "feedback", "pair"]):
            patterns.append({"pattern": "Collaborative validation", "category": "strength"})
        if any(kw in what_worked for kw in ["documented", "documentation", "spec", "readme"]):
            patterns.append({"pattern": "Documentation-driven development", "category": "strength"})

        # Check for failure patterns
        what_failed = (reflection.get("what_failed") or "").lower()
        if any(kw in what_failed for kw in ["rushed", "deadline", "too fast", "skipped"]):
            patterns.append({"pattern": "Time pressure issues", "category": "risk"})
        if any(kw in what_failed for kw in ["scope creep", "overengineered", "too complex"]):
            patterns.append({"pattern": "Scope management", "category": "risk"})
        if any(kw in what_failed for kw in ["unclear", "ambiguous", "misunderstood"]):
            patterns.append({"pattern": "Communication gaps", "category": "risk"})

        return patterns

    def _extract_common_phrases(self, texts: list[str], top_n: int) -> list[str]:
        """Extract common meaningful phrases from a list of texts."""
        phrases = []
        for text in texts:
            words = text.split()
            for i in range(len(words) - 1):
                phrase = f"{words[i]} {words[i+1]}"
                if len(phrase) > 10:
                    phrases.append(phrase.lower())
        if not phrases:
            return ["(no common patterns yet)"]
        return [p for p, _ in Counter(phrases).most_common(top_n)]

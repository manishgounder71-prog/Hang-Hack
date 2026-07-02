"""Learning Agent — Skill detection, evolution tracking, and pattern analysis."""
import time
import math
from typing import Any
from collections import Counter


class LearningAgent:
    """Detects reusable skill patterns from memory, tracks skill evolution
    over time, and correlates skills across domains with confidence
    modeling."""

    def __init__(self):
        self.name = "Learning Agent"
        self._skill_history: dict[str, dict] = {}
        self._max_skills = 50
        self._detection_threshold = 3  # min pattern occurrences to create skill

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def process(self, event: dict) -> dict:
        action = event.get("action", "learn")

        handlers = {
            "detect_skill": self._detect_skill,
            "detect_all": self._detect_all_skills,
            "evolve_skill": self._evolve_skill,
            "evolve_all": self._evolve_all,
            "correlate": self._correlate_skills,
            "rank": self._rank_skills,
            "stats": self._get_stats,
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

    async def _detect_skill(self, event: dict) -> dict:
        """Detect a single skill pattern from a set of memories."""
        from app.services.skill_service import SkillService

        memories = event.get("memories", [])
        if len(memories) < self._detection_threshold:
            return {"skill": None, "message": f"Need at least {self._detection_threshold} memories to detect patterns"}

        service = SkillService()
        skill = await service.detect_skill_pattern(memories)

        if skill and skill.get("name"):
            # Add metadata
            skill["detected_at"] = time.time()
            skill["usage_count"] = 1
            skill["confidence_score"] = self._compute_initial_confidence(skill, len(memories))
            skill["id"] = f"skill_{skill['name'].lower().replace(' ', '_')}"

            self._skill_history[skill["id"]] = skill
            return {"skill": skill, "detected": True, "confidence": skill["confidence_score"]}

        return {"skill": None, "detected": False, "message": "No reusable pattern detected"}

    async def _detect_all_skills(self, event: dict) -> dict:
        """Scan all available memories and detect all possible skills."""
        from app.services.skill_service import SkillService

        memories = event.get("memories", [])
        user_id = event.get("user_id", "")
        service = SkillService()

        if len(memories) < self._detection_threshold:
            return {"skills": [], "total": 0, "message": "Insufficient data for skill detection"}

        # Cluster memories by topic for better pattern detection
        clusters = self._cluster_memories(memories)
        detected = []

        for cluster_id, cluster_mems in clusters.items():
            if len(cluster_mems) < self._detection_threshold:
                continue
            try:
                skill = await service.detect_skill_pattern(cluster_mems)
                if skill and skill.get("name"):
                    skill["id"] = f"skill_{skill['name'].lower().replace(' ', '_')}"
                    skill["detected_at"] = time.time()
                    skill["usage_count"] = len(cluster_mems)
                    skill["confidence_score"] = self._compute_initial_confidence(skill, len(cluster_mems))
                    skill["cluster_size"] = len(cluster_mems)
                    self._skill_history[skill["id"]] = skill
                    detected.append(skill)
            except Exception:
                continue

        return {
            "skills": detected,
            "total": len(detected),
            "clusters_analyzed": len(clusters),
            "user_id": user_id,
        }

    async def _evolve_skill(self, event: dict) -> dict:
        """Evolve an existing skill based on new usage data."""
        from app.services.skill_service import SkillService

        skill_id = event.get("skill_id", "")
        new_usage = event.get("usage", {})
        service = SkillService()

        existing = self._skill_history.get(skill_id)
        if not existing:
            return {"error": f"Skill {skill_id} not found", "evolved": False}

        evolution = await service.evolve_skill(skill_id=skill_id, new_usage=new_usage)

        # Update skill with evolution
        existing["usage_count"] = existing.get("usage_count", 1) + 1
        existing["last_evolved"] = time.time()

        # Boost confidence with each successful use
        confidence_boost = min(0.1, 1.0 - existing.get("confidence_score", 0.5)) * 0.2
        existing["confidence_score"] = min(1.0, existing.get("confidence_score", 0.5) + confidence_boost)

        if evolution.get("steps"):
            existing["steps"] = evolution["steps"]
        if evolution.get("best_practices"):
            existing["best_practices"] = evolution["best_practices"]

        return {
            "skill": existing,
            "evolution": evolution,
            "confidence": existing["confidence_score"],
            "evolved": True,
        }

    async def _evolve_all(self, event: dict) -> dict:
        """Evolve all skills simultaneously."""
        results = []
        for skill_id in list(self._skill_history.keys()):
            try:
                r = await self._evolve_skill({"skill_id": skill_id, "usage": event.get("usage", {})})
                results.append(r)
            except Exception:
                continue
        avg_confidence = sum(r.get("confidence", 0) for r in results) / max(len(results), 1)
        return {"evolved": len(results), "results": results, "avg_confidence": round(avg_confidence, 3)}

    async def _correlate_skills(self, event: dict) -> dict:
        """Find correlations between different skills."""
        if len(self._skill_history) < 2:
            return {"correlations": [], "message": "Need at least 2 skills for correlation"}

        skills = list(self._skill_history.values())
        correlations = []
        for i in range(len(skills)):
            for j in range(i + 1, len(skills)):
                score = self._compute_correlation(skills[i], skills[j])
                if score > 0.3:
                    correlations.append({
                        "skill_a": skills[i]["name"],
                        "skill_b": skills[j]["name"],
                        "correlation": round(score, 3),
                        "suggestion": f"Consider combining '{skills[i]['name']}' with '{skills[j]['name']}'"
                    })

        correlations.sort(key=lambda c: -c["correlation"])
        return {"correlations": correlations[:10], "total_pairs": len(correlations)}

    async def _rank_skills(self, event: dict) -> dict:
        """Rank skills by combined metrics."""
        if not self._skill_history:
            return {"ranked": [], "total": 0}

        ranked = sorted(
            self._skill_history.values(),
            key=lambda s: s.get("confidence_score", 0) * (1 + math.log(s.get("usage_count", 1) + 1)),
            reverse=True,
        )
        return {
            "ranked": [
                {
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "confidence": s.get("confidence_score"),
                    "usage_count": s.get("usage_count", 0),
                    "description": s.get("description", "")[:100],
                }
                for s in ranked[:20]
            ],
            "total": len(ranked),
        }

    async def _get_stats(self, event: dict) -> dict:
        if not self._skill_history:
            return {"total_skills": 0, "avg_confidence": 0, "total_uses": 0}

        confidences = [s.get("confidence_score", 0.5) for s in self._skill_history.values()]
        usages = [s.get("usage_count", 0) for s in self._skill_history.values()]
        return {
            "total_skills": len(self._skill_history),
            "avg_confidence": round(sum(confidences) / len(confidences), 3),
            "total_uses": sum(usages),
            "avg_uses": round(sum(usages) / len(usages), 1) if usages else 0,
            "top_skill": max(self._skill_history.values(), key=lambda s: s.get("confidence_score", 0)).get("name", ""),
        }

    # ── Intelligence ─────────────────────────────────────────────────────

    def _compute_initial_confidence(self, skill: dict, memory_count: int) -> float:
        """Calculate initial confidence for a newly detected skill."""
        confidence = 0.4  # baseline

        # Boost based on number of supporting memories
        confidence += min(0.3, memory_count * 0.05)

        # Boost if skill has multiple steps
        steps = skill.get("steps", [])
        if len(steps) >= 3:
            confidence += 0.15
        elif len(steps) >= 2:
            confidence += 0.1

        # Boost if skill has a clear description
        desc = skill.get("description", "")
        if len(desc) > 50:
            confidence += 0.1

        return min(1.0, max(0.1, confidence))

    def _cluster_memories(self, memories: list[dict]) -> dict[str, list[dict]]:
        """Simple content-based clustering of memories."""
        clusters: dict[str, list[dict]] = {}
        for mem in memories:
            tags = mem.get("tags", [])
            content = mem.get("content", "")
            # Use tags as cluster keys
            key = ",".join(sorted(tags)) if tags else content[:20]
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(mem)
        return clusters

    def _compute_correlation(self, skill_a: dict, skill_b: dict) -> float:
        """Compute correlation score between two skills."""
        # Shared keywords in descriptions
        desc_a = set((skill_a.get("description", "") + " " + " ".join(skill_a.get("steps", []))).lower().split())
        desc_b = set((skill_b.get("description", "") + " " + " ".join(skill_b.get("steps", []))).lower().split())
        shared = len(desc_a & desc_b) / max(len(desc_a | desc_b), 1)

        # Confidence proximity
        conf_a = skill_a.get("confidence_score", 0.5)
        conf_b = skill_b.get("confidence_score", 0.5)
        conf_proximity = 1.0 - abs(conf_a - conf_b)

        # Weighted combination
        return (shared * 0.6 + conf_proximity * 0.4)

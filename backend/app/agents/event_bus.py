import asyncio
from collections import defaultdict


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list] = defaultdict(list)
        self._history: list = []

    def subscribe(self, event_type: str, agent):
        self._subscribers[event_type].append(agent)

    async def publish(self, event_type: str, event: dict) -> list[dict]:
        results = []
        for agent in self._subscribers.get(event_type, []):
            try:
                result = await agent.process(event)
                results.append(result)
            except Exception as e:
                results.append({"agent": agent.name, "error": str(e)})
        self._history.append({"type": event_type, "event": event, "results": results})
        return results

    def get_history(self, limit: int = 50) -> list[dict]:
        return self._history[-limit:]


event_bus = EventBus()

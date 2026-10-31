import asyncio
import json
import logging
from typing import Dict, Any, Set

logger = logging.getLogger("crm.api.events_bus")


class EventBus:
    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=100)
        self._subscribers.add(q)
        logger.info(f"New SSE client subscribed. Total active listeners: {len(self._subscribers)}")
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._subscribers:
            self._subscribers.remove(q)
            logger.info(f"SSE client disconnected. Remaining listeners: {len(self._subscribers)}")

    async def broadcast(self, event_type: str, data: Any):
        payload = {
            "type": event_type,
            "data": data
        }
        msg = f"data: {json.dumps(payload, default=str)}\n\n"
        dead_subscribers = []
        for q in self._subscribers:
            try:
                if q.full():
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                q.put_nowait(msg)
            except Exception:
                dead_subscribers.append(q)

        for dead in dead_subscribers:
            self.unsubscribe(dead)


# Global singleton event bus
event_bus = EventBus()

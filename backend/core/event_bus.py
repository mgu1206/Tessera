import asyncio
from typing import AsyncGenerator


class EventBus:
    def __init__(self):
        self._queues: list[asyncio.Queue] = []

    async def publish(self, event_type: str, data: dict):
        for queue in self._queues:
            await queue.put({"type": event_type, "data": data})

    async def subscribe(self) -> AsyncGenerator[dict, None]:
        queue: asyncio.Queue = asyncio.Queue()
        self._queues.append(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            self._queues.remove(queue)


event_bus = EventBus()

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.core.event_bus import event_bus

router = APIRouter(prefix="/api", tags=["events"])


@router.get("/events")
async def sse():
    async def generate():
        async for event in event_bus.subscribe():
            data = json.dumps(event["data"], ensure_ascii=False)
            yield f"event: {event['type']}\ndata: {data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

import asyncio
import logging
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from src.api.events_bus import event_bus

logger = logging.getLogger("crm.api.stream")
router = APIRouter(prefix="/api/v1/stream", tags=["Live Event Streaming"])


@router.get("/events")
async def sse_stream(request: Request):
    queue = event_bus.subscribe()

    async def event_generator():
        try:
            # Send initial connected event
            yield f'data: {{"type": "connected", "data": {{"status": "ONLINE"}}}}\n\n'
            while True:
                if await request.is_disconnected():
                    break
                try:
                    # Wait up to 15 seconds for an event, then send keep-alive comment
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield msg
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

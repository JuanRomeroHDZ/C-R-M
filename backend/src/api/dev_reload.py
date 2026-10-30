import asyncio
import logging
import os
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("crm.api.dev_reload")
router = APIRouter(prefix="/api/v1/dev", tags=["Dev"])

connected_clients: Set[WebSocket] = set()


@router.websocket("/live-reload")
async def live_reload_ws(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"Live-reload client connected. Total clients: {len(connected_clients)}")
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info(f"Live-reload client disconnected. Total clients: {len(connected_clients)}")


async def broadcast_reload():
    if not connected_clients:
        return
    logger.info(f"Broadcasting reload signal to {len(connected_clients)} clients...")
    disconnected = set()
    for ws in list(connected_clients):
        try:
            await ws.send_text("reload")
        except Exception:
            disconnected.add(ws)
    for ws in disconnected:
        connected_clients.discard(ws)


@router.post("/trigger-reload")
async def trigger_reload():
    await broadcast_reload()
    return {"status": "BROADCASTED", "clients": len(connected_clients)}

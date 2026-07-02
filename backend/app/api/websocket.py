import json
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.memory import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        dead = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.add(connection)
        self.active_connections -= dead

    async def send_personal(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "ping")

                if msg_type == "ping":
                    await manager.send_personal({"type": "pong", "status": "connected"}, websocket)

                elif msg_type == "subscribe":
                    topic = msg.get("topic", "dashboard")
                    await manager.send_personal({
                        "type": "subscribed",
                        "topic": topic,
                    }, websocket)

                elif msg_type == "chat":
                    # Chat messages are handled via REST - this is just a notification channel
                    await manager.send_personal({
                        "type": "chat_ack",
                        "message": "Message received",
                    }, websocket)

            except json.JSONDecodeError:
                await manager.send_personal({
                    "type": "error",
                    "message": "Invalid JSON",
                }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.post("/ws/broadcast")
async def broadcast_event(event: dict):
    """Admin endpoint to broadcast events to all connected clients."""
    await manager.broadcast(event)
    return {"status": "broadcast", "connections": len(manager.active_connections)}


@router.get("/ws/status")
async def ws_status():
    return {"active_connections": len(manager.active_connections)}

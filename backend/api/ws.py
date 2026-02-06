from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self._dashboard_connections: Set[WebSocket] = set()
        self._room_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect_dashboard(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._dashboard_connections.add(websocket)
        logger.info(f"Dashboard client connected. Total: {len(self._dashboard_connections)}")

    async def connect_room(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        async with self._lock:
            if room_id not in self._room_connections:
                self._room_connections[room_id] = set()
            self._room_connections[room_id].add(websocket)
        logger.info(f"Room {room_id} client connected")

    async def disconnect_dashboard(self, websocket: WebSocket):
        async with self._lock:
            self._dashboard_connections.discard(websocket)
        logger.info(f"Dashboard client disconnected. Total: {len(self._dashboard_connections)}")

    async def disconnect_room(self, websocket: WebSocket, room_id: str):
        async with self._lock:
            if room_id in self._room_connections:
                self._room_connections[room_id].discard(websocket)
        logger.info(f"Room {room_id} client disconnected")

    async def broadcast_dashboard(self, data: dict):
        """Broadcast update to all dashboard clients."""
        if not self._dashboard_connections:
            return

        message = json.dumps(data)
        disconnected = set()

        for conn in self._dashboard_connections.copy():
            try:
                await conn.send_text(message)
            except Exception:
                disconnected.add(conn)

        async with self._lock:
            self._dashboard_connections -= disconnected

    async def broadcast_room(self, room_id: str, data: dict):
        """Broadcast update to clients watching specific room."""
        if room_id not in self._room_connections:
            return

        message = json.dumps(data)
        disconnected = set()

        for conn in self._room_connections[room_id].copy():
            try:
                await conn.send_text(message)
            except Exception:
                disconnected.add(conn)

        async with self._lock:
            if room_id in self._room_connections:
                self._room_connections[room_id] -= disconnected


manager = ConnectionManager()


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    """WebSocket for real-time dashboard updates."""
    await manager.connect_dashboard(websocket)
    try:
        while True:
            # Keep connection alive, handle pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect_dashboard(websocket)


@router.websocket("/ws/room/{room_id}")
async def room_websocket(websocket: WebSocket, room_id: str):
    """WebSocket for real-time room updates with preview."""
    await manager.connect_room(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect_room(websocket, room_id)


async def broadcast_count_update(
    room_id: str,
    count: int,
    raw_count: int,
    occupancy: float,
    frame_base64: str = None
):
    """Broadcast count update to dashboard and room clients."""
    from db.models import get_occupancy_status
    from datetime import datetime

    # Dashboard update (without frame)
    dashboard_data = {
        "type": "count_update",
        "room_id": room_id,
        "count": count,
        "raw_count": raw_count,
        "occupancy_percent": round(occupancy, 1),
        "status": get_occupancy_status(occupancy).value,
        "timestamp": datetime.utcnow().isoformat(),
    }
    await manager.broadcast_dashboard(dashboard_data)

    # Room update (with frame)
    room_data = {
        **dashboard_data,
        "frame": frame_base64,
    }
    await manager.broadcast_room(room_id, room_data)

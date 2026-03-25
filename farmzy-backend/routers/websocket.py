from __future__ import annotations

import json
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Tracks active websocket connections by farm."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, farm_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[farm_id].add(websocket)

    def disconnect(self, farm_id: str, websocket: WebSocket) -> None:
        if farm_id in self._connections:
            self._connections[farm_id].discard(websocket)
            if not self._connections[farm_id]:
                self._connections.pop(farm_id, None)

    async def broadcast(self, farm_id: str, payload: dict) -> None:
        dead_connections: list[WebSocket] = []
        for socket in list(self._connections.get(farm_id, set())):
            try:
                await socket.send_text(json.dumps(payload, default=str))
            except Exception:
                dead_connections.append(socket)

        for socket in dead_connections:
            self.disconnect(farm_id, socket)


connection_manager = ConnectionManager()


@router.websocket("/ws/farm/{farm_id}")
async def farm_socket(websocket: WebSocket, farm_id: str) -> None:
    await connection_manager.connect(farm_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(farm_id, websocket)
    except Exception:
        connection_manager.disconnect(farm_id, websocket)

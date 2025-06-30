from fastapi import WebSocket
from typing import List
import asyncio
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
            logger.info(f"Nueva conexión: {id(websocket)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                logger.info(f"Conexión cerrada: {id(websocket)}")

    async def broadcast(self, data: dict):
        dead_connections = []
        async with self._lock:
            for connection in self.active_connections:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    logger.error(f"Error en broadcast: {str(e)}")
                    dead_connections.append(connection)
            
            for conn in dead_connections:
                await self.disconnect(conn)

manager = ConnectionManager()
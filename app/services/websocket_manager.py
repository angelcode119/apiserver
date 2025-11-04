from fastapi import WebSocket
from typing import Dict, Optional

import json
from datetime import datetime

class ConnectionManager:

    def __init__(self):

        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, device_id: str, websocket: WebSocket):

        if device_id in self.active_connections:
            try:
                old_ws = self.active_connections[device_id]
                await old_ws.close()

            except:
                pass

        self.active_connections[device_id] = websocket

    def disconnect(self, device_id: str):
        if device_id in self.active_connections:
            del self.active_connections[device_id]

    def is_connected(self, device_id: str) -> bool:
        return device_id in self.active_connections

    async def send_message(self, device_id: str, message: dict) -> bool:
        if device_id not in self.active_connections:

            return False

        try:
            websocket = self.active_connections[device_id]
            await websocket.send_json(message)

            return True
        except Exception as e:

            self.disconnect(device_id)
            return False

    async def send_pong(self, device_id: str, timestamp: int):
        return await self.send_message(device_id, {
            "type": "pong",
            "timestamp": timestamp
        })

    async def send_registered(self, device_id: str):
        return await self.send_message(device_id, {
            "type": "registered",
            "device_id": device_id,
            "message": "Device registered successfully"
        })

    async def send_command(self, device_id: str, command: str, parameters: Optional[dict] = None):
        message = {
            "type": "command",
            "command": command
        }

        if parameters:
            message["parameters"] = parameters

        return await self.send_message(device_id, message)

    async def broadcast(self, message: dict):
        disconnected = []

        for device_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except:
                disconnected.append(device_id)

        for device_id in disconnected:
            self.disconnect(device_id)

    def get_connected_devices(self) -> list:
        return list(self.active_connections.keys())

    def get_connection_count(self) -> int:
        return len(self.active_connections)

manager = ConnectionManager()
# fastapi_photo_app/notifier.py
import asyncio
from typing import List
from fastapi import WebSocket, WebSocketDisconnect

active_connections: List[WebSocket] = []

async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text() 
    except WebSocketDisconnect:
        active_connections.remove(websocket)

def notify_clients(message: str):
    for conn in active_connections:
        asyncio.create_task(conn.send_text(message))

from typing import Dict, List, Any
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger("vora.websocket")

class ConnectionManager:
    """Gestionnaire de connexions WebSocket temps réel pour Flutter et dispatch VORA"""
    
    def __init__(self):
        # Connexions abonnées à une course spécifique (ex: ride_id -> [ws1, ws2])
        self.ride_channels: Dict[int, List[WebSocket]] = {}
        # Connexions globales (ex: chauffeurs en attente, dispatch)
        self.global_broadcast: List[WebSocket] = []

    async def connect_ride(self, ride_id: int, websocket: WebSocket):
        await websocket.accept()
        if ride_id not in self.ride_channels:
            self.ride_channels[ride_id] = []
        self.ride_channels[ride_id].append(websocket)
        logger.info(f"WebSocket client connected to ride #{ride_id}")

    def disconnect_ride(self, ride_id: int, websocket: WebSocket):
        if ride_id in self.ride_channels:
            if websocket in self.ride_channels[ride_id]:
                self.ride_channels[ride_id].remove(websocket)
            if not self.ride_channels[ride_id]:
                del self.ride_channels[ride_id]
        logger.info(f"WebSocket client disconnected from ride #{ride_id}")

    async def broadcast_to_ride(self, ride_id: int, event_type: str, data: Any):
        """Envoie un événement temps réel à tous les participants d'une course (passager, chauffeur)"""
        if ride_id in self.ride_channels:
            payload = json.dumps({"event": event_type, "data": data})
            dead_connections = []
            for ws in self.ride_channels[ride_id]:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead_connections.append(ws)
            for dead_ws in dead_connections:
                self.disconnect_ride(ride_id, dead_ws)

    async def connect_global(self, websocket: WebSocket):
        await websocket.accept()
        self.global_broadcast.append(websocket)

    def disconnect_global(self, websocket: WebSocket):
        if websocket in self.global_broadcast:
            self.global_broadcast.remove(websocket)

    async def broadcast_global(self, event_type: str, data: Any):
        """Diffusion globale (ex: nouvelle course disponible pour les chauffeurs à proximité)"""
        payload = json.dumps({"event": event_type, "data": data})
        dead_connections = []
        for ws in self.global_broadcast:
            try:
                await ws.send_text(payload)
            except Exception:
                dead_connections.append(ws)
        for dead_ws in dead_connections:
            self.disconnect_global(dead_ws)

manager = ConnectionManager()

from fastapi import WebSocket
from typing import List, Dict, Any
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_data: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_data[websocket] = {
            "connected_at": asyncio.get_event_loop().time(),
            "player_id": None,
            "last_activity": asyncio.get_event_loop().time()
        }
        logger.info(f"New WebSocket connection established. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if websocket in self.connection_data:
            player_id = self.connection_data[websocket].get("player_id")
            if player_id:
                logger.info(f"Player {player_id} disconnected")
            del self.connection_data[websocket]
        
        logger.info(f"WebSocket connection closed. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
            self._update_activity(websocket)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            await self._handle_connection_error(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Send a message to all connected WebSocket clients"""
        disconnected = []
        
        for websocket in self.active_connections:
            try:
                await websocket.send_text(json.dumps(message))
                self._update_activity(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast_game_update(self, game_state: Dict[str, Any]):
        """Broadcast game state update to all connected clients"""
        message = {
            "type": "game_update",
            "data": game_state,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(message)

    async def broadcast_pose_detection(self, pose_data: Dict[str, Any]):
        """Broadcast pose detection results"""
        message = {
            "type": "pose_detection",
            "data": pose_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(message)

    async def send_game_action(self, player_id: str, action: Dict[str, Any], websocket: WebSocket):
        """Send game action to a specific player"""
        message = {
            "type": "game_action",
            "player_id": player_id,
            "data": action,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_personal_message(message, websocket)

    def register_player(self, websocket: WebSocket, player_id: str, player_name: str):
        """Register a player with a WebSocket connection"""
        if websocket in self.connection_data:
            self.connection_data[websocket]["player_id"] = player_id
            self.connection_data[websocket]["player_name"] = player_name
            logger.info(f"Player {player_name} (ID: {player_id}) registered with WebSocket")

    def get_player_info(self, websocket: WebSocket) -> Dict[str, Any]:
        """Get player information for a WebSocket connection"""
        return self.connection_data.get(websocket, {})

    def get_connected_players(self) -> List[Dict[str, Any]]:
        """Get list of all connected players"""
        players = []
        for websocket, data in self.connection_data.items():
            if data.get("player_id"):
                players.append({
                    "player_id": data["player_id"],
                    "player_name": data.get("player_name", "Unknown"),
                    "connected_at": data["connected_at"],
                    "last_activity": data["last_activity"]
                })
        return players

    def _update_activity(self, websocket: WebSocket):
        """Update last activity time for a connection"""
        if websocket in self.connection_data:
            self.connection_data[websocket]["last_activity"] = asyncio.get_event_loop().time()

    async def _handle_connection_error(self, websocket: WebSocket):
        """Handle WebSocket connection errors"""
        logger.warning("WebSocket connection error detected")
        self.disconnect(websocket)

    async def cleanup_inactive_connections(self, timeout_seconds: int = 300):
        """Clean up inactive connections"""
        current_time = asyncio.get_event_loop().time()
        inactive_connections = []
        
        for websocket, data in self.connection_data.items():
            if current_time - data["last_activity"] > timeout_seconds:
                inactive_connections.append(websocket)
        
        for websocket in inactive_connections:
            logger.info("Cleaning up inactive WebSocket connection")
            self.disconnect(websocket)

    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)

    async def ping_all(self):
        """Send ping to all connections to check if they're still alive"""
        message = {"type": "ping", "timestamp": asyncio.get_event_loop().time()}
        await self.broadcast(message) 
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import asyncio
from typing import List, Dict, Any
import logging

from pose_detection import PoseDetector
from game_logic import BoxingGame
from websocket_manager import ConnectionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Boxing AI Game API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
pose_detector = PoseDetector()
game_logic = BoxingGame()
manager = ConnectionManager()

# Pydantic models
class PoseData(BaseModel):
    keypoints: List[Dict[str, float]]
    timestamp: float

class GameAction(BaseModel):
    action_type: str
    player_id: str
    data: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Boxing AI Game API...")
    await pose_detector.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Boxing AI Game API...")
    await pose_detector.cleanup()

@app.get("/")
async def root():
    return {"message": "Boxing AI Game API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "pose_detector": pose_detector.is_ready()}

@app.post("/pose/detect")
async def detect_pose(pose_data: PoseData):
    """Process pose data and return boxing actions"""
    try:
        # Process pose data
        actions = await pose_detector.process_pose(pose_data.keypoints)
        
        # Update game logic
        game_update = await game_logic.process_actions(actions)
        
        return {
            "actions": actions,
            "game_state": game_update,
            "timestamp": pose_data.timestamp
        }
    except Exception as e:
        logger.error(f"Error processing pose data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/game/status")
async def get_game_status():
    """Get current game status"""
    return {
        "game_state": game_logic.get_state(),
        "players": game_logic.get_players(),
        "score": game_logic.get_score()
    }

@app.post("/game/reset")
async def reset_game():
    """Reset the game state"""
    game_logic.reset()
    return {"message": "Game reset successfully"}

@app.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time game communication"""
    await manager.connect(websocket)
    try:
        while True:
            # Receive data from Unity
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process the message
            response = await process_websocket_message(message)
            
            # Send response back to Unity
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def process_websocket_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """Process incoming WebSocket messages"""
    message_type = message.get("type")
    
    if message_type == "pose_data":
        # Process pose data from Unity
        pose_data = message.get("data", {})
        actions = await pose_detector.process_pose(pose_data.get("keypoints", []))
        game_update = await game_logic.process_actions(actions)
        
        return {
            "type": "game_update",
            "data": {
                "actions": actions,
                "game_state": game_update
            }
        }
    
    elif message_type == "game_action":
        # Process game actions from Unity
        action = message.get("data", {})
        game_update = await game_logic.process_actions([action])
        
        return {
            "type": "game_update",
            "data": game_update
        }
    
    elif message_type == "ping":
        return {"type": "pong"}
    
    else:
        return {"type": "error", "message": "Unknown message type"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
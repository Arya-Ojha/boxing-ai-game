# Boxing AI Game

A real-time boxing game that uses pose detection with MediaPipe MoveNet, FastAPI backend, and Unity frontend.

## Project Structure

```
boxing-ai-game/
├── backend/                 # FastAPI backend with pose detection
├── unity-game/             # Unity frontend game
├── pose-detection/         # MoveNet pose detection module
├── docs/                   # Documentation
└── scripts/               # Utility scripts
```

## Features

- Real-time pose detection using MediaPipe MoveNet
- FastAPI backend for pose processing and game logic
- Unity frontend for 3D boxing game
- WebSocket communication between components
- Gesture recognition for boxing moves

## Setup Instructions

### Backend Setup

1. Navigate to `backend/`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `uvicorn main:app --reload`

### Unity Setup

1. Open Unity Hub
2. Open the `unity-game/` folder as a Unity project
3. Install required packages (see Unity setup guide)

### Pose Detection Setup

1. Navigate to `pose-detection/`
2. Install dependencies: `pip install -r requirements.txt`
3. Test pose detection: `python test_pose_detection.py`

## Development

- Backend runs on `http://localhost:8000`
- Unity game connects via WebSocket
- Pose detection processes camera feed in real-time

## API Endpoints

- `POST /pose/detect` - Process pose data
- `GET /game/status` - Get current game status
- `WebSocket /ws/game` - Real-time game communication

# Boxing AI Game - Unity Frontend

This is the Unity frontend for the Boxing AI Game that connects to the FastAPI backend for real-time pose detection and game logic.

## Project Structure

```
unity-game/
├── Assets/
│   ├── Scripts/           # C# scripts for game logic
│   ├── Prefabs/          # Game objects and UI elements
│   ├── Scenes/           # Unity scenes
│   ├── Materials/         # Materials and textures
│   ├── Animations/        # Character animations
│   └── Audio/            # Sound effects and music
├── Packages/              # Unity packages
└── ProjectSettings/       # Unity project settings
```

## Features

- Real-time WebSocket communication with FastAPI backend
- 3D boxing arena with character models
- Pose detection integration
- Boxing move animations
- Health and score tracking
- Multiplayer support (local)

## Setup Instructions

### Prerequisites

- Unity 2022.3 LTS or later
- .NET 6.0 or later

### Installation

1. Open Unity Hub
2. Click "Open" and select the `unity-game/` folder
3. Wait for Unity to import the project
4. Install required packages (see below)

### Required Unity Packages

- WebSocket Sharp (for WebSocket communication)
- TextMeshPro (for UI text)
- Input System (for input handling)
- Cinemachine (for camera control)

### Configuration

1. Open `Assets/Scripts/GameManager.cs`
2. Update the WebSocket URL to match your backend:
   ```csharp
   private string websocketUrl = "ws://localhost:8000/ws/game";
   ```

## Game Controls

- **Pose Detection**: Stand in front of camera and perform boxing moves
- **Jab**: Extend left arm forward
- **Cross**: Extend right arm forward
- **Hook**: Swing arm horizontally
- **Uppercut**: Swing arm upward
- **Block**: Raise arms in front of face
- **Dodge**: Move side to side
- **Guard**: Keep arms in defensive position

## Development

### Running the Game

1. Start the FastAPI backend: `cd backend && uvicorn main:app --reload`
2. Start pose detection: `cd pose-detection && python pose_detector.py`
3. Open Unity and run the game scene

### Building

1. File → Build Settings
2. Select target platform (Windows, macOS, Linux)
3. Click "Build"

## Scripts Overview

- `GameManager.cs`: Main game logic and WebSocket communication
- `PoseDetector.cs`: Handles pose data from backend
- `BoxingCharacter.cs`: Character controller and animations
- `UIManager.cs`: UI updates and score display
- `WebSocketClient.cs`: WebSocket communication with backend

## Troubleshooting

### WebSocket Connection Issues

- Ensure backend is running on correct port
- Check firewall settings
- Verify WebSocket URL in GameManager

### Pose Detection Issues

- Ensure camera is properly connected
- Check lighting conditions
- Verify pose detection module is running

### Performance Issues

- Reduce graphics quality in Unity settings
- Lower camera resolution in pose detection
- Close unnecessary applications

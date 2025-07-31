# Boxing AI Game - Quick Start Guide

This guide will help you get the Boxing AI Game up and running in minutes.

## Prerequisites

- **Python 3.8+** - [Download here](https://www.python.org/downloads/)
- **Unity 2022.3 LTS+** - [Download here](https://unity.com/download)
- **Webcam** - For pose detection
- **Git** - For cloning the repository

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd boxing-ai-game
```

### 2. Run Setup Script

```bash
python scripts/setup.py
```

This will:

- Install all Python dependencies
- Create necessary directories
- Set up configuration files
- Run basic tests

### 3. Start the Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 4. Start Pose Detection

In a new terminal:

```bash
cd pose-detection
python pose_detector.py
```

This will start the camera and begin pose detection.

### 5. Open Unity Project

1. Open Unity Hub
2. Click "Open" and select the `unity-game/` folder
3. Wait for Unity to import the project
4. Open the main game scene

## Testing the Setup

### Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Game status
curl http://localhost:8000/game/status
```

### Test Pose Detection

1. Stand in front of your camera
2. Perform boxing moves:

   - **Jab**: Extend left arm forward
   - **Cross**: Extend right arm forward
   - **Hook**: Swing arm horizontally
   - **Block**: Raise arms in front of face

3. Check the console output for detected moves

### Test Unity Connection

1. Open Unity and run the game
2. Check the console for WebSocket connection status
3. Perform moves and watch the character animations

## Game Controls

### Pose-Based Controls

- **Jab**: Extend left arm forward
- **Cross**: Extend right arm forward
- **Hook**: Swing arm horizontally
- **Uppercut**: Swing arm upward
- **Block**: Raise arms in front of face
- **Dodge**: Move side to side
- **Guard**: Keep arms in defensive position

### Unity UI Controls

- **Start Game**: Begin a new match
- **Pause Game**: Pause the current match
- **Reset Game**: Reset to initial state

## Troubleshooting

### Common Issues

#### 1. Camera Not Found

**Error**: `Could not open camera 0`

**Solution**:

- Check if webcam is connected
- Try different camera ID in `pose-detection/pose_detector.py`
- On Windows, try camera ID 1 or 2

#### 2. WebSocket Connection Failed

**Error**: `Failed to connect to WebSocket`

**Solution**:

- Ensure backend is running on port 8000
- Check firewall settings
- Verify WebSocket URL in Unity GameManager

#### 3. Pose Detection Not Working

**Error**: No moves detected

**Solution**:

- Ensure good lighting
- Stand 2-3 meters from camera
- Make sure full body is visible
- Check camera permissions

#### 4. Unity Build Errors

**Error**: Missing dependencies

**Solution**:

- Install required Unity packages:
  - WebSocket Sharp
  - TextMeshPro
  - Input System
  - Cinemachine

#### 5. Performance Issues

**Symptoms**: Low frame rate, lag

**Solutions**:

- Reduce camera resolution in pose detection
- Lower graphics quality in Unity
- Close unnecessary applications
- Use a dedicated GPU if available

### Debug Mode

Enable debug logging:

```bash
# Backend debug
cd backend
uvicorn main:app --reload --log-level debug

# Pose detection debug
cd pose-detection
python pose_detector.py --debug
```

### Testing Individual Components

#### Test Backend Only

```bash
cd backend
python -c "from main import app; print('Backend imports successful')"
```

#### Test Pose Detection Only

```bash
cd pose-detection
python test_pose_detection.py
```

#### Test Unity Scripts

1. Open Unity
2. Open Console window
3. Check for any script compilation errors

## Configuration

### Backend Configuration

Edit `backend/config.ini`:

```ini
[server]
host = "0.0.0.0"
port = 8000
debug = true

[pose_detection]
camera_id = 0
confidence_threshold = 0.5
frame_rate = 30
```

### Pose Detection Configuration

Edit `pose-detection/config.ini`:

```ini
[camera]
device_id = 0
width = 640
height = 480
fps = 30

[detection]
confidence_threshold = 0.5
model_complexity = 2
```

### Unity Configuration

Edit `unity-game/Assets/Scripts/GameManager.cs`:

```csharp
public string websocketUrl = "ws://localhost:8000/ws/game";
```

## Development Workflow

### 1. Backend Development

```bash
cd backend
uvicorn main:app --reload
```

- Edit Python files in `backend/`
- API changes are auto-reloaded
- Check logs for errors

### 2. Pose Detection Development

```bash
cd pose-detection
python pose_detector.py
```

- Edit detection logic in `pose_detector.py`
- Test with `test_pose_detection.py`
- Adjust thresholds in config

### 3. Unity Development

1. Open Unity project
2. Edit C# scripts in `Assets/Scripts/`
3. Test in Play mode
4. Build for target platform

## Performance Optimization

### Backend Optimization

- Use `uvicorn` with multiple workers
- Enable async processing
- Monitor memory usage

### Pose Detection Optimization

- Reduce camera resolution
- Lower frame rate
- Use GPU acceleration if available

### Unity Optimization

- Use object pooling
- Optimize animations
- Reduce draw calls
- Use LOD (Level of Detail)

## Deployment

### Backend Deployment

```bash
# Production server
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Unity Build

1. File → Build Settings
2. Select target platform
3. Click "Build"
4. Deploy executable

## Support

### Getting Help

1. Check the troubleshooting section above
2. Review API documentation
3. Check Unity console for errors
4. Verify all components are running

### Logs

- Backend logs: Check terminal output
- Pose detection logs: Check terminal output
- Unity logs: Window → General → Console

### Common Commands

```bash
# Start all services
python scripts/setup.py
cd backend && uvicorn main:app --reload &
cd pose-detection && python pose_detector.py &

# Stop all services
pkill -f uvicorn
pkill -f pose_detector

# Check status
curl http://localhost:8000/health
```

## Next Steps

1. **Customize the game**: Modify game logic in `backend/game_logic.py`
2. **Add new moves**: Extend pose detection in `backend/pose_detection.py`
3. **Improve UI**: Enhance Unity interface
4. **Add multiplayer**: Implement multiple player support
5. **Deploy online**: Set up cloud hosting

Happy boxing! 🥊

# Boxing AI Game API Documentation

## Overview

The Boxing AI Game API is built with FastAPI and provides real-time pose detection, game logic, and WebSocket communication for the Unity frontend.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. All endpoints are publicly accessible.

## API Endpoints

### Health Check

#### GET /health

Check if the API is running and pose detector is ready.

**Response:**

```json
{
	"status": "healthy",
	"pose_detector": true
}
```

### Game Status

#### GET /game/status

Get current game state and player information.

**Response:**

```json
{
	"game_state": {
		"state": "waiting",
		"current_round": 1,
		"max_rounds": 3,
		"round_time": 180,
		"players": [
			{
				"id": "player1",
				"name": "Player 1",
				"health": 100,
				"score": 0,
				"last_move": "jab",
				"last_move_time": 1640995200.0,
				"is_blocking": false,
				"is_dodging": false
			}
		],
		"game_start_time": null,
		"last_update_time": null
	},
	"players": [
		{
			"id": "player1",
			"name": "Player 1",
			"health": 100,
			"score": 0,
			"last_move": null,
			"last_move_time": null,
			"is_blocking": false,
			"is_dodging": false
		}
	],
	"score": {
		"player1": 0
	}
}
```

### Game Control

#### POST /game/reset

Reset the game to initial state.

**Response:**

```json
{
	"message": "Game reset successfully"
}
```

### Pose Detection

#### POST /pose/detect

Process pose data and return boxing actions.

**Request Body:**

```json
{
	"keypoints": [
		{
			"index": 0,
			"x": 0.5,
			"y": 0.3,
			"z": 0.0,
			"confidence": 0.9
		}
	],
	"timestamp": 1640995200.0
}
```

**Response:**

```json
{
  "actions": [
    {
      "move": "jab",
      "confidence": 0.85,
      "timestamp": 1640995200.0
    }
  ],
  "game_state": {
    "state": "playing",
    "current_round": 1,
    "max_rounds": 3,
    "round_time": 180,
    "players": [...],
    "game_start_time": 1640995200.0,
    "last_update_time": 1640995200.0
  },
  "timestamp": 1640995200.0
}
```

## WebSocket API

### WebSocket Endpoint

#### WebSocket /ws/game

Real-time communication endpoint for game updates and pose detection.

**Connection URL:**

```
ws://localhost:8000/ws/game
```

### WebSocket Message Types

#### 1. Pose Data

**From Unity to Backend:**

```json
{
  "type": "pose_data",
  "data": {
    "keypoints": [...],
    "moves": [
      {
        "move": "jab",
        "confidence": 0.85,
        "timestamp": 1640995200.0
      }
    ],
    "timestamp": 1640995200.0
  }
}
```

#### 2. Game Action

**From Unity to Backend:**

```json
{
	"type": "game_action",
	"data": {
		"action_type": "start_game",
		"player_id": "player1",
		"data": {}
	}
}
```

#### 3. Game Update

**From Backend to Unity:**

```json
{
  "type": "game_update",
  "data": {
    "state": "playing",
    "current_round": 1,
    "max_rounds": 3,
    "round_time": 180,
    "players": [...],
    "game_start_time": 1640995200.0,
    "last_update_time": 1640995200.0
  },
  "timestamp": 1640995200.0
}
```

#### 4. Pose Detection

**From Backend to Unity:**

```json
{
  "type": "pose_detection",
  "data": {
    "keypoints": [...],
    "moves": [
      {
        "move": "jab",
        "confidence": 0.85,
        "timestamp": 1640995200.0
      }
    ],
    "timestamp": 1640995200.0
  },
  "timestamp": 1640995200.0
}
```

#### 5. Ping/Pong

**From Unity to Backend:**

```json
{
	"type": "ping",
	"timestamp": 1640995200.0
}
```

**From Backend to Unity:**

```json
{
	"type": "pong",
	"timestamp": 1640995200.0
}
```

## Boxing Moves

The API recognizes the following boxing moves:

### Offensive Moves

1. **Jab** - Straight punch with lead hand

   - Arm extended forward
   - Wrist in front of shoulder
   - Confidence threshold: 0.7

2. **Cross** - Straight punch with rear hand

   - Arm extended forward
   - Wrist in front of shoulder
   - Confidence threshold: 0.7

3. **Hook** - Horizontal punch

   - Arm swung horizontally
   - Wrist at shoulder level or higher
   - Confidence threshold: 0.6

4. **Uppercut** - Upward punch
   - Arm swung upward
   - Wrist above shoulder level
   - Confidence threshold: 0.6

### Defensive Moves

5. **Block** - Defensive guard

   - Arms raised in front of face
   - Wrists close to shoulders
   - Confidence threshold: 0.5

6. **Dodge** - Lateral movement

   - Side-to-side movement
   - Shoulder or hip movement detected
   - Confidence threshold: 0.5

7. **Guard** - Defensive position
   - Arms in defensive stance
   - Wrists near elbows
   - Confidence threshold: 0.5

## Game States

1. **waiting** - Game not started, waiting for players
2. **playing** - Game in progress
3. **paused** - Game paused
4. **finished** - Game completed

## Error Responses

### 400 Bad Request

```json
{
	"detail": "Invalid pose data format"
}
```

### 500 Internal Server Error

```json
{
	"detail": "Error processing pose data"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## CORS

CORS is enabled for all origins. Configure appropriately for production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## WebSocket Connection Management

The API automatically manages WebSocket connections:

- Connections are tracked in memory
- Inactive connections are cleaned up after 5 minutes
- Connection status is logged
- Automatic reconnection handling

## Testing

### Test with curl

```bash
# Health check
curl http://localhost:8000/health

# Game status
curl http://localhost:8000/game/status

# Reset game
curl -X POST http://localhost:8000/game/reset
```

### Test WebSocket with wscat

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws/game

# Send pose data
{"type": "pose_data", "data": {"keypoints": [], "moves": [], "timestamp": 1640995200.0}}
```

## Performance Considerations

- Pose detection runs at ~30 FPS
- WebSocket messages are sent asynchronously
- Game state updates are batched
- Memory usage is monitored and logged

## Security Considerations

- Input validation on all endpoints
- Error messages don't expose internal details
- WebSocket connections are validated
- Consider adding authentication for production

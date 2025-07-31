using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using System.Collections.Generic;
using System;
using Newtonsoft.Json;

[System.Serializable]
public class PoseData
{
    public List<Keypoint> keypoints;
    public List<Move> moves;
    public double timestamp;
}

[System.Serializable]
public class Keypoint
{
    public int index;
    public float x;
    public float y;
    public float z;
    public float confidence;
}

[System.Serializable]
public class Move
{
    public string move;
    public float confidence;
    public double timestamp;
}

[System.Serializable]
public class GameState
{
    public string state;
    public int current_round;
    public int max_rounds;
    public int round_time;
    public List<Player> players;
    public double? game_start_time;
    public double? last_update_time;
}

[System.Serializable]
public class Player
{
    public string id;
    public string name;
    public int health;
    public int score;
    public string last_move;
    public double? last_move_time;
    public bool is_blocking;
    public bool is_dodging;
}

[System.Serializable]
public class WebSocketMessage
{
    public string type;
    public object data;
    public double timestamp;
}

public class GameManager : MonoBehaviour
{
    [Header("WebSocket Settings")]
    public string websocketUrl = "ws://localhost:8000/ws/game";
    
    [Header("Game Settings")]
    public int maxHealth = 100;
    public float roundDuration = 180f; // 3 minutes
    
    [Header("UI References")]
    public Text healthText;
    public Text scoreText;
    public Text roundText;
    public Text gameStateText;
    public Button startGameButton;
    public Button pauseGameButton;
    
    [Header("Character References")]
    public BoxingCharacter playerCharacter;
    public BoxingCharacter opponentCharacter;
    
    // WebSocket client
    private WebSocketClient webSocketClient;
    
    // Game state
    private GameState currentGameState;
    private Player currentPlayer;
    private bool isConnected = false;
    
    // Pose detection
    private PoseData lastPoseData;
    private List<Move> detectedMoves = new List<Move>();
    
    // Events
    public static event Action<Move> OnMoveDetected;
    public static event Action<GameState> OnGameStateChanged;
    public static event Action<bool> OnConnectionChanged;

    void Start()
    {
        InitializeGame();
        ConnectToBackend();
    }

    void Update()
    {
        // Handle pose data updates
        if (lastPoseData != null && lastPoseData.moves != null)
        {
            ProcessDetectedMoves(lastPoseData.moves);
        }
        
        // Update UI
        UpdateUI();
    }

    void OnDestroy()
    {
        DisconnectFromBackend();
    }

    private void InitializeGame()
    {
        // Initialize UI
        if (startGameButton != null)
            startGameButton.onClick.AddListener(StartGame);
        
        if (pauseGameButton != null)
            pauseGameButton.onClick.AddListener(PauseGame);
        
        // Initialize game state
        currentGameState = new GameState
        {
            state = "waiting",
            current_round = 1,
            max_rounds = 3,
            round_time = 180,
            players = new List<Player>()
        };
        
        UpdateUI();
    }

    private async void ConnectToBackend()
    {
        try
        {
            webSocketClient = new WebSocketClient(websocketUrl);
            webSocketClient.OnMessageReceived += HandleWebSocketMessage;
            webSocketClient.OnConnectionChanged += HandleConnectionChanged;
            
            await webSocketClient.Connect();
            Debug.Log("Connected to backend");
            
            // Register player
            await RegisterPlayer("player1", "Player 1");
            
        }
        catch (Exception e)
        {
            Debug.LogError($"Failed to connect to backend: {e.Message}");
        }
    }

    private void DisconnectFromBackend()
    {
        if (webSocketClient != null)
        {
            webSocketClient.Disconnect();
            webSocketClient = null;
        }
    }

    private void HandleWebSocketMessage(string message)
    {
        try
        {
            var wsMessage = JsonConvert.DeserializeObject<WebSocketMessage>(message);
            
            switch (wsMessage.type)
            {
                case "game_update":
                    HandleGameUpdate(wsMessage.data);
                    break;
                    
                case "pose_detection":
                    HandlePoseDetection(wsMessage.data);
                    break;
                    
                case "pong":
                    Debug.Log("Received pong from server");
                    break;
                    
                default:
                    Debug.LogWarning($"Unknown message type: {wsMessage.type}");
                    break;
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"Error handling WebSocket message: {e.Message}");
        }
    }

    private void HandleGameUpdate(object data)
    {
        try
        {
            var gameStateJson = JsonConvert.SerializeObject(data);
            currentGameState = JsonConvert.DeserializeObject<GameState>(gameStateJson);
            
            // Update player reference
            if (currentGameState.players != null)
            {
                currentPlayer = currentGameState.players.Find(p => p.id == "player1");
            }
            
            // Trigger game state change event
            OnGameStateChanged?.Invoke(currentGameState);
            
            // Update character animations
            UpdateCharacterAnimations();
            
            Debug.Log($"Game state updated: {currentGameState.state}");
        }
        catch (Exception e)
        {
            Debug.LogError($"Error handling game update: {e.Message}");
        }
    }

    private void HandlePoseDetection(object data)
    {
        try
        {
            var poseDataJson = JsonConvert.SerializeObject(data);
            lastPoseData = JsonConvert.DeserializeObject<PoseData>(poseDataJson);
            
            Debug.Log($"Received pose data with {lastPoseData.moves?.Count ?? 0} moves");
        }
        catch (Exception e)
        {
            Debug.LogError($"Error handling pose detection: {e.Message}");
        }
    }

    private void HandleConnectionChanged(bool connected)
    {
        isConnected = connected;
        OnConnectionChanged?.Invoke(connected);
        
        Debug.Log($"Connection changed: {connected}");
    }

    private async void RegisterPlayer(string playerId, string playerName)
    {
        if (webSocketClient != null && webSocketClient.IsConnected)
        {
            var message = new
            {
                type = "register_player",
                data = new
                {
                    player_id = playerId,
                    player_name = playerName
                }
            };
            
            await webSocketClient.SendMessage(JsonConvert.SerializeObject(message));
        }
    }

    private async void StartGame()
    {
        if (webSocketClient != null && webSocketClient.IsConnected)
        {
            var message = new
            {
                type = "start_game",
                data = new { }
            };
            
            await webSocketClient.SendMessage(JsonConvert.SerializeObject(message));
        }
    }

    private async void PauseGame()
    {
        if (webSocketClient != null && webSocketClient.IsConnected)
        {
            var message = new
            {
                type = "pause_game",
                data = new { }
            };
            
            await webSocketClient.SendMessage(JsonConvert.SerializeObject(message));
        }
    }

    private void ProcessDetectedMoves(List<Move> moves)
    {
        foreach (var move in moves)
        {
            // Trigger move detected event
            OnMoveDetected?.Invoke(move);
            
            // Update character animations
            if (playerCharacter != null)
            {
                playerCharacter.PerformMove(move.move, move.confidence);
            }
            
            Debug.Log($"Detected move: {move.move} with confidence {move.confidence}");
        }
    }

    private void UpdateCharacterAnimations()
    {
        if (currentPlayer != null)
        {
            // Update player character
            if (playerCharacter != null)
            {
                playerCharacter.SetHealth(currentPlayer.health);
                playerCharacter.SetScore(currentPlayer.score);
                
                if (currentPlayer.is_blocking)
                    playerCharacter.SetBlocking(true);
                else if (currentPlayer.is_dodging)
                    playerCharacter.SetDodging(true);
                else
                    playerCharacter.SetNeutral();
            }
            
            // Update opponent character (if multiplayer)
            if (opponentCharacter != null)
            {
                var opponent = currentGameState.players.Find(p => p.id != "player1");
                if (opponent != null)
                {
                    opponentCharacter.SetHealth(opponent.health);
                    opponentCharacter.SetScore(opponent.score);
                }
            }
        }
    }

    private void UpdateUI()
    {
        // Update health display
        if (healthText != null && currentPlayer != null)
        {
            healthText.text = $"Health: {currentPlayer.health}/{maxHealth}";
        }
        
        // Update score display
        if (scoreText != null && currentPlayer != null)
        {
            scoreText.text = $"Score: {currentPlayer.score}";
        }
        
        // Update round display
        if (roundText != null && currentGameState != null)
        {
            roundText.text = $"Round: {currentGameState.current_round}/{currentGameState.max_rounds}";
        }
        
        // Update game state display
        if (gameStateText != null && currentGameState != null)
        {
            gameStateText.text = $"State: {currentGameState.state.ToUpper()}";
        }
        
        // Update button states
        if (startGameButton != null)
        {
            startGameButton.interactable = isConnected && currentGameState.state == "waiting";
        }
        
        if (pauseGameButton != null)
        {
            pauseGameButton.interactable = isConnected && currentGameState.state == "playing";
        }
    }

    // Public methods for external access
    public bool IsConnected => isConnected;
    public GameState CurrentGameState => currentGameState;
    public Player CurrentPlayer => currentPlayer;
    public PoseData LastPoseData => lastPoseData;
} 
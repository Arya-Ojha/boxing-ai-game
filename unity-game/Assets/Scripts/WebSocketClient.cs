using UnityEngine;
using System;
using System.Collections;
using System.Threading.Tasks;
using WebSocketSharp;

public class WebSocketClient : MonoBehaviour
{
    private WebSocket webSocket;
    private string url;
    private bool isConnecting = false;
    
    // Events
    public event Action<string> OnMessageReceived;
    public event Action<bool> OnConnectionChanged;
    public event Action<string> OnError;
    
    public bool IsConnected => webSocket != null && webSocket.ReadyState == WebSocketState.Open;
    
    public WebSocketClient(string websocketUrl)
    {
        this.url = websocketUrl;
    }
    
    public async Task Connect()
    {
        if (isConnecting || IsConnected)
            return;
        
        isConnecting = true;
        
        try
        {
            webSocket = new WebSocket(url);
            
            // Set up event handlers
            webSocket.OnOpen += (sender, e) =>
            {
                Debug.Log("WebSocket connected");
                OnConnectionChanged?.Invoke(true);
            };
            
            webSocket.OnMessage += (sender, e) =>
            {
                Debug.Log($"WebSocket message received: {e.Data}");
                OnMessageReceived?.Invoke(e.Data);
            };
            
            webSocket.OnClose += (sender, e) =>
            {
                Debug.Log($"WebSocket closed: {e.Code} - {e.Reason}");
                OnConnectionChanged?.Invoke(false);
            };
            
            webSocket.OnError += (sender, e) =>
            {
                Debug.LogError($"WebSocket error: {e.Message}");
                OnError?.Invoke(e.Message);
            };
            
            // Connect
            webSocket.Connect();
            
            // Wait for connection
            await WaitForConnection();
            
        }
        catch (Exception e)
        {
            Debug.LogError($"Failed to connect to WebSocket: {e.Message}");
            OnError?.Invoke(e.Message);
        }
        finally
        {
            isConnecting = false;
        }
    }
    
    private async Task WaitForConnection()
    {
        int timeout = 5000; // 5 seconds
        int elapsed = 0;
        
        while (!IsConnected && elapsed < timeout)
        {
            await Task.Delay(100);
            elapsed += 100;
        }
        
        if (!IsConnected)
        {
            throw new TimeoutException("WebSocket connection timeout");
        }
    }
    
    public async Task SendMessage(string message)
    {
        if (!IsConnected)
        {
            Debug.LogWarning("Cannot send message: WebSocket not connected");
            return;
        }
        
        try
        {
            webSocket.Send(message);
            Debug.Log($"WebSocket message sent: {message}");
        }
        catch (Exception e)
        {
            Debug.LogError($"Failed to send WebSocket message: {e.Message}");
            OnError?.Invoke(e.Message);
        }
    }
    
    public void Disconnect()
    {
        if (webSocket != null)
        {
            webSocket.Close();
            webSocket = null;
        }
    }
    
    void OnDestroy()
    {
        Disconnect();
    }
    
    void OnApplicationPause(bool pauseStatus)
    {
        if (pauseStatus)
        {
            // Pause game - keep connection alive
            Debug.Log("Application paused - keeping WebSocket connection alive");
        }
    }
    
    void OnApplicationFocus(bool hasFocus)
    {
        if (!hasFocus)
        {
            Debug.Log("Application lost focus");
        }
    }
} 
#!/usr/bin/env python3
"""
Setup script for Boxing AI Game
Installs dependencies and initializes the project structure
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {command}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception running command: {command}")
        print(f"Exception: {e}")
        return False

def install_python_dependencies():
    """Install Python dependencies for backend and pose detection"""
    print("Installing Python dependencies...")
    
    # Backend dependencies
    if not run_command("pip install -r backend/requirements.txt"):
        print("Failed to install backend dependencies")
        return False
    
    # Pose detection dependencies
    if not run_command("pip install -r pose-detection/requirements.txt"):
        print("Failed to install pose detection dependencies")
        return False
    
    print("Python dependencies installed successfully")
    return True

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Error: Python 3.8 or higher is required")
        return False
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_system_requirements():
    """Check system requirements"""
    print("Checking system requirements...")
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check if camera is available (optional)
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("Camera is available")
            cap.release()
        else:
            print("Warning: Camera not available")
    except ImportError:
        print("Warning: OpenCV not available")
    
    # Check platform
    system = platform.system()
    print(f"Platform: {system}")
    
    return True

def create_directories():
    """Create necessary directories"""
    print("Creating directories...")
    
    directories = [
        "backend/logs",
        "pose-detection/logs",
        "unity-game/Assets/Scripts",
        "unity-game/Assets/Prefabs",
        "unity-game/Assets/Scenes",
        "unity-game/Assets/Materials",
        "unity-game/Assets/Animations",
        "unity-game/Assets/Audio",
        "docs",
        "scripts"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def create_config_files():
    """Create configuration files"""
    print("Creating configuration files...")
    
    # Backend config
    backend_config = """# Backend configuration
[server]
host = "0.0.0.0"
port = 8000
debug = true

[pose_detection]
camera_id = 0
confidence_threshold = 0.5
frame_rate = 30

[game]
max_rounds = 3
round_duration = 180
max_health = 100
"""
    
    with open("backend/config.ini", "w") as f:
        f.write(backend_config)
    
    # Pose detection config
    pose_config = """# Pose detection configuration
[camera]
device_id = 0
width = 640
height = 480
fps = 30

[detection]
confidence_threshold = 0.5
model_complexity = 2
min_detection_confidence = 0.5
min_tracking_confidence = 0.5

[websocket]
backend_url = "ws://localhost:8000/ws/game"
reconnect_interval = 5
"""
    
    with open("pose-detection/config.ini", "w") as f:
        f.write(pose_config)
    
    print("Configuration files created")

def run_tests():
    """Run basic tests"""
    print("Running tests...")
    
    # Test backend
    if run_command("cd backend && python -c 'import main; print(\"Backend imports successful\")'"):
        print("Backend test passed")
    else:
        print("Backend test failed")
    
    # Test pose detection
    if run_command("cd pose-detection && python -c 'import pose_detector; print(\"Pose detection imports successful\")'"):
        print("Pose detection test passed")
    else:
        print("Pose detection test failed")

def main():
    """Main setup function"""
    print("Setting up Boxing AI Game...")
    print("=" * 50)
    
    # Check system requirements
    if not check_system_requirements():
        print("System requirements check failed")
        return False
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_python_dependencies():
        print("Failed to install dependencies")
        return False
    
    # Create config files
    create_config_files()
    
    # Run tests
    run_tests()
    
    print("=" * 50)
    print("Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the backend: cd backend && uvicorn main:app --reload")
    print("2. Start pose detection: cd pose-detection && python pose_detector.py")
    print("3. Open Unity and load the unity-game project")
    print("4. Configure WebSocket URL in GameManager.cs if needed")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
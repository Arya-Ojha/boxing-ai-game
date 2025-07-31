import cv2
import mediapipe as mp
import numpy as np
import asyncio
import json
import websockets
import logging
from typing import List, Dict, Any, Optional
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PoseDetector:
    def __init__(self, camera_id: int = 0, backend_url: str = "ws://localhost:8000/ws/game"):
        self.camera_id = camera_id
        self.backend_url = backend_url
        self.cap = None
        self.mp_pose = mp.solutions.pose
        self.pose = None
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Boxing move detection parameters
        self.move_thresholds = {
            'jab': 0.7,
            'cross': 0.7,
            'hook': 0.6,
            'uppercut': 0.6,
            'block': 0.5,
            'dodge': 0.5,
            'guard': 0.5
        }
        
        # Keypoint indices for boxing moves
        self.keypoints = {
            'nose': 0,
            'left_shoulder': 11,
            'right_shoulder': 12,
            'left_elbow': 13,
            'right_elbow': 14,
            'left_wrist': 15,
            'right_wrist': 16,
            'left_hip': 23,
            'right_hip': 24,
            'left_knee': 25,
            'right_knee': 26,
            'left_ankle': 27,
            'right_ankle': 28
        }
        
        # Boxing move detection functions
        self.boxing_moves = {
            'jab': self._detect_jab,
            'cross': self._detect_cross,
            'hook': self._detect_hook,
            'uppercut': self._detect_uppercut,
            'block': self._detect_block,
            'dodge': self._detect_dodge,
            'guard': self._detect_guard
        }
        
        self.websocket = None
        self.is_running = False

    async def initialize(self):
        """Initialize camera and pose detection"""
        try:
            # Initialize camera
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                raise RuntimeError(f"Could not open camera {self.camera_id}")
            
            # Initialize MediaPipe pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=2,
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # Connect to backend WebSocket
            await self._connect_websocket()
            
            logger.info("Pose detector initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize pose detector: {e}")
            return False

    async def _connect_websocket(self):
        """Connect to backend WebSocket"""
        try:
            self.websocket = await websockets.connect(self.backend_url)
            logger.info(f"Connected to backend at {self.backend_url}")
        except Exception as e:
            logger.error(f"Failed to connect to backend: {e}")
            self.websocket = None

    async def start_detection(self):
        """Start real-time pose detection"""
        if not self.cap or not self.pose:
            logger.error("Pose detector not initialized")
            return
        
        self.is_running = True
        logger.info("Starting pose detection...")
        
        try:
            while self.is_running:
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    continue
                
                # Process frame
                results = await self._process_frame(frame)
                
                # Send results to backend
                if results and self.websocket:
                    await self._send_pose_data(results)
                
                # Display frame (optional)
                if self._should_display_frame():
                    self._display_frame(frame, results)
                
                # Control frame rate
                await asyncio.sleep(0.033)  # ~30 FPS
                
        except Exception as e:
            logger.error(f"Error in pose detection loop: {e}")
        finally:
            await self.cleanup()

    async def _process_frame(self, frame):
        """Process a single frame for pose detection"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process pose detection
            results = self.pose.process(rgb_frame)
            
            if results.pose_landmarks:
                # Extract keypoints
                keypoints = self._extract_keypoints(results.pose_landmarks, frame.shape)
                
                # Detect boxing moves
                detected_moves = self._detect_boxing_moves(keypoints)
                
                return {
                    'keypoints': keypoints,
                    'moves': detected_moves,
                    'timestamp': time.time()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return None

    def _extract_keypoints(self, landmarks, frame_shape):
        """Extract keypoints from MediaPipe landmarks"""
        keypoints = []
        height, width = frame_shape[:2]
        
        for i, landmark in enumerate(landmarks.landmark):
            keypoints.append({
                'index': i,
                'x': landmark.x,
                'y': landmark.y,
                'z': landmark.z,
                'confidence': landmark.visibility
            })
        
        return keypoints

    def _detect_boxing_moves(self, keypoints):
        """Detect boxing moves from keypoints"""
        detected_moves = []
        
        # Convert keypoints to numpy array for easier processing
        pose_data = self._keypoints_to_array(keypoints)
        
        for move_name, detect_func in self.boxing_moves.items():
            confidence = detect_func(pose_data)
            if confidence > self.move_thresholds[move_name]:
                detected_moves.append({
                    'move': move_name,
                    'confidence': confidence,
                    'timestamp': time.time()
                })
        
        return detected_moves

    def _keypoints_to_array(self, keypoints):
        """Convert keypoints to numpy array"""
        pose_data = np.zeros((33, 3))  # x, y, confidence
        
        for kp in keypoints:
            idx = kp['index']
            if 0 <= idx < 33:
                pose_data[idx] = [kp['x'], kp['y'], kp['confidence']]
        
        return pose_data

    def _detect_jab(self, pose_data):
        """Detect jab (straight punch with lead hand)"""
        left_wrist = pose_data[self.keypoints['left_wrist']]
        left_elbow = pose_data[self.keypoints['left_elbow']]
        left_shoulder = pose_data[self.keypoints['left_shoulder']]
        
        # Check if left arm is extended forward
        arm_extension = self._calculate_arm_extension(left_wrist, left_elbow, left_shoulder)
        forward_position = left_wrist[0] > left_shoulder[0]
        
        if arm_extension > 0.8 and forward_position:
            return min(arm_extension, 1.0)
        return 0.0

    def _detect_cross(self, pose_data):
        """Detect cross (straight punch with rear hand)"""
        right_wrist = pose_data[self.keypoints['right_wrist']]
        right_elbow = pose_data[self.keypoints['right_elbow']]
        right_shoulder = pose_data[self.keypoints['right_shoulder']]
        
        # Check if right arm is extended forward
        arm_extension = self._calculate_arm_extension(right_wrist, right_elbow, right_shoulder)
        forward_position = right_wrist[0] > right_shoulder[0]
        
        if arm_extension > 0.8 and forward_position:
            return min(arm_extension, 1.0)
        return 0.0

    def _detect_hook(self, pose_data):
        """Detect hook punch"""
        left_wrist = pose_data[self.keypoints['left_wrist']]
        right_wrist = pose_data[self.keypoints['right_wrist']]
        left_shoulder = pose_data[self.keypoints['left_shoulder']]
        right_shoulder = pose_data[self.keypoints['right_shoulder']]
        
        # Check for horizontal arm movement
        left_hook = (left_wrist[1] > left_shoulder[1] and 
                    abs(left_wrist[0] - left_shoulder[0]) > 0.3)
        right_hook = (right_wrist[1] > right_shoulder[1] and 
                     abs(right_wrist[0] - right_shoulder[0]) > 0.3)
        
        if left_hook or right_hook:
            return 0.8
        return 0.0

    def _detect_uppercut(self, pose_data):
        """Detect uppercut punch"""
        left_wrist = pose_data[self.keypoints['left_wrist']]
        right_wrist = pose_data[self.keypoints['right_wrist']]
        left_shoulder = pose_data[self.keypoints['left_shoulder']]
        right_shoulder = pose_data[self.keypoints['right_shoulder']]
        
        # Check for upward arm movement
        left_uppercut = (left_wrist[1] < left_shoulder[1] and 
                        left_wrist[0] > left_shoulder[0] - 0.2)
        right_uppercut = (right_wrist[1] < right_shoulder[1] and 
                         right_wrist[0] > right_shoulder[0] - 0.2)
        
        if left_uppercut or right_uppercut:
            return 0.8
        return 0.0

    def _detect_block(self, pose_data):
        """Detect blocking movement"""
        left_wrist = pose_data[self.keypoints['left_wrist']]
        right_wrist = pose_data[self.keypoints['right_wrist']]
        left_shoulder = pose_data[self.keypoints['left_shoulder']]
        right_shoulder = pose_data[self.keypoints['right_shoulder']]
        
        # Check if arms are raised in front of face
        left_block = (left_wrist[1] < left_shoulder[1] and 
                     abs(left_wrist[0] - left_shoulder[0]) < 0.3)
        right_block = (right_wrist[1] < right_shoulder[1] and 
                      abs(right_wrist[0] - right_shoulder[0]) < 0.3)
        
        if left_block and right_block:
            return 0.9
        elif left_block or right_block:
            return 0.6
        return 0.0

    def _detect_dodge(self, pose_data):
        """Detect dodging movement"""
        left_hip = pose_data[self.keypoints['left_hip']]
        right_hip = pose_data[self.keypoints['right_hip']]
        left_shoulder = pose_data[self.keypoints['left_shoulder']]
        right_shoulder = pose_data[self.keypoints['right_shoulder']]
        
        # Check for lateral movement
        shoulder_movement = abs(left_shoulder[0] - right_shoulder[0])
        hip_movement = abs(left_hip[0] - right_hip[0])
        
        if shoulder_movement > 0.4 or hip_movement > 0.4:
            return 0.7
        return 0.0

    def _detect_guard(self, pose_data):
        """Detect guard position"""
        left_wrist = pose_data[self.keypoints['left_wrist']]
        right_wrist = pose_data[self.keypoints['right_wrist']]
        left_elbow = pose_data[self.keypoints['left_elbow']]
        right_elbow = pose_data[self.keypoints['right_elbow']]
        
        # Check if arms are in defensive position
        left_guard = (left_wrist[1] > left_elbow[1] and 
                     left_elbow[1] > left_wrist[1] - 0.3)
        right_guard = (right_wrist[1] > right_elbow[1] and 
                      right_elbow[1] > right_wrist[1] - 0.3)
        
        if left_guard and right_guard:
            return 0.8
        return 0.0

    def _calculate_arm_extension(self, wrist, elbow, shoulder):
        """Calculate how extended the arm is"""
        wrist_elbow_dist = np.linalg.norm(wrist[:2] - elbow[:2])
        elbow_shoulder_dist = np.linalg.norm(elbow[:2] - shoulder[:2])
        total_arm_length = wrist_elbow_dist + elbow_shoulder_dist
        straight_dist = np.linalg.norm(wrist[:2] - shoulder[:2])
        
        if total_arm_length > 0:
            extension = straight_dist / total_arm_length
            return min(extension, 1.0)
        return 0.0

    async def _send_pose_data(self, pose_data):
        """Send pose data to backend via WebSocket"""
        try:
            message = {
                "type": "pose_data",
                "data": pose_data
            }
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send pose data: {e}")
            await self._reconnect_websocket()

    async def _reconnect_websocket(self):
        """Reconnect to WebSocket if connection is lost"""
        try:
            if self.websocket:
                await self.websocket.close()
            await self._connect_websocket()
        except Exception as e:
            logger.error(f"Failed to reconnect WebSocket: {e}")

    def _should_display_frame(self):
        """Determine if frame should be displayed"""
        return False  # Set to True for debugging

    def _display_frame(self, frame, results):
        """Display frame with pose landmarks"""
        if results and 'keypoints' in results:
            # Draw pose landmarks
            annotated_frame = frame.copy()
            # Add drawing code here if needed
            cv2.imshow('Pose Detection', annotated_frame)
            cv2.waitKey(1)

    def stop_detection(self):
        """Stop pose detection"""
        self.is_running = False
        logger.info("Stopping pose detection...")

    async def cleanup(self):
        """Cleanup resources"""
        self.is_running = False
        
        if self.cap:
            self.cap.release()
        
        if self.pose:
            self.pose.close()
        
        if self.websocket:
            await self.websocket.close()
        
        cv2.destroyAllWindows()
        logger.info("Pose detector cleaned up")

async def main():
    """Main function to run pose detection"""
    detector = PoseDetector()
    
    if await detector.initialize():
        try:
            await detector.start_detection()
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            await detector.cleanup()
    else:
        logger.error("Failed to initialize pose detector")

if __name__ == "__main__":
    asyncio.run(main()) 
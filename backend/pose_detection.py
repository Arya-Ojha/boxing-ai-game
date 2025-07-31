import mediapipe as mp
import numpy as np
import cv2
import asyncio
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PoseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = None
        self.is_initialized = False
        
        # Boxing gesture thresholds
        self.punch_threshold = 0.7
        self.block_threshold = 0.6
        self.dodge_threshold = 0.5
        
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
        
        # Boxing move definitions
        self.boxing_moves = {
            'jab': self._detect_jab,
            'cross': self._detect_cross,
            'hook': self._detect_hook,
            'uppercut': self._detect_uppercut,
            'block': self._detect_block,
            'dodge': self._detect_dodge,
            'guard': self._detect_guard
        }

    async def initialize(self):
        """Initialize MediaPipe pose detection"""
        try:
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=2,
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.is_initialized = True
            logger.info("Pose detector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pose detector: {e}")
            raise

    async def cleanup(self):
        """Cleanup pose detector resources"""
        if self.pose:
            self.pose.close()
        self.is_initialized = False
        logger.info("Pose detector cleaned up")

    def is_ready(self) -> bool:
        """Check if pose detector is ready"""
        return self.is_initialized and self.pose is not None

    async def process_pose(self, keypoints: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Process pose keypoints and detect boxing moves"""
        if not self.is_ready():
            logger.warning("Pose detector not ready")
            return []

        try:
            # Convert keypoints to numpy array
            pose_data = self._normalize_keypoints(keypoints)
            
            # Detect boxing moves
            detected_moves = []
            
            for move_name, detect_func in self.boxing_moves.items():
                confidence = detect_func(pose_data)
                if confidence > 0.5:  # Minimum confidence threshold
                    detected_moves.append({
                        'move': move_name,
                        'confidence': confidence,
                        'timestamp': asyncio.get_event_loop().time()
                    })
            
            return detected_moves
            
        except Exception as e:
            logger.error(f"Error processing pose: {e}")
            return []

    def _normalize_keypoints(self, keypoints: List[Dict[str, float]]) -> np.ndarray:
        """Normalize keypoints to numpy array"""
        # Convert to 33 keypoints format (MediaPipe standard)
        normalized = np.zeros((33, 3))  # x, y, confidence
        
        for kp in keypoints:
            if 'x' in kp and 'y' in kp and 'confidence' in kp:
                idx = kp.get('index', 0)
                if 0 <= idx < 33:
                    normalized[idx] = [kp['x'], kp['y'], kp['confidence']]
        
        return normalized

    def _detect_jab(self, pose_data: np.ndarray) -> float:
        """Detect jab (straight punch with lead hand)"""
        left_wrist = pose_data[self.keypoints['left_wrist']]
        left_elbow = pose_data[self.keypoints['left_elbow']]
        left_shoulder = pose_data[self.keypoints['left_shoulder']]
        
        # Check if left arm is extended forward
        arm_extension = self._calculate_arm_extension(left_wrist, left_elbow, left_shoulder)
        
        # Check if wrist is in front of shoulder
        forward_position = left_wrist[0] > left_shoulder[0]
        
        if arm_extension > 0.8 and forward_position:
            return min(arm_extension, 1.0)
        return 0.0

    def _detect_cross(self, pose_data: np.ndarray) -> float:
        """Detect cross (straight punch with rear hand)"""
        right_wrist = pose_data[self.keypoints['right_wrist']]
        right_elbow = pose_data[self.keypoints['right_elbow']]
        right_shoulder = pose_data[self.keypoints['right_shoulder']]
        
        # Check if right arm is extended forward
        arm_extension = self._calculate_arm_extension(right_wrist, right_elbow, right_shoulder)
        
        # Check if wrist is in front of shoulder
        forward_position = right_wrist[0] > right_shoulder[0]
        
        if arm_extension > 0.8 and forward_position:
            return min(arm_extension, 1.0)
        return 0.0

    def _detect_hook(self, pose_data: np.ndarray) -> float:
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

    def _detect_uppercut(self, pose_data: np.ndarray) -> float:
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

    def _detect_block(self, pose_data: np.ndarray) -> float:
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

    def _detect_dodge(self, pose_data: np.ndarray) -> float:
        """Detect dodging movement"""
        left_hip = pose_data[self.keypoints['left_hip']]
        right_hip = pose_data[self.keypoints['right_hip']]
        left_shoulder = pose_data[self.keypoints['left_shoulder']]
        right_shoulder = pose_data[self.keypoints['right_shoulder']]
        
        # Check for lateral movement (side-to-side)
        shoulder_movement = abs(left_shoulder[0] - right_shoulder[0])
        hip_movement = abs(left_hip[0] - right_hip[0])
        
        if shoulder_movement > 0.4 or hip_movement > 0.4:
            return 0.7
        return 0.0

    def _detect_guard(self, pose_data: np.ndarray) -> float:
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

    def _calculate_arm_extension(self, wrist: np.ndarray, elbow: np.ndarray, shoulder: np.ndarray) -> float:
        """Calculate how extended the arm is"""
        # Calculate distances
        wrist_elbow_dist = np.linalg.norm(wrist[:2] - elbow[:2])
        elbow_shoulder_dist = np.linalg.norm(elbow[:2] - shoulder[:2])
        
        # Calculate total arm length
        total_arm_length = wrist_elbow_dist + elbow_shoulder_dist
        
        # Calculate straight line distance from shoulder to wrist
        straight_dist = np.linalg.norm(wrist[:2] - shoulder[:2])
        
        # Extension ratio (1.0 = fully extended)
        if total_arm_length > 0:
            extension = straight_dist / total_arm_length
            return min(extension, 1.0)
        return 0.0 
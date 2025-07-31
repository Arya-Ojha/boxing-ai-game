import asyncio
import cv2
import mediapipe as mp
import numpy as np
import logging
from pose_detector import PoseDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pose_detection():
    """Test pose detection functionality"""
    logger.info("Starting pose detection test...")
    
    # Initialize pose detector
    detector = PoseDetector(camera_id=0)
    
    try:
        # Initialize without WebSocket connection for testing
        detector.cap = cv2.VideoCapture(0)
        if not detector.cap.isOpened():
            logger.error("Could not open camera")
            return
        
        detector.pose = detector.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        logger.info("Pose detector initialized successfully")
        
        # Test pose detection for a few frames
        frame_count = 0
        max_frames = 100  # Test for 100 frames
        
        while frame_count < max_frames:
            ret, frame = detector.cap.read()
            if not ret:
                logger.warning("Failed to read frame")
                continue
            
            # Process frame
            results = await detector._process_frame(frame)
            
            if results:
                keypoints = results['keypoints']
                moves = results['moves']
                
                logger.info(f"Frame {frame_count}: Detected {len(moves)} moves")
                
                for move in moves:
                    logger.info(f"  - {move['move']}: {move['confidence']:.2f}")
            
            frame_count += 1
            
            # Display frame
            cv2.imshow('Pose Detection Test', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        logger.info("Pose detection test completed")
        
    except Exception as e:
        logger.error(f"Error during pose detection test: {e}")
    
    finally:
        # Cleanup
        if detector.cap:
            detector.cap.release()
        if detector.pose:
            detector.pose.close()
        cv2.destroyAllWindows()

def test_move_detection():
    """Test boxing move detection with sample data"""
    logger.info("Testing boxing move detection...")
    
    # Create sample pose data
    sample_pose_data = np.zeros((33, 3))
    
    # Simulate a jab position
    sample_pose_data[11] = [0.3, 0.5, 0.9]  # left shoulder
    sample_pose_data[13] = [0.4, 0.5, 0.9]  # left elbow
    sample_pose_data[15] = [0.8, 0.5, 0.9]  # left wrist (extended forward)
    
    # Test jab detection
    detector = PoseDetector()
    jab_confidence = detector._detect_jab(sample_pose_data)
    logger.info(f"Jab detection confidence: {jab_confidence:.2f}")
    
    # Test cross detection
    sample_pose_data[12] = [0.7, 0.5, 0.9]  # right shoulder
    sample_pose_data[14] = [0.6, 0.5, 0.9]  # right elbow
    sample_pose_data[16] = [0.2, 0.5, 0.9]  # right wrist (extended forward)
    
    cross_confidence = detector._detect_cross(sample_pose_data)
    logger.info(f"Cross detection confidence: {cross_confidence:.2f}")
    
    # Test block detection
    sample_pose_data[15] = [0.4, 0.3, 0.9]  # left wrist (raised)
    sample_pose_data[16] = [0.6, 0.3, 0.9]  # right wrist (raised)
    
    block_confidence = detector._detect_block(sample_pose_data)
    logger.info(f"Block detection confidence: {block_confidence:.2f}")

async def main():
    """Main test function"""
    logger.info("Starting pose detection tests...")
    
    # Test move detection with sample data
    test_move_detection()
    
    # Test real-time pose detection
    await test_pose_detection()
    
    logger.info("All tests completed")

if __name__ == "__main__":
    asyncio.run(main()) 
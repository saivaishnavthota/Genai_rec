"""Proctor service for detecting violations"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import cv2
import numpy as np
from ...config import settings
from ..models.ai_sessions import AISessionFlag, FlagType, FlagSeverity
from ..utils.flag_tracker import (
    FlagTracker, create_head_turn_tracker, create_face_absent_tracker,
    create_multi_face_tracker, create_phone_tracker, create_audio_multi_speaker_tracker,
    create_tab_switch_tracker
)
from .clip_service import ClipService

logger = logging.getLogger(__name__)


class ProctorService:
    """Service for proctoring violations"""
    
    def __init__(self, clip_service: ClipService):
        self.clip_service = clip_service
        
        # Initialize trackers
        self.head_turn_tracker = create_head_turn_tracker()
        self.face_absent_tracker = create_face_absent_tracker()
        self.multi_face_tracker = create_multi_face_tracker()
        self.phone_tracker = create_phone_tracker()
        self.audio_multi_speaker_tracker = create_audio_multi_speaker_tracker()
        self.tab_switch_tracker = create_tab_switch_tracker()
        
        # Face detection (using OpenCV DNN or MediaPipe)
        self.face_detector = None
        self._init_face_detector()
    
    def _init_face_detector(self):
        """Initialize face detector"""
        try:
            # Use Haar Cascade (built into OpenCV, no external files needed)
            self.face_detector = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            if self.face_detector.empty():
                raise ValueError("Failed to load Haar Cascade classifier")
            logger.info("Initialized face detector (Haar Cascade)")
        except Exception as e:
            logger.warning(f"Face detector initialization failed: {e}")
            self.face_detector = None
    
    def detect_faces_in_frame(
        self,
        frame: np.ndarray,
        timestamp: float
    ) -> Dict[str, Any]:
        """
        Detect faces in frame using OpenCV
        
        Args:
            frame: Video frame (numpy array)
            timestamp: Frame timestamp
            
        Returns:
            Detection result with face count and confidence
        """
        if not self.face_detector:
            logger.warning("Face detector not initialized")
            return {"face_count": 0, "confidence": 0.0}
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
            
            # Detect faces with more lenient parameters
            # Lower scaleFactor and minNeighbors for better detection
            faces = self.face_detector.detectMultiScale(
                gray,
                scaleFactor=1.05,  # Smaller step = more detection attempts
                minNeighbors=3,    # Lower threshold = more detections
                minSize=(20, 20),  # Smaller minimum size
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            face_count = len(faces)
            confidence = min(0.95, 0.7 + (face_count * 0.1)) if face_count > 0 else 0.0
            
            if face_count > 0:
                logger.debug(f"Detected {face_count} face(s) at {timestamp:.2f}s: {faces.tolist()}")
            
            return {
                "face_count": face_count,
                "confidence": confidence,
                "metadata": {
                    "faces": [{"x": int(x), "y": int(y), "w": int(w), "h": int(h)} 
                             for (x, y, w, h) in faces]
                }
            }
        except Exception as e:
            logger.warning(f"Face detection error: {e}", exc_info=True)
            return {"face_count": 0, "confidence": 0.0}
    
    def process_client_events(
        self,
        session_id: int,
        events: List[Dict[str, Any]],
        current_time: float
    ) -> List[AISessionFlag]:
        """
        Process client telemetry events and emit flags
        
        Args:
            session_id: Session ID
            events: List of client events
            current_time: Current timestamp in seconds
            
        Returns:
            List of emitted flags
        """
        flags = []
        
        for event in events:
            event_type = event.get("event_type")
            timestamp = event.get("timestamp", current_time)
            confidence = event.get("confidence", 0.0)
            metadata = event.get("metadata", {})
            
            if event_type == "head_pose":
                yaw = event.get("yaw", 0)
                # Use absolute yaw for detection
                yaw_abs = abs(yaw)
                # Convert yaw to confidence-like metric (0-1 scale)
                # Threshold: >35° for moderate, >45° for high
                # Normalize: yaw_abs / 45.0 gives us 0-1 where 1.0 = 45°
                # Only trigger if yaw_abs > 35°
                if yaw_abs > 35.0:
                    conf = min(1.0, yaw_abs / 45.0)
                else:
                    conf = 0.0  # Below threshold, no flag
                
                logger.debug(f"Processing head_pose event: yaw={yaw:.2f}°, yaw_abs={yaw_abs:.2f}°, conf={conf:.2f}, timestamp={timestamp:.2f}")
                
                window = self.head_turn_tracker.update(timestamp, conf, {"yaw": yaw, "yaw_abs": yaw_abs})
                if window:
                    logger.info(f"Head turn flag emitted: {window.severity} at {window.t_start:.2f}s (yaw={yaw:.2f}°)")
                    flag = self._create_flag(
                        session_id,
                        FlagType.HEAD_TURN,
                        window.severity,
                        window.confidence,
                        window.t_start,
                        window.t_end,
                        window.metadata
                    )
                    flags.append(flag)
            
            elif event_type == "face_present":
                # Face absent = low confidence
                # confidence is 0.0 when face absent, 1.0 when present
                conf = 1.0 - confidence
                face_count = event.get("face_count", 0)
                
                logger.debug(f"Processing face_present event: confidence={confidence:.2f}, face_count={face_count}, conf_for_absent={conf:.2f}")
                
                window = self.face_absent_tracker.update(timestamp, conf, {"face_count": face_count, **metadata})
                if window:
                    logger.info(f"Face absent flag emitted: {window.severity} at {window.t_start:.2f}s")
                    flag = self._create_flag(
                        session_id,
                        FlagType.FACE_ABSENT,
                        window.severity,
                        window.confidence,
                        window.t_start,
                        window.t_end,
                        window.metadata
                    )
                    flags.append(flag)
            
            elif event_type == "multi_face":
                face_count = event.get("face_count", 1)
                conf = 1.0 if face_count > 1 else 0.0
                
                logger.debug(f"Processing multi_face event: face_count={face_count}, conf={conf:.2f}")
                
                window = self.multi_face_tracker.update(timestamp, conf, {"face_count": face_count})
                if window:
                    logger.info(f"Multi-face flag emitted: {window.severity} at {window.t_start:.2f}s (face_count={face_count})")
                    flag = self._create_flag(
                        session_id,
                        FlagType.MULTI_FACE,
                        window.severity,
                        window.confidence,
                        window.t_start,
                        window.t_end,
                        window.metadata
                    )
                    flags.append(flag)
            
            elif event_type == "phone":
                phone_detected = event.get("phone_detected", False)
                conf = confidence if phone_detected else 0.0
                
                logger.debug(f"Processing phone event: phone_detected={phone_detected}, conf={conf:.2f}")
                
                window = self.phone_tracker.update(timestamp, conf, {"phone_detected": phone_detected, **metadata})
                if window:
                    logger.info(f"Phone flag emitted: {window.severity} at {window.t_start:.2f}s")
                    flag = self._create_flag(
                        session_id,
                        FlagType.PHONE,
                        window.severity,
                        window.confidence,
                        window.t_start,
                        window.t_end,
                        window.metadata
                    )
                    flags.append(flag)
            
            elif event_type == "tab_switch":
                tab_visible = event.get("tab_visible", True)
                # Frontend sends confidence=0.9 when tab is hidden, 0.0 when visible
                # Use confidence directly (higher when tab is hidden)
                conf = confidence if not tab_visible else 0.0
                
                logger.debug(f"Processing tab_switch event: tab_visible={tab_visible}, confidence={confidence:.2f}, conf={conf:.2f}")
                
                window = self.tab_switch_tracker.update(timestamp, conf, {"tab_visible": tab_visible, **metadata})
                if window:
                    logger.info(f"Tab switch flag emitted: {window.severity} at {window.t_start:.2f}s")
                    flag = self._create_flag(
                        session_id,
                        FlagType.TAB_SWITCH,
                        window.severity,
                        window.confidence,
                        window.t_start,
                        window.t_end,
                        window.metadata
                    )
                    flags.append(flag)
        
        return flags
    
    def detect_phone_in_frame(
        self,
        frame: np.ndarray,
        timestamp: float
    ) -> Optional[Dict[str, Any]]:
        """
        Detect phone in frame using OpenCV (improved heuristic detection)
        
        Args:
            frame: Video frame (numpy array)
            timestamp: Frame timestamp
            
        Returns:
            Detection result with confidence or None
        """
        try:
            h, w = frame.shape[:2]
            
            # Convert to grayscale for processing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Use adaptive thresholding for better edge detection
            # This helps detect phones even with varying lighting
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Also try Canny edge detection
            edges = cv2.Canny(blurred, 30, 100)
            
            # Combine both methods
            combined = cv2.bitwise_or(thresh, edges)
            
            # Find contours
            contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            phone_candidates = []
            
            for contour in contours:
                # Skip very small contours
                if cv2.contourArea(contour) < 100:
                    continue
                
                # Get bounding rectangle
                x, y, rect_w, rect_h = cv2.boundingRect(contour)
                
                # More lenient size filter (phones can be 3-30% of frame)
                min_size = min(w, h) * 0.03
                max_size = min(w, h) * 0.30
                
                if rect_w < min_size or rect_h < min_size:
                    continue
                if rect_w > max_size or rect_h > max_size:
                    continue
                
                # More lenient aspect ratio (phones are typically 1.2:1 to 4:1)
                aspect_ratio = max(rect_w, rect_h) / min(rect_w, rect_h) if min(rect_w, rect_h) > 0 else 0
                if aspect_ratio < 1.2 or aspect_ratio > 4.5:
                    continue
                
                # Check if in lower 70% of frame (where hands typically are)
                # Or in center area (where phones might be held)
                is_lower_portion = y > h * 0.3
                is_center_area = (x > w * 0.2 and x < w * 0.8) and (y > h * 0.2 and y < h * 0.8)
                
                if is_lower_portion or is_center_area:
                    # Calculate how rectangular the contour is
                    area = cv2.contourArea(contour)
                    rect_area = rect_w * rect_h
                    extent = area / rect_area if rect_area > 0 else 0
                    
                    # More lenient extent requirement
                    if extent > 0.5:  # Lowered from 0.6
                        # Calculate confidence based on multiple factors
                        size_score = min(1.0, (rect_w * rect_h) / (w * h * 0.1))  # Prefer medium-sized objects
                        aspect_score = 1.0 if 1.5 <= aspect_ratio <= 3.0 else 0.7  # Prefer phone-like aspect ratios
                        extent_score = extent
                        
                        confidence = min(0.85, (size_score * 0.3 + aspect_score * 0.3 + extent_score * 0.4))
                        
                        phone_candidates.append({
                            'x': x, 'y': y, 'w': rect_w, 'h': rect_h,
                            'confidence': confidence,
                            'aspect_ratio': aspect_ratio,
                            'extent': extent
                        })
            
            if phone_candidates:
                # Return the best candidate (highest confidence)
                best = max(phone_candidates, key=lambda x: x['confidence'])
                logger.debug(f"📱 Phone candidate at {timestamp:.2f}s: conf={best['confidence']:.2f}, "
                           f"bbox=({best['x']},{best['y']},{best['w']},{best['h']}), "
                           f"aspect={best['aspect_ratio']:.2f}, extent={best['extent']:.2f}")
                return {
                    "confidence": best['confidence'],
                    "metadata": {
                        "bbox": [best['x'], best['y'], best['w'], best['h']],
                        "aspect_ratio": best['aspect_ratio'],
                        "extent": best['extent']
                    }
                }
            
            return None
        except Exception as e:
            logger.warning(f"Phone detection error: {e}", exc_info=True)
            return None
    
    def process_frame(
        self,
        session_id: int,
        frame: np.ndarray,
        timestamp: float,
        recording_path: Optional[str] = None
    ) -> Optional[AISessionFlag]:
        """
        Process a single frame for violations
        
        Args:
            session_id: Session ID
            frame: Video frame
            timestamp: Frame timestamp
            recording_path: Optional path to recording for clip generation
            
        Returns:
            Flag if violation detected, None otherwise
        """
        # Phone detection
        phone_detection = self.detect_phone_in_frame(frame, timestamp)
        if phone_detection and phone_detection.get("confidence", 0) >= 0.60:
            window = self.phone_tracker.update(
                timestamp,
                phone_detection["confidence"],
                phone_detection.get("metadata", {})
            )
            if window:
                clip_url = None
                if recording_path:
                    try:
                        clip_url = self.clip_service.generate_and_upload_clip(
                            session_id,
                            0,  # Flag ID would be set after creation
                            recording_path,
                            window.t_start,
                            window.t_end
                        )
                    except Exception as e:
                        logger.error(f"Failed to generate clip: {e}")
                
                flag = self._create_flag(
                    session_id,
                    FlagType.PHONE,
                    window.severity,
                    window.confidence,
                    window.t_start,
                    window.t_end,
                    window.metadata,
                    clip_url
                )
                return flag
        
        return None
    
    def _create_flag(
        self,
        session_id: int,
        flag_type: FlagType,
        severity: FlagSeverity,
        confidence: float,
        t_start: float,
        t_end: float,
        metadata: Dict,
        clip_url: Optional[str] = None
    ) -> AISessionFlag:
        """Create a flag object"""
        return AISessionFlag(
            session_id=session_id,
            flag_type=flag_type,
            severity=severity,
            confidence=confidence,
            t_start=t_start,
            t_end=t_end,
            clip_url=clip_url,
            flag_metadata=metadata
        )


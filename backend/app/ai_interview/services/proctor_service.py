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
            # Try to load OpenCV DNN face detector
            prototxt = "models/deploy.prototxt"  # Would need actual model files
            model = "models/res10_300x300_ssd_iter_140000.caffemodel"
            # For now, use Haar Cascade as fallback
            self.face_detector = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            logger.info("Initialized face detector")
        except Exception as e:
            logger.warning(f"Face detector initialization failed: {e}")
    
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
                # Threshold: 35° for moderate, 45° for high
                # So we normalize: yaw_abs / 45.0 gives us 0-1 where 1.0 = 45°
                conf = min(1.0, yaw_abs / 45.0)
                
                logger.debug(f"Processing head_pose event: yaw={yaw:.2f}°, conf={conf:.2f}, timestamp={timestamp:.2f}")
                
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
                conf = 1.0 - confidence if not tab_visible else 0.0  # Higher conf when tab hidden
                
                logger.debug(f"Processing tab_switch event: tab_visible={tab_visible}, conf={conf:.2f}")
                
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
        Detect phone in frame using YOLO (stub - would need actual YOLO model)
        
        Args:
            frame: Video frame (numpy array)
            timestamp: Frame timestamp
            
        Returns:
            Detection result or None
        """
        # TODO: Implement YOLO phone detection
        # For now, return None
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


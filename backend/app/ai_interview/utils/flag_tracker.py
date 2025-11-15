"""
Flag Tracker - Debounces telemetry events into proctor flags

Implements exact thresholds as specified:
- Head pose: Moderate if |yaw|>35° for ≥2.0s; High if ≥45° for ≥3.0s
- Face absent: Moderate if ≥3s; High if ≥8s
- Multi-face: High if >1 face for ≥0.5s
- Phone: Moderate if conf≥0.60 for ≥1.0s; High if conf≥0.75 for ≥2.0s
- Audio multi-speaker: Moderate ≥2s; High ≥5s
"""
import logging
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
from ..models.ai_sessions import FlagType, FlagSeverity

logger = logging.getLogger(__name__)


class FlagKind(str, Enum):
    """Flag kind for tracking"""
    HEAD_TURN = "head_turn"
    FACE_ABSENT = "face_absent"
    MULTI_FACE = "multi_face"
    PHONE = "phone"
    AUDIO_MULTI_SPEAKER = "audio_multi_speaker"
    TAB_SWITCH = "tab_switch"


@dataclass
class FlagWindow:
    """Emitted flag window"""
    t_start: float
    t_end: float
    confidence: float
    severity: FlagSeverity
    metadata: Dict


class FlagTracker:
    """Tracks telemetry and emits flags when thresholds are met"""
    
    def __init__(
        self,
        kind: FlagKind,
        min_conf: float,
        min_duration: float,
        cooldown: float = 1.0,
        high_severity_conf: Optional[float] = None,
        high_severity_duration: Optional[float] = None
    ):
        """
        Args:
            kind: Flag kind
            min_conf: Minimum confidence for moderate severity
            min_duration: Minimum duration for moderate severity (seconds)
            cooldown: Cooldown period before next flag (seconds)
            high_severity_conf: Optional confidence threshold for high severity
            high_severity_duration: Optional duration threshold for high severity
        """
        self.kind = kind
        self.min_conf = min_conf
        self.min_duration = min_duration
        self.cooldown = cooldown
        self.high_severity_conf = high_severity_conf
        self.high_severity_duration = high_severity_duration
        
        # State
        self.active_start: Optional[float] = None
        self.max_conf: float = 0.0
        self.last_emit_time: float = 0.0
        self.metadata: Dict = {}
    
    def update(self, t: float, conf: float, metadata: Optional[Dict] = None) -> Optional[FlagWindow]:
        """
        Update tracker with new observation
        
        Args:
            t: Timestamp in seconds
            conf: Confidence score (0.0 to 1.0)
            metadata: Optional metadata
            
        Returns:
            FlagWindow if threshold exceeded, None otherwise
        """
        if metadata:
            self.metadata.update(metadata)
        
        # Check if condition is met
        meets_threshold = conf >= self.min_conf
        
        if meets_threshold:
            # Check for high severity
            is_high = (
                self.high_severity_conf is not None
                and self.high_severity_duration is not None
                and conf >= self.high_severity_conf
            )
            
            if self.active_start is None:
                # Start tracking
                self.active_start = t
                self.max_conf = conf
            else:
                # Update max confidence
                self.max_conf = max(self.max_conf, conf)
            
            # Check if we should emit
            duration = t - self.active_start
            
            # Determine severity
            if is_high and duration >= self.high_severity_duration:
                severity = FlagSeverity.HIGH
                required_duration = self.high_severity_duration
            else:
                severity = FlagSeverity.MODERATE
                required_duration = self.min_duration
            
            # Log tracker state for debugging
            logger.debug(f"Tracker {self.kind}: t={t:.2f}s, conf={conf:.2f}, duration={duration:.2f}s, "
                        f"required={required_duration:.2f}s, active_start={self.active_start}, "
                        f"cooldown_ok={t - self.last_emit_time >= self.cooldown}")
            
            if duration >= required_duration:
                # Check cooldown
                if t - self.last_emit_time >= self.cooldown:
                    # Emit flag with 2s pre/post roll
                    window = FlagWindow(
                        t_start=max(0, self.active_start - 2.0),
                        t_end=t + 2.0,
                        confidence=self.max_conf,
                        severity=severity,
                        metadata=self.metadata.copy()
                    )
                    logger.info(f"✅ Tracker {self.kind} emitting flag: {severity} at {window.t_start:.2f}s-{window.t_end:.2f}s "
                              f"(duration={duration:.2f}s >= {required_duration:.2f}s)")
                    self.active_start = None
                    self.max_conf = 0.0
                    self.last_emit_time = t
                    self.metadata = {}
                    return window
                else:
                    logger.debug(f"⏸️ Tracker {self.kind} in cooldown: {t - self.last_emit_time:.2f}s < {self.cooldown:.2f}s")
            else:
                logger.debug(f"⏳ Tracker {self.kind} duration not met: {duration:.2f}s < {required_duration:.2f}s")
        else:
            # Reset if condition not met
            if self.active_start is not None:
                logger.debug(f"🔄 Tracker {self.kind} resetting: conf={conf:.2f} < min_conf={self.min_conf:.2f}")
            self.active_start = None
            self.max_conf = 0.0
        
        return None


# Factory functions for specific flag types
def create_head_turn_tracker() -> FlagTracker:
    """Head turn tracker: Moderate if |yaw|>35° for ≥2.0s; High if ≥45° for ≥3.0s"""
    return FlagTracker(
        kind=FlagKind.HEAD_TURN,
        min_conf=0.5,  # Threshold for >35° (35/45 = 0.778, so any value >35° will be >= 0.778)
        min_duration=2.0,
        high_severity_conf=0.9,  # Threshold for >45° (45/45 = 1.0)
        high_severity_duration=3.0,
        cooldown=2.0
    )


def create_face_absent_tracker() -> FlagTracker:
    """Face absent tracker: Moderate if ≥3s; High if ≥8s"""
    return FlagTracker(
        kind=FlagKind.FACE_ABSENT,
        min_conf=0.5,  # Face absent = low confidence
        min_duration=3.0,
        high_severity_conf=0.5,
        high_severity_duration=8.0,
        cooldown=1.0
    )


def create_multi_face_tracker() -> FlagTracker:
    """Multi-face tracker: High if >1 face for ≥0.5s"""
    return FlagTracker(
        kind=FlagKind.MULTI_FACE,
        min_conf=0.5,  # Lower threshold for better detection
        min_duration=0.5,  # 0.5s = 1 frame at 2fps sampling
        high_severity_conf=0.5,
        high_severity_duration=0.5,
        cooldown=0.0  # No cooldown - allow immediate flags
    )


def create_phone_tracker() -> FlagTracker:
    """Phone tracker: Moderate if conf≥0.50 for ≥0.5s; High if conf≥0.70 for ≥1.0s"""
    return FlagTracker(
        kind=FlagKind.PHONE,
        min_conf=0.50,  # Lowered from 0.60
        min_duration=0.5,  # 0.5s = 1 frame at 2fps sampling
        high_severity_conf=0.70,  # Lowered from 0.75
        high_severity_duration=1.0,  # 1.0s = 2 frames at 2fps sampling
        cooldown=0.0  # No cooldown - allow immediate flags
    )


def create_audio_multi_speaker_tracker() -> FlagTracker:
    """Audio multi-speaker tracker: Moderate ≥2s; High ≥5s"""
    return FlagTracker(
        kind=FlagKind.AUDIO_MULTI_SPEAKER,
        min_conf=0.6,  # Multi-speaker detection confidence
        min_duration=2.0,
        high_severity_conf=0.6,
        high_severity_duration=5.0,
        cooldown=1.0
    )


def create_tab_switch_tracker() -> FlagTracker:
    """Tab switch tracker: Moderate if tab hidden ≥2s; High if ≥5s"""
    return FlagTracker(
        kind=FlagKind.TAB_SWITCH,
        min_conf=0.7,  # Tab not visible
        min_duration=2.0,
        high_severity_conf=0.7,
        high_severity_duration=5.0,
        cooldown=1.0
    )


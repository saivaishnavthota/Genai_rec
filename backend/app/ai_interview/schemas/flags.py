"""Proctor flag schemas"""
from datetime import datetime
from typing import Optional, Literal
from decimal import Decimal
from pydantic import Field, field_validator, ConfigDict
from .base import BaseSchema
from ..models.ai_sessions import FlagType, FlagSeverity


class ClientEvent(BaseSchema):
    """Client-side telemetry event (head pose, face detection)"""
    event_type: Literal["head_pose", "face_present", "multi_face", "phone", "tab_switch"] = Field(
        ..., description="Type of telemetry event"
    )
    timestamp: float = Field(..., description="Event timestamp in seconds")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    metadata: dict = Field(default_factory=dict, description="Additional event data")
    
    # For head_pose events
    yaw: Optional[float] = Field(None, description="Head yaw angle in degrees")
    pitch: Optional[float] = Field(None, description="Head pitch angle in degrees")
    roll: Optional[float] = Field(None, description="Head roll angle in degrees")
    
    # For face detection events
    face_count: Optional[int] = Field(None, ge=0, description="Number of faces detected")
    
    # For phone detection events
    phone_detected: Optional[bool] = Field(None, description="Phone detected in frame")
    
    # For tab switch events
    tab_visible: Optional[bool] = Field(None, description="Tab is visible")
    
    @field_validator("yaw", "pitch", "roll")
    @classmethod
    def validate_angles(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if not -180 <= v <= 180:
                raise ValueError("Angle must be between -180 and 180 degrees")
        return v


class ClientEventsRequest(BaseSchema):
    """Batch of client events"""
    events: list[ClientEvent] = Field(..., min_length=1, description="List of telemetry events")


class FlagOut(BaseSchema):
    """Proctor flag output schema"""
    model_config = ConfigDict(populate_by_name=True, by_alias=True)
    
    id: int
    session_id: int
    flag_type: FlagType
    severity: FlagSeverity
    confidence: Decimal
    t_start: Decimal
    t_end: Decimal
    clip_url: Optional[str] = None
    metadata: Optional[dict] = Field(None, alias="flag_metadata", description="Additional flag metadata")
    created_at: datetime


class FlagCreate(BaseSchema):
    """Internal schema for creating flags"""
    session_id: int
    flag_type: FlagType
    severity: FlagSeverity
    confidence: float
    t_start: float
    t_end: float
    clip_url: Optional[str] = None
    flag_metadata: Optional[dict] = Field(None, description="Additional flag metadata")


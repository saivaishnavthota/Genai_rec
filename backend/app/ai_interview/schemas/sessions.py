"""Session schemas"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import Field
from .base import BaseSchema
from ..models.ai_sessions import SessionStatus, Recommendation


class SessionCreate(BaseSchema):
    """Request schema for creating a new AI interview session"""
    application_id: int = Field(..., description="Application ID (candidate)")
    job_id: int = Field(..., description="Job ID")


class SessionOut(BaseSchema):
    """Response schema for AI interview session"""
    id: int
    application_id: int
    job_id: int
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    status: SessionStatus
    total_score: Optional[Decimal] = None
    recommendation: Optional[Recommendation] = None
    transcript_url: Optional[str] = None
    video_url: Optional[str] = None
    report_json: Optional[dict] = None
    policy_version: str
    rubric_version: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class SessionStartResponse(BaseSchema):
    """Response when starting a session"""
    session_id: int
    webrtc_token: Optional[str] = None  # Optional WebRTC token for streaming
    policy_version: str
    rubric_version: str


class SessionReportOut(BaseSchema):
    """Full session report with flags and scores"""
    session: SessionOut
    flags: list[dict]  # Will be validated as FlagOut
    transcript: Optional[dict] = None  # JSON transcript with timestamps
    scores: Optional[dict] = None  # Will be validated as ScoreOut


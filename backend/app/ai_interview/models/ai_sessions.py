"""
AI Interview Session Models
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    Numeric, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid
from ...database import Base


class SessionStatus(str, enum.Enum):
    """Session status enumeration"""
    CREATED = "created"
    LIVE = "live"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


class Recommendation(str, enum.Enum):
    """Final recommendation enumeration"""
    PASS = "pass"
    REVIEW = "review"
    FAIL = "fail"


class FlagType(str, enum.Enum):
    """Proctor flag type enumeration"""
    HEAD_TURN = "head_turn"
    FACE_ABSENT = "face_absent"
    MULTI_FACE = "multi_face"
    PHONE = "phone"
    AUDIO_MULTI_SPEAKER = "audio_multi_speaker"
    SCREEN_POLICY = "screen_policy"
    TAB_SWITCH = "tab_switch"


class FlagSeverity(str, enum.Enum):
    """Flag severity enumeration"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class AISession(Base):
    """AI Interview Session"""
    __tablename__ = "ai_interview_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    # Using application_id to reference candidates (Application model)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    status = Column(
        SQLEnum(SessionStatus, native_enum=False),
        nullable=False,
        default=SessionStatus.CREATED,
        index=True
    )
    
    total_score = Column(Numeric(5, 2), nullable=True)  # 0.00 to 10.00
    recommendation = Column(
        SQLEnum(Recommendation, native_enum=False),
        nullable=True
    )
    
    transcript_url = Column(Text, nullable=True)
    video_url = Column(Text, nullable=True)  # URL to video recording
    report_json = Column(JSON, nullable=True)  # Full report with citations
    
    policy_version = Column(String(50), nullable=False, default="1.0")
    rubric_version = Column(String(50), nullable=False, default="1.0")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    application = relationship("Application", foreign_keys=[application_id])
    job = relationship("Job", foreign_keys=[job_id])
    flags = relationship("AISessionFlag", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_session_application", "application_id"),
        Index("idx_session_job", "job_id"),
        Index("idx_session_status", "status"),
    )


class AISessionFlag(Base):
    """Proctor flags generated during AI interview"""
    __tablename__ = "ai_proctor_flags"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("ai_interview_sessions.id"), nullable=False, index=True)
    
    flag_type = Column(
        SQLEnum(FlagType, native_enum=False),
        nullable=False,
        index=True
    )
    severity = Column(
        SQLEnum(FlagSeverity, native_enum=False),
        nullable=False,
        index=True
    )
    confidence = Column(Numeric(5, 4), nullable=False)  # 0.0000 to 1.0000
    
    t_start = Column(Numeric(10, 3), nullable=False)  # Start time in seconds
    t_end = Column(Numeric(10, 3), nullable=False)    # End time in seconds
    
    clip_url = Column(Text, nullable=True)  # URL to 6-10s clip
    flag_metadata = Column(JSON, nullable=True)  # Additional flag metadata (renamed from 'metadata' - SQLAlchemy reserved)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("AISession", back_populates="flags")
    
    __table_args__ = (
        Index("idx_flag_session_time", "session_id", "t_start"),
        Index("idx_flag_type", "flag_type"),
        Index("idx_flag_severity", "severity"),
    )


from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date, Time, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class InterviewSchedule(Base):
    __tablename__ = "interview_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, nullable=False)
    
    # Availability Management
    availability_requested_at = Column(DateTime(timezone=True), nullable=True)
    available_slots = Column(JSON, nullable=True)  # Array of slot objects
    slots_generated_from = Column(Date, nullable=True)
    slots_generated_to = Column(Date, nullable=True)
    
    # Candidate Selection
    selected_slot_date = Column(Date, nullable=True)
    selected_slot_time = Column(Time, nullable=True)
    candidate_selected_at = Column(DateTime(timezone=True), nullable=True)
    
    # Interview Details
    primary_interviewer_email = Column(String(255), nullable=True)
    primary_interviewer_name = Column(String(255), nullable=True)
    backup_interviewer_email = Column(String(255), nullable=True)
    backup_interviewer_name = Column(String(255), nullable=True)
    interview_scheduled_at = Column(DateTime(timezone=True), nullable=True)
    interview_duration = Column(Integer, default=60)  # minutes
    
    # Google Meet Integration
    google_meet_link = Column(String(500), nullable=True)
    google_calendar_event_id = Column(String(255), nullable=True)
    google_meet_created = Column(DateTime(timezone=True), nullable=True)
    
    # Status Tracking
    status = Column(String(50), default="pending")  # pending, confirmed, completed, cancelled
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    application = relationship("Application", back_populates="interview_schedule", foreign_keys=[application_id])
    reviews = relationship("InterviewReview", back_populates="interview_schedule")

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class InterviewReview(Base):
    __tablename__ = "interview_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    interview_schedule_id = Column(Integer, ForeignKey("interview_schedules.id"), nullable=True)
    
    # Review Source
    interviewer_email = Column(String(255), nullable=True)
    interviewer_name = Column(String(255), nullable=True)
    interviewer_type = Column(String(50), nullable=True)  # 'primary' or 'backup'
    review_email_subject = Column(String(500), nullable=True)
    review_email_body = Column(Text, nullable=True)
    review_received_at = Column(DateTime(timezone=True), nullable=True)
    review_submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Parsed Scores (1-10 scale)
    technical_score = Column(Integer, nullable=True)
    communication_score = Column(Integer, nullable=True)
    problem_solving_score = Column(Integer, nullable=True)
    cultural_fit_score = Column(Integer, nullable=True)
    leadership_potential = Column(Integer, nullable=True)
    
    # Overall Assessment
    overall_rating = Column(Integer, nullable=True)  # 1-10 scale
    overall_recommendation = Column(String(20), nullable=True)  # hire, reject, maybe
    strengths = Column(Text, nullable=True)
    areas_for_improvement = Column(Text, nullable=True)
    additional_comments = Column(Text, nullable=True)
    
    # Processing Status
    is_valid_format = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_errors = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    application = relationship("Application", back_populates="interview_review", foreign_keys=[application_id])
    interview_schedule = relationship("InterviewSchedule", back_populates="reviews")

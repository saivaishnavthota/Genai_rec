from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class ResumeUpdateRequest(Base):
    """Track resume update requests for candidates with score < 70"""
    __tablename__ = "resume_update_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, unique=True)
    
    # LLM Evaluation
    llm_evaluation_result = Column(Boolean, nullable=False)  # True if LLM says "good candidate"
    llm_evaluation_reason = Column(Text, nullable=True)  # LLM's reasoning
    llm_evaluation_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Update Tracking
    update_attempts_count = Column(Integer, default=0, nullable=False)  # 0-3 attempts
    max_attempts = Column(Integer, default=3, nullable=False)
    
    # Email Tracking
    last_email_sent_at = Column(DateTime(timezone=True), nullable=True)
    next_email_due_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(50), default="llm_evaluation_pending", nullable=False)
    # Possible statuses:
    # - "llm_evaluation_pending": Initial state, waiting for LLM evaluation
    # - "llm_approved": LLM approved, ready to send first email
    # - "email_sent": Email sent, waiting for candidate response
    # - "resume_updated": Candidate updated resume, needs re-scoring
    # - "completed_success": Candidate achieved ≥70 score after updates
    # - "completed_failure": Max attempts reached, final rejection
    # - "llm_rejected": LLM rejected, immediate rejection
    
    # Final outcome
    final_score_achieved = Column(Float, nullable=True)
    completion_reason = Column(String(100), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    application = relationship("Application", back_populates="resume_update_request")
    update_history = relationship("ResumeUpdateHistory", back_populates="update_request", cascade="all, delete-orphan")


class ResumeUpdateHistory(Base):
    """Track individual resume update attempts"""
    __tablename__ = "resume_update_history"
    
    id = Column(Integer, primary_key=True, index=True)
    update_request_id = Column(Integer, ForeignKey("resume_update_requests.id"), nullable=False)
    
    # Update Details
    attempt_number = Column(Integer, nullable=False)  # 1, 2, or 3
    email_sent_at = Column(DateTime(timezone=True), nullable=False)
    
    # Resume Update
    resume_updated = Column(Boolean, default=False, nullable=False)
    resume_updated_at = Column(DateTime(timezone=True), nullable=True)
    old_resume_filename = Column(String(255), nullable=True)
    new_resume_filename = Column(String(255), nullable=True)
    
    # Re-scoring Results
    old_score = Column(Float, nullable=True)
    new_score = Column(Float, nullable=True)
    score_improvement = Column(Float, nullable=True)  # new_score - old_score
    
    # Scoring Details
    new_scoring_details = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(50), default="email_sent", nullable=False)
    # Possible statuses:
    # - "email_sent": Email sent, waiting for response
    # - "resume_received": New resume uploaded
    # - "rescored": Resume rescored
    # - "threshold_achieved": Score ≥70 achieved
    # - "expired": 24 hours passed without update
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    update_request = relationship("ResumeUpdateRequest", back_populates="update_history")


class LLMEvaluationLog(Base):
    """Log all LLM evaluations for audit and improvement"""
    __tablename__ = "llm_evaluation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    
    # Input Data
    candidate_data = Column(JSON, nullable=False)  # Skills, experience, education, etc.
    job_requirements = Column(JSON, nullable=False)  # Job skills, requirements, etc.
    initial_score = Column(Float, nullable=False)
    
    # LLM Request/Response
    llm_prompt = Column(Text, nullable=False)
    llm_response_raw = Column(Text, nullable=False)
    llm_response_parsed = Column(JSON, nullable=True)
    
    # Evaluation Result
    evaluation_result = Column(Boolean, nullable=False)  # True = good candidate, False = reject
    evaluation_confidence = Column(Float, nullable=True)  # 0-1 confidence score if provided
    evaluation_reasoning = Column(Text, nullable=True)
    
    # Processing Details
    processing_time_ms = Column(Integer, nullable=True)
    llm_model_used = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    application = relationship("Application")

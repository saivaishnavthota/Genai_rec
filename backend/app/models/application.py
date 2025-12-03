from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    reference_number = Column(String, unique=True, nullable=False, index=True)
    
    # Candidate Information
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    portfolio_url = Column(String, nullable=True)
    
    # Resume and Additional Info
    resume_filename = Column(String, nullable=False)
    resume_path = Column(String, nullable=False)
    cover_letter = Column(Text, nullable=True)
    additional_info = Column(Text, nullable=True)
    
    # Parsed Resume Data
    parsed_skills = Column(JSON, nullable=True)  # Extracted from resume
    parsed_experience = Column(JSON, nullable=True)  # Work experience
    parsed_education = Column(JSON, nullable=True)  # Education details
    parsed_certifications = Column(JSON, nullable=True)  # Certifications
    
    # Application Status
    # Standardized statuses: pending, under_review, shortlisted, interview_scheduled, hired, rejected
    status = Column(String, default="pending")
    current_stage = Column(String, default="application")  # application, screening, interview, final
    
    # Foreign Keys
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    interview_schedule_id = Column(Integer, ForeignKey("interview_schedules.id"), nullable=True)
    interview_review_id = Column(Integer, ForeignKey("interview_reviews.id"), nullable=True)
    
    # Interview Tracking
    selection_email_sent_at = Column(DateTime(timezone=True), nullable=True)
    hr_notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    final_interview_score = Column(DECIMAL(5,2), nullable=True)
    
    # Final Decision Details
    rejection_reason = Column(Text, nullable=True)  # Explanation for rejection
    tentative_joining_date = Column(DateTime(timezone=True), nullable=True)  # Tentative joining date for hired candidates
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    job = relationship("Job", back_populates="applications")
    scores = relationship("ApplicationScore", back_populates="application", cascade="all, delete-orphan", order_by="ApplicationScore.created_at.desc()")
    interview_schedule = relationship("InterviewSchedule", back_populates="application", uselist=False, foreign_keys="InterviewSchedule.application_id")
    interview_review = relationship("InterviewReview", back_populates="application", uselist=False, foreign_keys="InterviewReview.application_id")
    resume_update_request = relationship("ResumeUpdateRequest", back_populates="application", uselist=False, cascade="all, delete-orphan")

class ApplicationScore(Base):
    __tablename__ = "application_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    
    # Scoring Details
    match_score = Column(Float, nullable=False, default=0.0)  # Job-candidate match score
    ats_score = Column(Float, nullable=False, default=0.0)    # ATS compatibility score
    final_score = Column(Float, nullable=False, default=0.0)  # Weighted average
    
    # Score Breakdown
    skills_match = Column(Float, nullable=True)
    experience_match = Column(Float, nullable=True)
    education_match = Column(Float, nullable=True)
    certification_match = Column(Float, nullable=True)
    
    # ATS Breakdown
    ats_format_score = Column(Float, nullable=True)
    ats_keywords_score = Column(Float, nullable=True)
    ats_structure_score = Column(Float, nullable=True)
    
    # Additional scoring data
    scoring_details = Column(JSON, nullable=True)  # Detailed breakdown
    ai_feedback = Column(Text, nullable=True)      # AI-generated feedback (rule-based summary)
    score_explanation = Column(Text, nullable=True)  # LLM-generated detailed explanation
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    application = relationship("Application", back_populates="scores")

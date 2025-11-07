from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    short_description = Column(Text, nullable=True)
    department = Column(String, nullable=True)
    location = Column(String, nullable=True)
    job_type = Column(String, nullable=True)  # full-time, part-time, contract, etc.
    experience_level = Column(String, nullable=True)  # entry, mid, senior
    salary_range = Column(String, nullable=True)
    
    # AI Generated fields
    key_skills = Column(JSON, nullable=True)  # List of skills
    required_experience = Column(String, nullable=True)
    certifications = Column(JSON, nullable=True)  # List of certifications
    additional_requirements = Column(JSON, nullable=True)
    
    # Status and workflow
    status = Column(String, default="draft")  # draft, pending_approval, approved, published, archived
    is_active = Column(Boolean, default=True)
    
    # Foreign Keys
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="jobs")
    created_by_user = relationship("User", back_populates="jobs_created", foreign_keys=[created_by])
    approved_by_user = relationship("User", back_populates="jobs_approved", foreign_keys=[approved_by])
    requirements = relationship("JobRequirement", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

class JobRequirement(Base):
    __tablename__ = "job_requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    requirement_type = Column(String, nullable=False)  # skill, experience, certification, education
    requirement_value = Column(String, nullable=False)
    is_mandatory = Column(Boolean, default=False)
    weight = Column(Integer, default=1)  # For scoring purposes
    
    # Relationships
    job = relationship("Job", back_populates="requirements")

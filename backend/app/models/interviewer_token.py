from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base
from datetime import datetime, timedelta, timezone
import uuid

class InterviewerToken(Base):
    __tablename__ = "interviewer_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    interviewer_email = Column(String(255), nullable=False)
    interviewer_name = Column(String(255), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    interviewer_type = Column(String(50), nullable=False)  # 'primary' or 'backup'
    
    # Token validity
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = relationship("Application", foreign_keys=[application_id])
    
    @classmethod
    def create_token(cls, interviewer_email: str, interviewer_name: str, application_id: int, interviewer_type: str):
        """Create a new interviewer token valid for 24 hours"""
        token = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        
        return cls(
            token=token,
            interviewer_email=interviewer_email,
            interviewer_name=interviewer_name,
            application_id=application_id,
            interviewer_type=interviewer_type,
            expires_at=expires_at
        )
    
    def is_valid(self) -> bool:
        """Check if token is still valid"""
        now = datetime.now(timezone.utc)
        return not self.is_used and now < self.expires_at
    
    def mark_used(self):
        """Mark token as used"""
        self.is_used = True
        self.used_at = datetime.now(timezone.utc)

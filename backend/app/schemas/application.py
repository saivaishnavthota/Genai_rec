from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class ApplicationBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    cover_letter: Optional[str] = None
    additional_info: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    job_id: int

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    current_stage: Optional[str] = None

class ApplicationScoreResponse(BaseModel):
    id: int
    match_score: float
    ats_score: float
    final_score: float
    skills_match: Optional[float] = None
    experience_match: Optional[float] = None
    education_match: Optional[float] = None
    certification_match: Optional[float] = None
    ats_format_score: Optional[float] = None
    ats_keywords_score: Optional[float] = None
    ats_structure_score: Optional[float] = None
    scoring_details: Optional[Dict[str, Any]] = None
    ai_feedback: Optional[str] = None
    score_explanation: Optional[str] = None  # LLM-generated detailed explanation
    created_at: datetime
    
    class Config:
        from_attributes = True

class ApplicationResponse(ApplicationBase):
    id: int
    reference_number: str
    resume_filename: str
    parsed_skills: Optional[List[str]] = None
    parsed_experience: Optional[List[Dict[str, Any]]] = None
    parsed_education: Optional[List[Dict[str, Any]]] = None
    parsed_certifications: Optional[List[str]] = None
    status: str
    current_stage: str
    job_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    scores: List[ApplicationScoreResponse] = []
    
    class Config:
        from_attributes = True

class ApplicationListResponse(BaseModel):
    total: int
    applications: List[ApplicationResponse]
    
class ApplicationStatsResponse(BaseModel):
    total_applications: int
    shortlisted_candidates: int
    rejected_candidates: int
    under_review: int
    by_job: Dict[str, int]
    by_status: Dict[str, int]

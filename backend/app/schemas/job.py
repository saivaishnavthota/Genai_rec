from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class JobRequirementCreate(BaseModel):
    requirement_type: str
    requirement_value: str
    is_mandatory: bool = False
    weight: int = 1

class JobRequirementResponse(JobRequirementCreate):
    id: int
    job_id: int
    
    class Config:
        from_attributes = True

class JobBase(BaseModel):
    title: str
    description: str
    short_description: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_range: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_range: Optional[str] = None
    key_skills: Optional[List[str]] = None
    required_experience: Optional[str] = None
    certifications: Optional[List[str]] = None
    additional_requirements: Optional[List[str]] = None
    status: Optional[str] = None

class JobResponse(JobBase):
    id: int
    key_skills: Optional[List[str]] = None
    required_experience: Optional[str] = None
    certifications: Optional[List[str]] = None
    additional_requirements: Optional[List[str]] = None
    status: str
    is_active: bool
    company_id: int
    created_by: int
    approved_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    requirements: List[JobRequirementResponse] = []
    
    class Config:
        from_attributes = True

class JobGenerateFieldsRequest(BaseModel):
    project_name: str
    role_title: str
    role_description: str

class JobGenerateFieldsResponse(BaseModel):
    key_skills: List[str]
    required_experience: str
    certifications: List[str]
    additional_requirements: List[str]
    
class JobGenerateDescriptionRequest(BaseModel):
    project_name: str
    role_title: str
    role_description: str
    key_skills: List[str]
    required_experience: str
    certifications: List[str]
    additional_requirements: List[str]

class JobGenerateDescriptionResponse(BaseModel):
    description: str
    short_description: str

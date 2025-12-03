from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.job import Job, JobRequirement
from ..models.user import User
from ..schemas.job import (
    JobCreate, JobResponse, JobUpdate, JobGenerateFieldsRequest, 
    JobGenerateFieldsResponse, JobGenerateDescriptionRequest, JobGenerateDescriptionResponse
)
from ..services.llm_service import LLMService
from .auth import get_current_user
from datetime import datetime

router = APIRouter()
llm_service = LLMService()

@router.post("/generate-fields", response_model=JobGenerateFieldsResponse)
async def generate_job_fields(
    request: JobGenerateFieldsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate additional job fields using AI"""
    if current_user.user_type not in ["account_manager", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Account Managers can generate job fields"
        )
    
    result = await llm_service.generate_job_fields(
        request.project_name,
        request.role_title,
        request.role_description
    )
    
    return JobGenerateFieldsResponse(**result)

@router.post("/generate-description", response_model=JobGenerateDescriptionResponse)
async def generate_job_description(
    request: JobGenerateDescriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate complete job description using AI"""
    if current_user.user_type not in ["account_manager", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Account Managers can generate job descriptions"
        )
    
    result = await llm_service.generate_job_description(
        request.project_name,
        request.role_title,
        request.role_description,
        request.key_skills,
        request.required_experience,
        request.certifications,
        request.additional_requirements
    )
    
    return JobGenerateDescriptionResponse(**result)

@router.post("/", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new job posting"""
    if current_user.user_type not in ["account_manager", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Account Managers can create jobs"
        )
    
    # Handle company assignment
    company_id = current_user.company_id
    
    # If user doesn't have a company assigned, assign the first available company
    # This is a temporary solution for users created without company assignment
    if company_id is None:
        from ..models.company import Company
        first_company = db.query(Company).first()
        if not first_company:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No companies available. Please create a company first."
            )
        company_id = first_company.id
        
        # Optionally update the user's company_id for future use
        current_user.company_id = company_id
        db.commit()
    
    # Create job
    db_job = Job(
        title=job_data.title,
        description=job_data.description,
        short_description=job_data.short_description,
        department=job_data.department,
        location=job_data.location,
        job_type=job_data.job_type,
        experience_level=job_data.experience_level,
        salary_range=job_data.salary_range,
        company_id=company_id,
        created_by=current_user.id,
        status="pending_approval"  # Jobs need HR approval before publishing
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    
    return JobResponse.from_orm(db_job)

@router.get("/", response_model=List[JobResponse])
async def get_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None),
    created_by_me: bool = Query(False),
    department: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get jobs based on user role and filters"""
    query = db.query(Job)
    
    # Filter by company for non-admin users
    if current_user.user_type != "admin":
        query = query.filter(Job.company_id == current_user.company_id)
    
    # Filter by creator if requested
    if created_by_me:
        query = query.filter(Job.created_by == current_user.id)
    
    # Filter by status
    if status_filter:
        query = query.filter(Job.status == status_filter)
    
    # Filter by department
    if department:
        query = query.filter(Job.department.ilike(f"%{department}%"))
    
    # Filter by job_type
    if job_type:
        query = query.filter(Job.job_type == job_type)
    
    # Filter by experience_level
    if experience_level:
        query = query.filter(Job.experience_level == experience_level)
    
    # Role-based filtering
    if current_user.user_type == "account_manager":
        # Account managers see jobs they created or all company jobs
        if not created_by_me:
            query = query.filter(Job.created_by == current_user.id)
    elif current_user.user_type == "hr":
        # HR sees all jobs in their company
        pass
    
    jobs = query.offset(skip).limit(limit).all()
    return [JobResponse.from_orm(job) for job in jobs]

@router.get("/public", response_model=List[JobResponse])
async def get_public_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get published jobs for public careers page"""
    query = db.query(Job).filter(
        Job.status == "published",
        Job.is_active == True
    )
    
    # Apply filters
    if department:
        query = query.filter(Job.department.ilike(f"%{department}%"))
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if job_type:
        query = query.filter(Job.job_type == job_type)
    
    jobs = query.offset(skip).limit(limit).all()
    return [JobResponse.from_orm(job) for job in jobs]

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check permissions
    if current_user.user_type not in ["admin"] and job.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return JobResponse.from_orm(job)

@router.get("/public/{job_id}", response_model=JobResponse)
async def get_public_job(job_id: int, db: Session = Depends(get_db)):
    """Get a published job for public view"""
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.status == "published",
        Job.is_active == True
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or not published"
        )
    
    return JobResponse.from_orm(job)

@router.get("/similar/{job_id}", response_model=List[JobResponse])
async def get_similar_jobs(
    job_id: int,
    limit: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get similar jobs for autofill suggestions"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check permissions
    if current_user.user_type != "admin" and job.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Find similar jobs based on department, job_type, or experience_level
    query = db.query(Job).filter(
        Job.id != job_id,
        Job.company_id == job.company_id
    )
    
    # Prioritize jobs with similar department, job_type, or experience_level
    similar_jobs = []
    
    # First try to find jobs with same department
    if job.department:
        dept_jobs = query.filter(Job.department == job.department).limit(limit).all()
        similar_jobs.extend(dept_jobs)
    
    # Then try same job_type
    if job.job_type and len(similar_jobs) < limit:
        existing_ids = [j.id for j in similar_jobs]
        type_query = query.filter(Job.job_type == job.job_type)
        if existing_ids:
            type_query = type_query.filter(~Job.id.in_(existing_ids))
        type_jobs = type_query.limit(limit - len(similar_jobs)).all()
        similar_jobs.extend(type_jobs)
    
    # Then try same experience_level
    if job.experience_level and len(similar_jobs) < limit:
        existing_ids = [j.id for j in similar_jobs]
        level_query = query.filter(Job.experience_level == job.experience_level)
        if existing_ids:
            level_query = level_query.filter(~Job.id.in_(existing_ids))
        level_jobs = level_query.limit(limit - len(similar_jobs)).all()
        similar_jobs.extend(level_jobs)
    
    # Fill remaining with any other jobs from same company
    if len(similar_jobs) < limit:
        existing_ids = [j.id for j in similar_jobs]
        other_query = query
        if existing_ids:
            other_query = other_query.filter(~Job.id.in_(existing_ids))
        other_jobs = other_query.limit(limit - len(similar_jobs)).all()
        similar_jobs.extend(other_jobs)
    
    return [JobResponse.from_orm(j) for j in similar_jobs[:limit]]

@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Prevent editing published jobs
    if job.status == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit a published job. Please unpublish it first or create a new job posting."
        )
    
    # Check permissions
    if current_user.user_type == "account_manager" and job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit jobs you created"
        )
    elif current_user.user_type not in ["account_manager", "hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Update job fields
    update_data = job_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    db.commit()
    db.refresh(job)
    
    return JobResponse.from_orm(job)

@router.patch("/{job_id}/approve")
async def approve_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a job (HR only)"""
    if current_user.user_type not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR can approve jobs"
        )
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status in ["approved", "published"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is already approved or published"
        )
    
    job.status = "approved"
    job.approved_by = current_user.id
    job.approved_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Job approved successfully. Use the publish option to make it visible on careers page."}

@router.patch("/{job_id}/publish")
async def publish_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish a job to careers page (HR only)"""
    if current_user.user_type not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR can publish jobs"
        )
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    if job.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job must be approved before publishing"
        )
    
    job.status = "published"
    job.published_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Job published successfully"}

@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check permissions
    if current_user.user_type == "account_manager" and job.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete jobs you created"
        )
    elif current_user.user_type not in ["account_manager", "hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    db.delete(job)
    db.commit()
    
    return {"message": "Job deleted successfully"}

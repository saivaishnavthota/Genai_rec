from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import Optional
import os
import logging

from ..database import get_db
from ..models.application import Application
from ..models.resume_update_tracking import ResumeUpdateRequest, ResumeUpdateHistory
from ..services.resume_update_service import resume_update_service
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resume-update", tags=["Resume Update"])

@router.get("/status/{reference_number}")
async def get_resume_update_status(
    reference_number: str,
    db: Session = Depends(get_db)
):
    """Get resume update status for a candidate by reference number"""
    try:
        # Find application by reference number
        application = db.query(Application).filter_by(reference_number=reference_number).first()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found with this reference number"
            )
        
        # Check if there's an active resume update request
        update_request = db.query(ResumeUpdateRequest).filter_by(application_id=application.id).first()
        
        if not update_request:
            return {
                "eligible_for_update": False,
                "message": "No resume update opportunity available for this application"
            }
        
        # Get update history
        update_history = db.query(ResumeUpdateHistory).filter_by(
            update_request_id=update_request.id
        ).order_by(ResumeUpdateHistory.attempt_number.desc()).all()
        
        # Get current score
        current_score = application.scores[-1].final_score if application.scores else 0
        
        # Determine current status and eligibility
        can_update = (
            update_request.status in ["llm_approved", "email_sent"] and
            update_request.update_attempts_count < update_request.max_attempts
        )
        
        response_data = {
            "eligible_for_update": can_update,
            "application": {
                "reference_number": application.reference_number,
                "candidate_name": application.full_name,
                "job_title": application.job.title,
                "current_score": current_score,
                "threshold_needed": settings.shortlist_threshold,
                "status": application.status
            },
            "update_request": {
                "status": update_request.status,
                "attempts_used": update_request.update_attempts_count,
                "max_attempts": update_request.max_attempts,
                "attempts_remaining": update_request.max_attempts - update_request.update_attempts_count,
                "llm_evaluation_result": update_request.llm_evaluation_result,
                "llm_evaluation_reason": update_request.llm_evaluation_reason,
                "last_email_sent": update_request.last_email_sent_at.isoformat() if update_request.last_email_sent_at else None,
                "next_email_due": update_request.next_email_due_at.isoformat() if update_request.next_email_due_at else None
            },
            "update_history": [
                {
                    "attempt_number": history.attempt_number,
                    "email_sent_at": history.email_sent_at.isoformat(),
                    "resume_updated": history.resume_updated,
                    "resume_updated_at": history.resume_updated_at.isoformat() if history.resume_updated_at else None,
                    "old_score": history.old_score,
                    "new_score": history.new_score,
                    "score_improvement": history.score_improvement,
                    "status": history.status
                }
                for history in update_history
            ]
        }
        
        # Add appropriate message based on status
        if update_request.status == "llm_rejected":
            response_data["message"] = "Unfortunately, your application was not selected for the resume update opportunity."
        elif update_request.status == "completed_success":
            response_data["message"] = f"Congratulations! Your updated resume achieved a score of {update_request.final_score_achieved:.1f} and you have been selected for the next steps."
        elif update_request.status == "completed_failure":
            response_data["message"] = f"You have used all available attempts. Your final score was {update_request.final_score_achieved:.1f}."
        elif can_update:
            response_data["message"] = f"You can update your resume to improve your score. Current score: {current_score:.1f}, Target: {settings.shortlist_threshold}"
        else:
            response_data["message"] = "Resume update opportunity is not currently available."
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error getting resume update status for {reference_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving resume update status"
        )

@router.post("/upload/{reference_number}")
async def upload_updated_resume(
    reference_number: str,
    resume: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload updated resume for a candidate"""
    try:
        # Find application by reference number
        application = db.query(Application).filter_by(reference_number=reference_number).first()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found with this reference number"
            )
        
        # Check if there's an active resume update request
        update_request = db.query(ResumeUpdateRequest).filter_by(application_id=application.id).first()
        
        if not update_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No resume update opportunity available for this application"
            )
        
        # Check if candidate can still update
        if (update_request.status not in ["llm_approved", "email_sent"] or 
            update_request.update_attempts_count >= update_request.max_attempts):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume update opportunity has expired or maximum attempts reached"
            )
        
        # Validate file type
        if not resume.filename.lower().endswith(('.pdf', '.doc', '.docx')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF, DOC, and DOCX files are allowed"
            )
        
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        import uuid
        file_extension = os.path.splitext(resume.filename)[1]
        unique_filename = f"{application.reference_number}_updated_{uuid.uuid4().hex[:8]}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await resume.read()
            buffer.write(content)
        
        # Process the updated resume
        result = await resume_update_service.process_resume_update(
            db, application, file_path, unique_filename
        )
        
        if result["success"]:
            logger.info(f"Resume updated successfully for application {application.id}")
            return {
                "success": True,
                "message": result["message"],
                "old_score": result.get("old_score"),
                "new_score": result.get("new_score"),
                "score_improvement": result.get("improvement"),
                "threshold_achieved": result.get("threshold_achieved", False),
                "attempts_remaining": result.get("attempts_remaining", 0),
                "final_rejection": result.get("final_rejection", False)
            }
        else:
            # Clean up file if processing failed
            try:
                os.remove(file_path)
            except:
                pass
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Error processing resume update")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading updated resume for {reference_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading resume"
        )

@router.get("/guidelines")
async def get_resume_improvement_guidelines():
    """Get guidelines for improving resume"""
    return {
        "guidelines": {
            "formatting": [
                "Use a clean, professional format with consistent fonts and spacing",
                "Include clear section headers (Experience, Education, Skills, etc.)",
                "Use bullet points for achievements and responsibilities",
                "Keep the resume to 1-2 pages maximum",
                "Save as PDF to preserve formatting"
            ],
            "content": [
                "Include relevant keywords from the job description",
                "Quantify achievements with specific numbers and metrics",
                "Focus on accomplishments rather than just job duties",
                "Highlight technical skills and certifications relevant to the role",
                "Include education, certifications, and professional development"
            ],
            "experience": [
                "List work experience in reverse chronological order",
                "Use action verbs to start bullet points (Developed, Managed, Implemented)",
                "Include company names, job titles, and employment dates",
                "Describe impact and results of your work",
                "Tailor experience descriptions to match job requirements"
            ],
            "skills": [
                "Create a dedicated skills section with relevant technical skills",
                "Include programming languages, tools, and technologies",
                "Mention soft skills that are relevant to the role",
                "Group skills by category (Programming, Databases, Tools, etc.)",
                "Be honest about your skill levels"
            ],
            "common_mistakes": [
                "Spelling and grammatical errors",
                "Using generic job descriptions",
                "Including irrelevant personal information",
                "Poor formatting and inconsistent styling",
                "Missing contact information or outdated details"
            ]
        },
        "ats_optimization": {
            "keywords": "Include relevant keywords from the job posting naturally throughout your resume",
            "file_format": "Use PDF format to ensure consistent formatting across different systems",
            "section_headers": "Use standard section headers like 'Experience', 'Education', 'Skills'",
            "fonts": "Use standard fonts like Arial, Calibri, or Times New Roman",
            "file_naming": "Name your file professionally: 'FirstName_LastName_Resume.pdf'"
        }
    }

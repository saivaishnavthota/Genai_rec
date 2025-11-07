from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.interviewer_token import InterviewerToken
from ..models.application import Application
from ..models.interview_review import InterviewReview
from pydantic import BaseModel
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models
class InterviewerLoginRequest(BaseModel):
    token: str

class InterviewerLoginResponse(BaseModel):
    success: bool
    message: str
    interviewer_name: str
    interviewer_email: str
    application_id: int
    candidate_name: str
    job_title: str
    interviewer_type: str

class InterviewReviewSubmission(BaseModel):
    technical_skills: int  # 1-10 scale
    communication: int     # 1-10 scale
    problem_solving: int   # 1-10 scale
    cultural_fit: int      # 1-10 scale
    leadership_potential: int  # 1-10 scale
    overall_rating: int    # 1-10 scale
    strengths: str
    areas_for_improvement: str
    recommendation: str    # 'hire', 'reject', 'maybe'
    additional_comments: Optional[str] = None

@router.post("/login", response_model=InterviewerLoginResponse)
async def interviewer_login(
    request: InterviewerLoginRequest,
    db: Session = Depends(get_db)
):
    """Validate interviewer token and provide access to review form"""
    
    try:
        # Find the token
        token_record = db.query(InterviewerToken).filter(
            InterviewerToken.token == request.token
        ).first()
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired token"
            )
        
        # Check if token is valid
        if not token_record.is_valid():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired or already been used"
            )
        
        # Get application details
        application = db.query(Application).filter(
            Application.id == token_record.application_id
        ).first()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        return InterviewerLoginResponse(
            success=True,
            message="Login successful",
            interviewer_name=token_record.interviewer_name,
            interviewer_email=token_record.interviewer_email,
            application_id=token_record.application_id,
            candidate_name=application.full_name,
            job_title=application.job.title,
            interviewer_type=token_record.interviewer_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during interviewer login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/submit-review/{token}")
async def submit_interview_review(
    token: str,
    review: InterviewReviewSubmission,
    db: Session = Depends(get_db)
):
    """Submit interview review using temporary token"""
    
    try:
        # Find and validate token
        token_record = db.query(InterviewerToken).filter(
            InterviewerToken.token == token
        ).first()
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired token"
            )
        
        if not token_record.is_valid():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired or already been used"
            )
        
        # Check if review already exists for this interviewer
        existing_review = db.query(InterviewReview).filter(
            InterviewReview.application_id == token_record.application_id,
            InterviewReview.interviewer_email == token_record.interviewer_email
        ).first()
        
        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review has already been submitted for this application"
            )
        
        # Create new review record
        interview_review = InterviewReview(
            application_id=token_record.application_id,
            interviewer_email=token_record.interviewer_email,
            interviewer_name=token_record.interviewer_name,
            interviewer_type=token_record.interviewer_type,
            technical_score=review.technical_skills,
            communication_score=review.communication,
            problem_solving_score=review.problem_solving,
            cultural_fit_score=review.cultural_fit,
            leadership_potential=review.leadership_potential,
            overall_rating=review.overall_rating,
            overall_recommendation=review.recommendation,
            strengths=review.strengths,
            areas_for_improvement=review.areas_for_improvement,
            additional_comments=review.additional_comments,
            review_submitted_at=datetime.utcnow()
        )
        
        db.add(interview_review)
        
        # Mark token as used
        token_record.mark_used()
        
        # Update application status - since we just added a review, change to review_received
        application = db.query(Application).filter(
            Application.id == token_record.application_id
        ).first()
        
        if application:
            # Always update to review_received when any review is submitted
            application.status = "review_received"
            logger.info(f"Updated application {application.id} status to review_received")
        
        db.commit()
        
        return {
            "success": True,
            "message": "Review submitted successfully",
            "review_id": interview_review.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting interview review: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit review"
        )

@router.get("/review-form/{token}")
async def get_review_form_data(
    token: str,
    db: Session = Depends(get_db)
):
    """Get data needed for the review form"""
    
    try:
        # Find and validate token
        token_record = db.query(InterviewerToken).filter(
            InterviewerToken.token == token
        ).first()
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired token"
            )
        
        if not token_record.is_valid():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired or already been used"
            )
        
        # Get application details
        application = db.query(Application).filter(
            Application.id == token_record.application_id
        ).first()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Check if review already submitted
        existing_review = db.query(InterviewReview).filter(
            InterviewReview.application_id == token_record.application_id,
            InterviewReview.interviewer_email == token_record.interviewer_email
        ).first()
        
        return {
            "candidate_name": application.full_name,
            "candidate_email": application.email,
            "job_title": application.job.title,
            "interviewer_name": token_record.interviewer_name,
            "interviewer_type": token_record.interviewer_type,
            "review_submitted": existing_review is not None,
            "token_expires_at": token_record.expires_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review form data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

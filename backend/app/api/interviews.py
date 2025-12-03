from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.application import Application
from ..models.interview_schedule import InterviewSchedule
from ..models.interview_review import InterviewReview
from ..models.user import User
from ..services.interview_service import InterviewService
from ..services.review_processing_service import ReviewProcessingService
from .auth import get_current_user
from pydantic import BaseModel
import logging

router = APIRouter()
interview_service = InterviewService()
review_service = ReviewProcessingService()
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class SlotSelectionRequest(BaseModel):
    selected_date: str  # YYYY-MM-DD format
    selected_time: str  # HH:MM format

class InterviewScheduleRequest(BaseModel):
    primary_interviewer_name: str
    primary_interviewer_email: str
    backup_interviewer_name: str
    backup_interviewer_email: str

class ReviewEmailData(BaseModel):
    from_email: str
    subject: str
    body: str

class FetchAvailabilityRequest(BaseModel):
    from_date: Optional[str] = None  # ISO format date string
    to_date: Optional[str] = None    # ISO format date string

@router.post("/fetch-availability/{application_id}")
async def fetch_availability(
    application_id: int,
    date_range: Optional[FetchAvailabilityRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """HR clicks 'Fetch Availability' - generate and send slots to candidate"""
    
    # Check permissions
    if current_user.user_type not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin can fetch availability"
        )
    
    # Get application and check permissions
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check company permissions
    if current_user.user_type != "admin" and application.job.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if application is in correct status for fetching availability
    # Allow shortlisted applications or those already in availability_requested status
    valid_statuses = ["shortlisted", "selected", "availability_requested"]
    if application.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application must be in one of {valid_statuses} status, currently: {application.status}"
        )
    
    try:
        # Extract date range if provided
        from_date = None
        to_date = None
        if date_range and date_range.from_date and date_range.to_date:
            from datetime import datetime
            # Handle ISO format strings (with or without timezone)
            try:
                # Try parsing with timezone first
                if 'Z' in date_range.from_date or '+' in date_range.from_date or date_range.from_date.count(':') > 1:
                    from_date = datetime.fromisoformat(date_range.from_date.replace('Z', '+00:00')).date()
                    to_date = datetime.fromisoformat(date_range.to_date.replace('Z', '+00:00')).date()
                else:
                    # Parse as date-only string (YYYY-MM-DD)
                    from_date = datetime.fromisoformat(date_range.from_date).date()
                    to_date = datetime.fromisoformat(date_range.to_date).date()
            except ValueError:
                # Fallback: try parsing as date string
                from_date = datetime.strptime(date_range.from_date.split('T')[0], '%Y-%m-%d').date()
                to_date = datetime.strptime(date_range.to_date.split('T')[0], '%Y-%m-%d').date()
        
        result = await interview_service.fetch_availability_slots(db, application_id, from_date, to_date)
        
        if result["success"]:
            return {
                "message": result["message"],
                "slots_count": result["slots_count"],
                "slots_from": result["slots_from"],
                "slots_to": result["slots_to"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
            
    except Exception as e:
        logger.error(f"Error fetching availability for application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing availability request"
        )

@router.get("/available-slots/{application_id}")
async def get_available_slots(
    application_id: int,
    db: Session = Depends(get_db)
):
    """Get generated slots for an application (public endpoint for candidates)"""
    
    # This is a public endpoint for candidates to view their interview slots
    # No authentication required as candidates don't have accounts
    
    interview_schedule = db.query(InterviewSchedule).filter(
        InterviewSchedule.application_id == application_id
    ).first()
    
    if not interview_schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No available slots found. Please ensure you have a valid link or contact HR."
        )
    
    # Only return slots if they haven't been selected yet
    if interview_schedule.selected_slot_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview slot has already been selected for this application."
        )
    
    return {
        "application_id": application_id,
        "available_slots": interview_schedule.available_slots,
        "slots_generated_from": interview_schedule.slots_generated_from,
        "slots_generated_to": interview_schedule.slots_generated_to,
        "message": "Available slots retrieved successfully"
    }

@router.post("/select-slot/{application_id}")
async def select_slot(
    application_id: int,
    slot_data: SlotSelectionRequest,
    db: Session = Depends(get_db)
):
    """Candidate selects interview slot (public endpoint with token)"""
    
    # This is a public endpoint for candidates to select slots
    # In a production system, you'd want to add token-based authentication
    
    try:
        result = await interview_service.process_slot_selection(
            db, 
            application_id, 
            slot_data.selected_date, 
            slot_data.selected_time
        )
        
        if result["success"]:
            return {
                "message": result["message"],
                "selected_date": result["selected_date"],
                "selected_time": result["selected_time"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
            
    except Exception as e:
        logger.error(f"Error selecting slot for application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing slot selection"
        )

@router.post("/schedule-interview/{application_id}")
async def schedule_interview(
    application_id: int,
    interview_data: InterviewScheduleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """HR schedules interview with interviewers"""
    
    # Check permissions
    if current_user.user_type not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin can schedule interviews"
        )
    
    # Get application and check permissions
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check company permissions
    if current_user.user_type != "admin" and application.job.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if application is in correct status
    if application.status != "slot_selected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application must be in 'slot_selected' status, currently: {application.status}"
        )
    
    try:
        interviewer_data = {
            "primary_interviewer_name": interview_data.primary_interviewer_name,
            "primary_interviewer_email": interview_data.primary_interviewer_email,
            "backup_interviewer_name": interview_data.backup_interviewer_name,
            "backup_interviewer_email": interview_data.backup_interviewer_email
        }
        
        result = await interview_service.schedule_interview(db, application_id, interviewer_data)
        
        if result["success"]:
            return {
                "message": result["message"],
                "interview_details": result["interview_details"],
                "emails_sent": result["emails_sent"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
            
    except Exception as e:
        logger.error(f"Error scheduling interview for application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error scheduling interview"
        )

@router.patch("/mark-completed/{application_id}")
async def mark_interview_completed(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """HR marks interview as completed"""
    
    # Check permissions
    if current_user.user_type not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin can mark interviews as completed"
        )
    
    # Get application and check permissions
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check company permissions
    if current_user.user_type != "admin" and application.job.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if application is in correct status
    if application.status != "interview_confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application must be in 'interview_confirmed' status, currently: {application.status}"
        )
    
    try:
        result = await interview_service.mark_interview_completed(db, application_id)
        
        if result["success"]:
            return {"message": result["message"]}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
            
    except Exception as e:
        logger.error(f"Error marking interview completed for application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error marking interview as completed"
        )

@router.get("/details/{application_id}")
async def get_interview_details(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get interview details for an application"""
    
    # Check permissions
    if current_user.user_type not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin can view interview details"
        )
    
    # Get application and check permissions
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check company permissions
    if current_user.user_type != "admin" and application.job.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    interview_details = interview_service.get_interview_details(db, application_id)
    
    if not interview_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview details not found"
        )
    
    return interview_details

@router.post("/process-review")
async def process_review_email(
    review_data: ReviewEmailData,
    db: Session = Depends(get_db)
):
    """Process incoming review email from interviewer (webhook endpoint)"""
    
    # This would typically be called by an email webhook service
    # In production, you'd want to add proper authentication/validation
    
    try:
        email_data = {
            "from_email": review_data.from_email,
            "subject": review_data.subject,
            "body": review_data.body
        }
        
        result = await review_service.process_review_email(db, email_data)
        
        return {
            "success": result["success"],
            "message": result["message"],
            "parsed_data": result.get("parsed_data")
        }
        
    except Exception as e:
        logger.error(f"Error processing review email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing review email"
        )

@router.get("/review-template/{application_id}")
async def get_review_template(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get review template for interviewer"""
    
    # Check permissions
    if current_user.user_type not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin can get review templates"
        )
    
    # Get application
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    template = review_service.get_review_template(
        application.full_name,
        application.job.title
    )
    
    return {
        "template": template,
        "candidate_name": application.full_name,
        "job_title": application.job.title
    }

@router.get("/review/{application_id}")
async def get_interview_review(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get interview review for an application"""
    
    # Check permissions
    if current_user.user_type not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin can view interview reviews"
        )
    
    # Get application and check permissions
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check company permissions
    if current_user.user_type != "admin" and application.job.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get interview review
    review = db.query(InterviewReview).filter(
        InterviewReview.application_id == application_id
    ).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview review not found"
        )
    
    return {
        "id": review.id,
        "application_id": review.application_id,
        "interviewer_email": review.interviewer_email,
        "technical_score": review.technical_score,
        "communication_score": review.communication_score,
        "problem_solving_score": review.problem_solving_score,
        "cultural_fit_score": review.cultural_fit_score,
        "leadership_potential": review.leadership_potential,
        "overall_recommendation": review.overall_recommendation,
        "strengths": review.strengths,
        "areas_for_improvement": review.areas_for_improvement,
        "additional_comments": review.additional_comments,
        "is_valid_format": review.is_valid_format,
        "review_received_at": review.review_received_at,
        "processed_at": review.processed_at
    }

@router.post("/send-review-tokens/{application_id}")
async def send_review_tokens(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send review tokens to interviewers after interview completion"""
    
    # Check permissions
    if current_user.user_type not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin can send review tokens"
        )
    
    # Get application and check permissions
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check company permissions
    if current_user.user_type != "admin" and application.job.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        result = await interview_service.send_review_tokens_after_interview(db, application_id)
        
        if result["success"]:
            return {
                "message": result["message"],
                "tokens_created": result["tokens_created"],
                "emails_sent": result["emails_sent"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
            
    except Exception as e:
        logger.error(f"Error sending review tokens for application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending review tokens"
        )

@router.get("/reviews/{application_id}")
async def get_all_interview_reviews(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all interview reviews for an application"""
    
    # Check permissions
    if current_user.user_type not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin can view interview reviews"
        )
    
    # Get application and check permissions
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check company permissions
    if current_user.user_type != "admin" and application.job.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Get all reviews for this application
        from ..models.interview_review import InterviewReview
        reviews = db.query(InterviewReview).filter(
            InterviewReview.application_id == application_id
        ).all()
        
        return {
            "application_id": application_id,
            "reviews": [format_review_response(review) for review in reviews],
            "review_count": len(reviews)
        }
        
    except Exception as e:
        logger.error(f"Error getting interview reviews for application {application_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting interview reviews"
        )

def format_review_response(review):
    """Format interview review for API response"""
    if not review:
        return None
    
    return {
        "id": review.id,
        "interviewer_email": review.interviewer_email,
        "interviewer_name": review.interviewer_name,
        "interviewer_type": review.interviewer_type,
        "technical_score": review.technical_score,
        "communication_score": review.communication_score,
        "problem_solving_score": review.problem_solving_score,
        "cultural_fit_score": review.cultural_fit_score,
        "leadership_potential": review.leadership_potential,
        "overall_rating": review.overall_rating,
        "overall_recommendation": review.overall_recommendation,
        "strengths": review.strengths,
        "areas_for_improvement": review.areas_for_improvement,
        "additional_comments": review.additional_comments,
        "review_submitted_at": review.review_submitted_at,
        "created_at": review.created_at
    }

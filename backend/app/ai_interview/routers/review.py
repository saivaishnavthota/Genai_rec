"""Review router for HR decisions"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from ...database import get_db
from ...api.auth import get_current_user
from ...models.user import User
from ..schemas.scoring import ReviewDecisionRequest
from ..models.ai_sessions import AISession, Recommendation
from ..services.interview_service import InterviewService
from ..services.storage_service import StorageService
from ..services.asr_service import ASRService
from ..services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()

_storage_service = StorageService()
_asr_service = ASRService()
_rag_service = RAGService()
_interview_service = InterviewService(_storage_service, _asr_service, _rag_service)


@router.post("/{session_id}/decision", status_code=status.HTTP_200_OK)
async def set_review_decision(
    session_id: int,
    request: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set HR review decision for a session
    
    Auth: HR/Admin only
    
    Body:
    - status: PASS | REVIEW | FAIL
    - notes: Optional review notes
    """
    if current_user.user_type not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin can set review decisions"
        )
    
    try:
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Map status string to Recommendation enum
        status_map = {
            "PASS": Recommendation.PASS,
            "REVIEW": Recommendation.REVIEW,
            "FAIL": Recommendation.FAIL
        }
        
        recommendation = status_map.get(request.status.upper())
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {request.status}"
            )
        
        # Update session
        session.recommendation = recommendation
        
        # Update report_json with notes
        if not session.report_json:
            session.report_json = {}
        session.report_json["review_notes"] = request.notes
        session.report_json["reviewed_by"] = current_user.email
        session.report_json["reviewed_at"] = str(datetime.utcnow())
        
        db.commit()
        db.refresh(session)
        
        return {
            "status": "success",
            "session_id": session_id,
            "recommendation": recommendation.value
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set review decision: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


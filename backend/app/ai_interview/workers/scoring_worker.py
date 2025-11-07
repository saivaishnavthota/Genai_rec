"""Background worker for scoring interviews"""
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from ...database import SessionLocal
from ..services.interview_service import InterviewService
from ..services.storage_service import StorageService
from ..services.asr_service import ASRService
from ..services.rag_service import RAGService

logger = logging.getLogger(__name__)


class ScoringWorker:
    """Background worker for scoring interviews"""
    
    def __init__(self):
        self.storage = StorageService()
        self.asr = ASRService()
        self.rag = RAGService()
        self.interview_service = InterviewService(self.storage, self.asr, self.rag)
    
    async def score_session(self, session_id: int):
        """
        Score an interview session
        
        Args:
            session_id: Session ID to score
        """
        db = SessionLocal()
        try:
            from ..models.ai_sessions import AISession
            
            session = db.query(AISession).filter(AISession.id == session_id).first()
            if not session:
                logger.error(f"Session {session_id} not found")
                return
            
            if session.status != "finalizing":
                logger.warning(f"Session {session_id} not in finalizing state")
                return
            
            # Get transcript
            if not session.transcript_url:
                logger.error(f"No transcript available for session {session_id}")
                return
            
            # Load transcript
            transcript_path = self.storage.get_transcript_path(session_id)
            # TODO: Download transcript from storage
            transcript_text = ""  # Placeholder
            
            # Score using RAG
            scores = await self.rag.score_interview(
                db,
                transcript_text,
                session_id,
                session.job_id
            )
            
            # Update session
            session.total_score = scores.final_score
            session.report_json = {
                "scores": scores.model_dump(),
                "scored_at": str(datetime.utcnow())
            }
            
            # Calculate recommendation
            recommendation = self.interview_service.calculate_recommendation(db, session_id)
            session.recommendation = recommendation
            session.status = "completed"
            
            db.commit()
            logger.info(f"Scored session {session_id}: {scores.final_score}")
        except Exception as e:
            logger.error(f"Failed to score session {session_id}: {e}")
            db.rollback()
        finally:
            db.close()


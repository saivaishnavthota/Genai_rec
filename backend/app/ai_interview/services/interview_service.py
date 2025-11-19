"""Interview service for managing AI interview sessions"""
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ...config import settings
from ..models.ai_sessions import AISession, SessionStatus, Recommendation, AISessionFlag, FlagSeverity
from ..schemas.sessions import SessionCreate, SessionOut, SessionReportOut
from ..schemas.scoring import ScoreOut
from .storage_service import StorageService
from .asr_service import ASRService
from .rag_service import RAGService

logger = logging.getLogger(__name__)


class InterviewService:
    """Service for managing AI interview sessions"""
    
    def __init__(
        self,
        storage_service: StorageService,
        asr_service: ASRService,
        rag_service: RAGService
    ):
        self.storage = storage_service
        self.asr = asr_service
        self.rag = rag_service
    
    def create_session(
        self,
        db: Session,
        application_id: int,
        job_id: int
    ) -> AISession:
        """
        Create a new AI interview session
        
        Args:
            db: Database session
            application_id: Application ID (candidate)
            job_id: Job ID
            
        Returns:
            Created AISession
        """
        session = AISession(
            application_id=application_id,
            job_id=job_id,
            status=SessionStatus.CREATED,
            policy_version=settings.policy_version,
            rubric_version=settings.rubric_version
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        logger.info(f"Created AI session {session.id} for application {application_id}")
        return session
    
    def start_session(self, db: Session, session_id: int) -> AISession:
        """Start an interview session"""
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.status != SessionStatus.CREATED:
            raise ValueError(f"Session {session_id} cannot be started from status {session.status}")
        
        session.status = SessionStatus.LIVE
        session.started_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        return session
    
    def end_session(self, db: Session, session_id: int, video_url: Optional[str] = None) -> AISession:
        """
        End an interview session (idempotent)
        
        Args:
            db: Database session
            session_id: Session ID
            video_url: Optional video URL to save
            
        Returns:
            Updated AISession
        """
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.status == SessionStatus.COMPLETED:
            return session  # Already completed
        
        session.status = SessionStatus.FINALIZING
        session.ended_at = datetime.utcnow()
        
        # Save video URL if provided
        if video_url:
            session.video_url = video_url
        else:
            # Try to set default video path
            video_path = f"sessions/{session_id}/raw.mp4"
            session.video_url = video_path
        
        db.commit()
        db.refresh(session)
        
        # TODO: Enqueue scoring job
        logger.info(f"Session {session_id} ended, finalizing...")
        return session
    
    def get_report(
        self,
        db: Session,
        session_id: int
    ) -> SessionReportOut:
        """
        Get full session report
        
        Args:
            db: Database session
            session_id: Session ID
            
        Returns:
            SessionReportOut with flags, transcript, scores
        """
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get flags
        flags = db.query(AISessionFlag).filter(
            AISessionFlag.session_id == session_id
        ).order_by(AISessionFlag.t_start).all()
        
        # Get transcript - try multiple paths
        transcript = None
        transcript_path = None
        
        # Try to get transcript from session.transcript_url first
        if session.transcript_url:
            transcript_path = session.transcript_url
        else:
            # Try default path
            transcript_path = self.storage.get_transcript_path(session_id)
        
        logger.debug(f"Attempting to load transcript for session {session_id} from: {transcript_path}")
        
        try:
            import tempfile
            import json
            import os
            
            tmp_path = None
            
            try:
                # Create temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                    tmp_path = tmp.name
                
                # Download transcript from storage
                if self.storage.is_available() and transcript_path:
                    try:
                        if not self.storage.client:
                            raise RuntimeError("Storage client not available")
                        logger.debug(f"Downloading transcript from storage: {transcript_path}")
                        self.storage.download_file(transcript_path, tmp_path)
                        logger.debug(f"Successfully downloaded transcript")
                    except (RuntimeError, Exception) as e:
                        logger.warning(f"Failed to download transcript from storage: {e}")
                        # Try alternative path
                        alt_path = f"sessions/{session_id}/artifacts/transcript.json"
                        try:
                            self.storage.download_file(alt_path, tmp_path)
                            logger.debug(f"Downloaded transcript from alternative path: {alt_path}")
                        except Exception as e2:
                            logger.warning(f"Alternative path also failed: {e2}")
                            # If storage not available, try to use transcript_url as direct path
                            if session.transcript_url and os.path.exists(session.transcript_url):
                                tmp_path = session.transcript_url
                                logger.debug(f"Using local file path: {tmp_path}")
                            else:
                                logger.warning(f"Transcript not available from storage or local path. Tried: {transcript_path}, {alt_path}")
                                raise
                
                # Load transcript JSON
                if tmp_path and os.path.exists(tmp_path):
                    file_size = os.path.getsize(tmp_path)
                    logger.debug(f"Loading transcript file: {tmp_path} ({file_size} bytes)")
                    with open(tmp_path, 'r', encoding='utf-8') as f:
                        transcript = json.load(f)
                    # Ensure transcript has segments format
                    if isinstance(transcript, dict) and 'segments' in transcript:
                        transcript = transcript
                    elif isinstance(transcript, dict) and 'text' in transcript:
                        # Convert text to segments format
                        transcript = {'segments': [{'text': transcript['text'], 'start': 0, 'end': 0}]}
                    elif isinstance(transcript, list):
                        transcript = {'segments': transcript}
                    else:
                        # Convert to segments format if needed
                        transcript = {'segments': transcript if isinstance(transcript, list) else []}
                    logger.debug(f"Loaded transcript with {len(transcript.get('segments', []))} segments")
                else:
                    logger.warning(f"Transcript file not found: {tmp_path}")
            except Exception as e:
                logger.warning(f"Failed to load transcript file: {e}")
            finally:
                # Cleanup temp file (only if it was created by us)
                if tmp_path and tmp_path.startswith(tempfile.gettempdir()):
                    try:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temp file: {e}")
        except Exception as e:
            logger.warning(f"Failed to load transcript: {e}")
        
        # Get scores from report_json
        scores = None
        if session.report_json and "scores" in session.report_json:
            scores = ScoreOut(**session.report_json["scores"])
        
        from ..schemas.flags import FlagOut
        
        # Convert flags - schema handles flag_metadata -> metadata mapping via alias
        flag_data = []
        for f in flags:
            # Use model_validate which handles the alias mapping
            flag_out = FlagOut.model_validate(f)
            # Serialize - will output 'metadata' due to alias
            flag_dict = flag_out.model_dump(by_alias=True)  # Use alias for output (metadata)
            flag_data.append(flag_dict)
        
        # Get video URL - use API endpoint for authenticated access
        # This allows us to serve videos through our API with proper authentication
        video_url = None
        if session.video_url:
            # Always use API endpoint for video access (more reliable than presigned URLs)
            from ...config import settings
            api_base = getattr(settings, 'api_base_url', 'http://localhost:8000')
            video_url = f"{api_base}/api/ai-interview/{session_id}/video"
            logger.debug(f"Generated video URL for session {session_id}: {video_url}")
        else:
            # Check if video might exist in storage even if video_url is not set
            video_path = f"sessions/{session_id}/raw.mp4"
            if self.storage.is_available():
                try:
                    # Check if video exists in storage
                    from minio.error import S3Error
                    try:
                        # Try to stat the object to see if it exists
                        self.storage.client.stat_object(self.storage.bucket_name, video_path)
                        # Video exists, generate API URL
                        from ...config import settings
                        api_base = getattr(settings, 'api_base_url', 'http://localhost:8000')
                        video_url = f"{api_base}/api/ai-interview/{session_id}/video"
                        logger.debug(f"Video found in storage, generated URL: {video_url}")
                    except S3Error:
                        logger.debug(f"Video not found in storage at {video_path}")
                        video_url = None
                except Exception as e:
                    logger.debug(f"Error checking video in storage: {e}")
                    video_url = None
        
        # Get clip URLs for flags
        for flag_dict in flag_data:
            if flag_dict.get('clip_url'):
                try:
                    # clip_url might be a storage path or already a URL
                    clip_storage_path = flag_dict['clip_url']
                    if not clip_storage_path.startswith('http'):
                        try:
                            # Check if storage is available first
                            if not self.storage.client:
                                raise RuntimeError("Storage client not available")
                            
                            clip_url = self.storage.get_presigned_url(clip_storage_path, expires=timedelta(days=7))
                            flag_dict['clip_url'] = clip_url
                        except (RuntimeError, Exception) as e:
                            logger.debug(f"Storage not available for clip, using API endpoint: {e}")
                            # Fallback to API endpoint
                            from ...config import settings
                            api_base = getattr(settings, 'api_base_url', 'http://localhost:8000')
                            flag_id = flag_dict.get('id')
                            flag_dict['clip_url'] = f"{api_base}/api/ai-interview/{session_id}/clips/{flag_id}"
                    # If it's already a URL, keep it as is
                except Exception as e:
                    logger.warning(f"Failed to get clip URL for flag {flag_dict.get('id')}: {e}")
        
        session_dict = session.__dict__.copy()
        session_dict['video_url'] = video_url
        
        return SessionReportOut(
            session=SessionOut.model_validate(session_dict),
            flags=flag_data,
            transcript=transcript,
            scores=scores.model_dump() if scores else None
        )
    
    def set_recommendation(
        self,
        db: Session,
        session_id: int,
        recommendation: Recommendation
    ) -> AISession:
        """
        Set final recommendation for session
        
        Args:
            db: Database session
            session_id: Session ID
            recommendation: Final recommendation
            
        Returns:
            Updated AISession
        """
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.recommendation = recommendation
        db.commit()
        db.refresh(session)
        return session
    
    def calculate_recommendation(
        self,
        db: Session,
        session_id: int
    ) -> Recommendation:
        """
        Calculate recommendation based on score and flags
        
        Policy:
        - Auto-PASS: final_score ≥ 7.0 AND no HIGH flags AND ≤2 MODERATE flags
        - Auto-FAIL: ≥2 HIGH flags OR explicit policy breach
        - Else: REVIEW
        """
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get flags
        flags = db.query(AISessionFlag).filter(
            AISessionFlag.session_id == session_id
        ).all()
        
        high_flags = [f for f in flags if f.severity == FlagSeverity.HIGH]
        moderate_flags = [f for f in flags if f.severity == FlagSeverity.MODERATE]
        
        # Check for auto-fail
        if len(high_flags) >= 2:
            return Recommendation.FAIL
        
        # Check for auto-pass
        if session.total_score and session.total_score >= Decimal("7.0"):
            if len(high_flags) == 0 and len(moderate_flags) <= 2:
                return Recommendation.PASS
        
        return Recommendation.REVIEW


"""Scoring router"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import logging
import tempfile
import os
from ...database import get_db
from ...api.auth import get_current_user
from ...models.user import User
from ..schemas.scoring import ScoringRequest, ScoreOut
from ..schemas.sessions import SessionReportOut
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


@router.get("/{session_id}/report", response_model=SessionReportOut)
async def get_report(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full session report with transcript, flags, and scores
    
    Auth: Candidate (own session) or HR/Admin
    """
    try:
        report = _interview_service.get_report(db, session_id)
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{session_id}/score", response_model=ScoreOut)
async def score_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Score an interview session (triggers RAG-based scoring)
    
    Auth: HR/Admin only
    Idempotent: Returns existing scores if already scored
    """
    # Check if user is HR or Admin
    if current_user.user_type not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin can trigger scoring"
        )
    
    try:
        from ..models.ai_sessions import AISession
        
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Check if already scored
        if session.report_json and "scores" in session.report_json:
            return ScoreOut(**session.report_json["scores"])
        
        # Get transcript
        if not session.transcript_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcript not available for scoring"
            )
        
        # Load transcript
        transcript_text = ""
        try:
            import tempfile
            import json
            import os
            
            transcript_path = _storage_service.get_transcript_path(session_id)
            tmp_path = None
            
            try:
                # Create temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                    tmp_path = tmp.name
                
                # Download transcript from storage
                try:
                    _storage_service.download_file(transcript_path, tmp_path)
                except Exception as e:
                    logger.warning(f"Failed to download transcript from storage: {e}")
                    # If storage not available, try to use transcript_url as direct path
                    if session.transcript_url and os.path.exists(session.transcript_url):
                        tmp_path = session.transcript_url
                    else:
                        raise ValueError("Transcript file not found")
                
                # Load transcript JSON and extract text
                if tmp_path and os.path.exists(tmp_path):
                    with open(tmp_path, 'r') as f:
                        transcript_data = json.load(f)
                    
                    # Extract text from transcript
                    if isinstance(transcript_data, dict) and 'segments' in transcript_data:
                        segments = transcript_data['segments']
                        transcript_text = ' '.join([seg.get('text', '') for seg in segments if isinstance(seg, dict)])
                    elif isinstance(transcript_data, list):
                        transcript_text = ' '.join([seg.get('text', '') for seg in transcript_data if isinstance(seg, dict)])
                    elif isinstance(transcript_data, str):
                        transcript_text = transcript_data
                    else:
                        transcript_text = str(transcript_data)
            except Exception as e:
                logger.warning(f"Failed to load transcript file: {e}")
                # If transcript is required, raise error
                if not transcript_text:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to load transcript: {str(e)}"
                    )
            finally:
                # Cleanup temp file (only if it was created by us)
                if tmp_path and tmp_path.startswith(tempfile.gettempdir()):
                    try:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temp file: {e}")
        except Exception as e:
            logger.error(f"Failed to load transcript for scoring: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transcript not available: {str(e)}"
            )
        
        # Score using RAG
        scores = await _rag_service.score_interview(
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
        recommendation = _interview_service.calculate_recommendation(db, session_id)
        session.recommendation = recommendation
        
        db.commit()
        db.refresh(session)
        
        return scores
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to score session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{session_id}/video")
async def get_video(
    session_id: int,
    token: Optional[str] = Query(None),  # Allow token as query param for video element
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
):
    """
    Stream video file for a session
    
    Auth: Candidate (own session) or HR/Admin
    Token can be provided via Authorization header or query parameter
    """
    try:
        from ..models.ai_sessions import AISession
        from ...api.auth import get_current_user
        from fastapi.security import HTTPBearer
        
        # Authenticate user - try header first, then query param
        current_user = None
        if credentials:
            try:
                current_user = await get_current_user(credentials, db)
            except:
                pass
        
        if not current_user and token:
            # Try to authenticate with query param token
            try:
                from ...utils.auth import verify_token
                payload = verify_token(token)
                email = payload.get("sub")
                current_user = db.query(User).filter(User.email == email).first()
            except:
                pass
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Get video path
        video_path = session.video_url or f"sessions/{session_id}/raw.mp4"
        
        # Download video to temp file if needed
        temp_video = None
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                temp_video = tmp.name
            
            # Download from storage
            try:
                _storage_service.download_file(video_path, temp_video)
            except Exception as e:
                logger.warning(f"Failed to download video from storage: {e}")
                # Try as local file path
                if os.path.exists(video_path):
                    temp_video = video_path
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Video file not found for session {session_id}"
                    )
            
            # Stream video file
            def generate():
                with open(temp_video, 'rb') as video_file:
                    while True:
                        chunk = video_file.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        yield chunk
            
            # Cleanup temp file after streaming
            def cleanup():
                if temp_video and temp_video.startswith(tempfile.gettempdir()):
                    try:
                        if os.path.exists(temp_video):
                            os.remove(temp_video)
                    except:
                        pass
            
            response = StreamingResponse(
                generate(),
                media_type="video/mp4",
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Disposition": f'inline; filename="session_{session_id}_video.mp4"'
                }
            )
            
            # Note: cleanup will happen when response is consumed
            return response
            
        except Exception as e:
            # Cleanup on error
            if temp_video and temp_video.startswith(tempfile.gettempdir()):
                try:
                    if os.path.exists(temp_video):
                        os.remove(temp_video)
                except:
                    pass
            raise
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve video: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{session_id}/clips/{flag_id}")
async def get_clip(
    session_id: int,
    flag_id: int,
    token: Optional[str] = Query(None),  # Allow token as query param
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
):
    """
    Stream video clip for a flag
    
    Auth: Candidate (own session) or HR/Admin
    Token can be provided via Authorization header or query parameter
    """
    try:
        from ..models.ai_sessions import AISessionFlag, AISession
        
        # Authenticate user - try header first, then query param
        current_user = None
        if credentials:
            try:
                current_user = await get_current_user(credentials, db)
            except:
                pass
        
        if not current_user and token:
            # Try to authenticate with query param token
            try:
                from ...utils.auth import verify_token
                payload = verify_token(token)
                email = payload.get("sub")
                current_user = db.query(User).filter(User.email == email).first()
            except:
                pass
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Verify session exists
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Get flag
        flag = db.query(AISessionFlag).filter(
            AISessionFlag.id == flag_id,
            AISessionFlag.session_id == session_id
        ).first()
        
        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flag {flag_id} not found for session {session_id}"
            )
        
        # Get clip path
        clip_path = flag.clip_url or f"sessions/{session_id}/clips/flag_{flag_id}.mp4"
        
        # Download clip to temp file if needed
        temp_clip = None
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                temp_clip = tmp.name
            
            # Download from storage
            try:
                _storage_service.download_file(clip_path, temp_clip)
            except Exception as e:
                logger.warning(f"Failed to download clip from storage: {e}")
                # Try as local file path
                if os.path.exists(clip_path):
                    temp_clip = clip_path
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Clip file not found for flag {flag_id}"
                    )
            
            # Stream clip file
            def generate():
                with open(temp_clip, 'rb') as clip_file:
                    while True:
                        chunk = clip_file.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        yield chunk
            
            response = StreamingResponse(
                generate(),
                media_type="video/mp4",
                headers={
                    "Accept-Ranges": "bytes",
                    "Content-Disposition": f'inline; filename="flag_{flag_id}_clip.mp4"'
                }
            )
            
            return response
            
        except Exception as e:
            # Cleanup on error
            if temp_clip and temp_clip.startswith(tempfile.gettempdir()):
                try:
                    if os.path.exists(temp_clip):
                        os.remove(temp_clip)
                except:
                    pass
            raise
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve clip: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


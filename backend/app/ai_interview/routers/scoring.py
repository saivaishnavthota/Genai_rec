"""Scoring router"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Any
from decimal import Decimal
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


def convert_decimals_to_floats(obj: Any) -> Any:
    """Recursively convert Decimal values to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimals_to_floats(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals_to_floats(item) for item in obj]
    else:
        return obj

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
        
        # Get transcript - try multiple sources
        transcript_text = ""
        transcript_path = None
        
        # Try to get transcript from session.transcript_url first
        if session.transcript_url:
            transcript_path = session.transcript_url
        else:
            # Try default path
            transcript_path = _storage_service.get_transcript_path(session_id)
        
        logger.info(f"Attempting to load transcript for session {session_id} from: {transcript_path}")
        
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
                if _storage_service.is_available() and transcript_path:
                    try:
                        logger.info(f"Downloading transcript from storage: {transcript_path}")
                        _storage_service.download_file(transcript_path, tmp_path)
                        logger.info(f"Successfully downloaded transcript")
                    except Exception as e:
                        logger.warning(f"Failed to download transcript from storage: {e}")
                        # Try alternative path
                        alt_path = f"sessions/{session_id}/artifacts/transcript.json"
                        try:
                            _storage_service.download_file(alt_path, tmp_path)
                            logger.info(f"Downloaded transcript from alternative path: {alt_path}")
                        except Exception as e2:
                            logger.warning(f"Alternative path also failed: {e2}")
                            # If storage not available, try to use transcript_url as direct path
                            if session.transcript_url and os.path.exists(session.transcript_url):
                                tmp_path = session.transcript_url
                                logger.info(f"Using local file path: {tmp_path}")
                            else:
                                raise ValueError(f"Transcript file not found at {transcript_path} or {alt_path}")
                
                # Load transcript JSON and extract text
                if tmp_path and os.path.exists(tmp_path):
                    file_size = os.path.getsize(tmp_path)
                    logger.info(f"Loading transcript file: {tmp_path} ({file_size} bytes)")
                    with open(tmp_path, 'r', encoding='utf-8') as f:
                        transcript_data = json.load(f)
                    
                    # Extract text from transcript
                    if isinstance(transcript_data, dict) and 'segments' in transcript_data:
                        segments = transcript_data['segments']
                        transcript_text = ' '.join([seg.get('text', '') for seg in segments if isinstance(seg, dict)])
                    elif isinstance(transcript_data, dict) and 'text' in transcript_data:
                        transcript_text = transcript_data['text']
                    elif isinstance(transcript_data, list):
                        transcript_text = ' '.join([seg.get('text', '') for seg in transcript_data if isinstance(seg, dict)])
                    elif isinstance(transcript_data, str):
                        transcript_text = transcript_data
                    else:
                        transcript_text = str(transcript_data)
                    
                    logger.info(f"Extracted transcript text: {len(transcript_text)} characters")
                else:
                    raise ValueError(f"Transcript file not found: {tmp_path}")
            except Exception as e:
                logger.error(f"Failed to load transcript file: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to load transcript: {str(e)}. Path tried: {transcript_path}"
                )
            finally:
                # Cleanup temp file (only if it was created by us)
                if tmp_path and tmp_path.startswith(tempfile.gettempdir()):
                    try:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temp file: {e}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to load transcript for scoring: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transcript not available: {str(e)}"
            )
        
        if not transcript_text or len(transcript_text.strip()) == 0:
            logger.warning(f"Transcript is empty for session {session_id}. transcript_url={session.transcript_url}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcript is empty or not available. Please ensure the interview video has been uploaded and transcribed before scoring. If the video was just uploaded, wait a few moments for transcription to complete."
            )
        
        # Score using RAG
        try:
            scores = await _rag_service.score_interview(
                db,
                transcript_text,
                session_id,
                session.job_id
            )
        except Exception as e:
            logger.error(f"RAG scoring failed for session {session_id}: {e}", exc_info=True)
            # Check if it's an Ollama connection error
            error_msg = str(e)
            if "Connection" in error_msg or "timeout" in error_msg.lower() or "refused" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Scoring service unavailable. Please ensure Ollama is running and accessible at {_rag_service.ollama_url}. Error: {error_msg}"
                )
            elif "JSON" in error_msg or "parse" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to parse scoring response from LLM. The model may have returned invalid JSON. Error: {error_msg}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to score interview: {error_msg}"
                )
        
        # Update session
        try:
            session.total_score = scores.final_score
            
            # Convert scores to dict and ensure all Decimal values are converted to float for JSON serialization
            scores_dict = scores.model_dump()
            # Recursively convert all Decimal values to float
            scores_dict = convert_decimals_to_floats(scores_dict)
            
            session.report_json = {
                "scores": scores_dict,
                "scored_at": str(datetime.utcnow())
            }
            
            # Calculate recommendation
            recommendation = _interview_service.calculate_recommendation(db, session_id)
            session.recommendation = recommendation
            
            db.commit()
            db.refresh(session)
        except Exception as e:
            logger.error(f"Failed to save scores to database for session {session_id}: {e}", exc_info=True)
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save scores: {str(e)}"
            )
        
        return scores
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to score session {session_id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to score session: {str(e)}"
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
        
        # Get video path - use session.video_url if set, otherwise try default path
        video_path = session.video_url
        if not video_path:
            video_path = f"sessions/{session_id}/raw.mp4"
        
        logger.info(f"Serving video for session {session_id}, path: {video_path}")
        
        # Download video to temp file if needed
        temp_video = None
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                temp_video = tmp.name
            
            # Download from storage
            video_found = False
            if _storage_service.is_available():
                try:
                    logger.info(f"Attempting to download video from storage: {video_path}")
                    _storage_service.download_file(video_path, temp_video)
                    video_found = os.path.exists(temp_video) and os.path.getsize(temp_video) > 0
                    if video_found:
                        logger.info(f"Successfully downloaded video from storage: {os.path.getsize(temp_video)} bytes")
                    else:
                        logger.warning(f"Downloaded file is empty or doesn't exist")
                except Exception as e:
                    logger.warning(f"Failed to download video from storage: {e}")
            
            # If storage download failed, try as local file path
            if not video_found:
                if os.path.exists(video_path):
                    logger.info(f"Using local file path: {video_path}")
                    temp_video = video_path
                    video_found = True
                else:
                    logger.error(f"Video file not found at path: {video_path}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Video file not found for session {session_id}. Path: {video_path}"
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


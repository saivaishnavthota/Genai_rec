"""Proctor router for AI interview sessions"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import json
import logging
from ...database import get_db
from ...api.auth import get_current_user
from ...models.user import User
from ..schemas.sessions import SessionCreate, SessionStartResponse
from ..schemas.flags import ClientEventsRequest, FlagOut
from ..services.interview_service import InterviewService
from ..services.proctor_service import ProctorService
from ..services.webrtc_service import WebRTCService
from ..services.storage_service import StorageService
from ..services.clip_service import ClipService
from ..services.asr_service import ASRService
from ..services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances (would be injected via dependency injection in production)
_storage_service = StorageService()
_clip_service = ClipService(_storage_service)
_asr_service = ASRService()
_rag_service = RAGService()
_proctor_service = ProctorService(_clip_service)
_webrtc_service = WebRTCService()
_interview_service = InterviewService(_storage_service, _asr_service, _rag_service)


@router.post("/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED)
async def start_interview(
    request: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a new AI interview session
    
    Auth: Candidate or HR with invite token
    """
    try:
        # Create session
        session = _interview_service.create_session(
            db,
            request.application_id,
            request.job_id
        )
        
        # Start session
        session = _interview_service.start_session(db, session.id)
        
        # Generate WebRTC token
        token = _webrtc_service.generate_token(session.id, request.application_id)
        
        return SessionStartResponse(
            session_id=session.id,
            webrtc_token=token,
            policy_version=session.policy_version,
            rubric_version=session.rubric_version
        )
    except Exception as e:
        logger.error(f"Failed to start interview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.websocket("/{session_id}/stream")
async def stream_interview(
    websocket: WebSocket,
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for streaming audio and receiving interim transcripts/flags
    
    Accepts:
    - Audio chunks (base64 encoded PCM)
    - Frame metadata (optional)
    
    Emits:
    - Interim transcripts
    - Provisional flags
    """
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "audio":
                # Process audio chunk
                # TODO: Implement audio processing
                pass
            
            elif data.get("type") == "frame_meta":
                # Process frame metadata
                # TODO: Implement frame processing
                pass
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


@router.post("/{session_id}/events", status_code=status.HTTP_204_NO_CONTENT)
async def submit_client_events(
    session_id: int,
    request: ClientEventsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit client telemetry events (head pose, face detection)
    
    Events are processed and debounced by the proctor service
    """
    try:
        # Process events
        logger.info(f"Processing {len(request.events)} client events for session {session_id}")
        flags = _proctor_service.process_client_events(
            session_id,
            [e.model_dump() for e in request.events],
            request.events[0].timestamp if request.events else 0.0
        )
        
        logger.info(f"Generated {len(flags)} flags from events")
        
        # Save flags to database
        for flag in flags:
            db.add(flag)
        db.commit()
        
        logger.info(f"Saved {len(flags)} flags to database for session {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to process events: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/application/{application_id}/sessions")
async def get_application_sessions(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all AI interview sessions for an application
    
    Auth: HR/Admin or Candidate (own application)
    """
    from ..models.ai_sessions import AISession
    from ..schemas.sessions import SessionOut
    
    # Get application to check permissions
    from ...models.application import Application
    application = db.query(Application).filter(Application.id == application_id).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found"
        )
    
    # Check permissions
    if current_user.user_type not in ["hr", "admin"]:
        # Candidate can only see their own applications
        if current_user.user_type == "candidate" and application.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Get all sessions for this application
    sessions = db.query(AISession).filter(
        AISession.application_id == application_id
    ).order_by(AISession.created_at.desc()).all()
    
    return {
        "application_id": application_id,
        "sessions": [SessionOut.model_validate(s).model_dump() for s in sessions],
        "total": len(sessions)
    }


@router.get("/{session_id}/questions")
async def get_questions(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get interview questions for a session
    
    Auth: Candidate or HR
    """
    try:
        from ...models.job import Job
        from ..models.ai_sessions import AISession
        
        # Get session
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Get job
        job = db.query(Job).filter(Job.id == session.job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found for session {session_id}"
            )
        
        # Generate questions based on job
        # For now, use a simple template-based approach
        questions = []
        
        # Question 1: Introduction
        questions.append({
            "id": 1,
            "text": "Tell us about yourself and why you're interested in this position.",
            "type": "behavioral",
            "time_limit": 120  # 2 minutes
        })
        
        # Question 2: Role-specific
        if job.key_skills:
            skills_list = job.key_skills if isinstance(job.key_skills, list) else []
            if skills_list:
                skills_text = ", ".join(skills_list[:3])
                questions.append({
                    "id": 2,
                    "text": f"This role requires skills in {skills_text}. Can you share your experience with these technologies?",
                    "type": "technical",
                    "time_limit": 180  # 3 minutes
                })
        
        # Question 3: Experience
        if job.experience_level:
            questions.append({
                "id": 3,
                "text": f"With this being a {job.experience_level} level position, what relevant experience do you bring to this role?",
                "type": "experience",
                "time_limit": 150  # 2.5 minutes
            })
        
        # Question 4: Problem-solving
        questions.append({
            "id": 4,
            "text": "Describe a challenging project or problem you've worked on. How did you approach it and what was the outcome?",
            "type": "behavioral",
            "time_limit": 180  # 3 minutes
        })
        
        # Question 5: Closing
        questions.append({
            "id": 5,
            "text": "Do you have any questions about the role or the company?",
            "type": "closing",
            "time_limit": 120  # 2 minutes
        })
        
        return {
            "questions": questions,
            "total": len(questions),
            "job_title": job.title
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get questions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{session_id}/flags", response_model=List[FlagOut])
async def get_flags(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all flags for a session
    
    Returns list of all proctor flags
    """
    from ..models.ai_sessions import AISessionFlag
    
    flags = db.query(AISessionFlag).filter(
        AISessionFlag.session_id == session_id
    ).order_by(AISessionFlag.t_start).all()
    
    logger.info(f"Fetched {len(flags)} flags for session {session_id}")
    
    # Convert flags to output schema with proper alias handling
    flag_outputs = []
    for f in flags:
        flag_out = FlagOut.model_validate(f)
        flag_outputs.append(flag_out)
    
    return flag_outputs


@router.post("/{session_id}/end", status_code=status.HTTP_200_OK)
async def end_interview(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    End an interview session (idempotent)
    
    Marks session as FINALIZING, saves video URL, and generates clips for flags
    """
    try:
        # Set default video path
        video_path = f"sessions/{session_id}/raw.mp4"
        session = _interview_service.end_session(db, session_id, video_url=video_path)
        
        # Generate clips for flags that don't have them
        from ..services.flag_clip_service import FlagClipService
        flag_clip_service = FlagClipService(_storage_service, _clip_service)
        
        # Run clip generation in background (non-blocking)
        try:
            await flag_clip_service.generate_clips_for_flags(db, session_id)
        except Exception as e:
            logger.warning(f"Failed to generate clips for flags: {e}")
            # Don't fail the request if clip generation fails
        
        # TODO: Enqueue scoring job in background
        
        return {"status": "ended", "session_id": session_id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to end interview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


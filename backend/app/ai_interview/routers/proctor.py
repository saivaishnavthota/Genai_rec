"""Proctor router for AI interview sessions"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import json
import logging
import os
import tempfile
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
from ...services.tts_service import TTSService

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
_tts_service = TTSService()


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
        # Get application and job details for email
        from ...models.application import Application
        from ...models.job import Job
        
        application = db.query(Application).filter(Application.id == request.application_id).first()
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {request.application_id} not found"
            )
        
        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {request.job_id} not found"
            )
        
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
        
        # Send interview invitation email to candidate
        try:
            from ...utils.interview_emails import send_ai_interview_invitation_email
            from ...config import settings
            
            # Generate interview link
            interview_link = f"{settings.frontend_url}/ai-interview/{session.id}"
            
            # Get candidate name and email
            candidate_name = application.full_name or application.candidate_email.split('@')[0]
            candidate_email = application.candidate_email
            job_title = job.title or "the position"
            
            # Send email
            email_sent = send_ai_interview_invitation_email(
                candidate_email=candidate_email,
                candidate_name=candidate_name,
                job_title=job_title,
                interview_link=interview_link
            )
            
            if email_sent:
                logger.info(f"✅ Interview invitation email sent to {candidate_email} for session {session.id}")
            else:
                logger.warning(f"⚠️ Failed to send interview invitation email to {candidate_email} for session {session.id}")
        except Exception as e:
            # Don't fail the request if email fails
            logger.error(f"Failed to send interview invitation email: {e}", exc_info=True)
        
        return SessionStartResponse(
            session_id=session.id,
            webrtc_token=token,
            policy_version=session.policy_version,
            rubric_version=session.rubric_version
        )
    except HTTPException:
        raise
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
    
    Questions are generated from the candidate's resume using LLM.
    Falls back to static questions if generation fails.
    
    Auth: Candidate or HR
    """
    try:
        from ...models.job import Job
        from ...models.application import Application
        from ..models.ai_sessions import AISession
        from ...services.llm_service import LLMService
        from ...utils.resume_parser import parse_resume
        
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
        
        # Get application to access resume
        application = None
        resume_text = ""
        
        if session.application_id:
            application = db.query(Application).filter(Application.id == session.application_id).first()
            
            if application and application.resume_path:
                try:
                    # Extract full text from resume file (not truncated)
                    from ...utils.resume_parser import extract_text_from_pdf, extract_text_from_docx, extract_text_from_doc
                    
                    # Get full resume text directly from file
                    if application.resume_filename.lower().endswith('.pdf'):
                        resume_text = extract_text_from_pdf(application.resume_path)
                    elif application.resume_filename.lower().endswith('.docx'):
                        resume_text = extract_text_from_docx(application.resume_path)
                    elif application.resume_filename.lower().endswith('.doc'):
                        resume_text = extract_text_from_doc(application.resume_path)
                    else:
                        # Fallback to parse_resume if file type not recognized
                        parsed_data = parse_resume(application.resume_path, application.resume_filename)
                        resume_text = parsed_data.get('raw_text', '')
                    
                    # Build resume summary from parsed data to enhance context
                    resume_summary_parts = []
                    if application.parsed_skills:
                        skills = application.parsed_skills if isinstance(application.parsed_skills, list) else []
                        if skills:
                            resume_summary_parts.append(f"Key Skills: {', '.join(skills[:15])}")
                    
                    if application.parsed_experience:
                        exp = application.parsed_experience if isinstance(application.parsed_experience, list) else []
                        if exp:
                            resume_summary_parts.append(f"Work Experience: {len(exp)} position(s)")
                    
                    if application.parsed_education:
                        edu = application.parsed_education if isinstance(application.parsed_education, list) else []
                        if edu:
                            resume_summary_parts.append(f"Education: {len(edu)} degree(s)")
                    
                    if application.parsed_certifications:
                        certs = application.parsed_certifications if isinstance(application.parsed_certifications, list) else []
                        if certs:
                            resume_summary_parts.append(f"Certifications: {', '.join(certs[:5])}")
                    
                    # Prepend summary to resume text for better context
                    if resume_summary_parts:
                        resume_text = "\n".join(resume_summary_parts) + "\n\n--- Full Resume Text ---\n\n" + resume_text
                    
                except Exception as e:
                    logger.warning(f"Failed to extract resume text: {e}")
                    resume_text = ""
        
        # Prepare job details
        job_title = job.title or "the position"
        job_description = job.description or job.short_description or ""
        key_skills = []
        if job.key_skills:
            key_skills = job.key_skills if isinstance(job.key_skills, list) else []
        experience_level = job.experience_level
        
        # Generate questions using LLM
        llm_service = LLMService()
        questions = await llm_service.generate_interview_questions(
            resume_text=resume_text,
            job_title=job_title,
            job_description=job_description,
            key_skills=key_skills,
            experience_level=experience_level
        )
        
        return {
            "questions": questions,
            "total": len(questions),
            "job_title": job_title
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get questions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{session_id}/questions/{question_id}/audio")
async def get_question_audio(
    session_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get TTS audio for a specific question

    Returns MP3 audio file that reads out the question text.

    Auth: Candidate or HR
    """
    try:
        from fastapi.responses import Response
        from ...models.job import Job
        from ...models.application import Application
        from ..models.ai_sessions import AISession
        from ...services.llm_service import LLMService
        from ...utils.resume_parser import parse_resume, extract_text_from_pdf, extract_text_from_docx, extract_text_from_doc

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

        # Get application to access resume
        application = None
        resume_text = ""

        if session.application_id:
            application = db.query(Application).filter(Application.id == session.application_id).first()

            if application and application.resume_path:
                try:
                    # Extract full text from resume file
                    if application.resume_filename.lower().endswith('.pdf'):
                        resume_text = extract_text_from_pdf(application.resume_path)
                    elif application.resume_filename.lower().endswith('.docx'):
                        resume_text = extract_text_from_docx(application.resume_path)
                    elif application.resume_filename.lower().endswith('.doc'):
                        resume_text = extract_text_from_doc(application.resume_path)
                    else:
                        parsed_data = parse_resume(application.resume_path, application.resume_filename)
                        resume_text = parsed_data.get('raw_text', '')

                    # Build resume summary
                    resume_summary_parts = []
                    if application.parsed_skills:
                        skills = application.parsed_skills if isinstance(application.parsed_skills, list) else []
                        if skills:
                            resume_summary_parts.append(f"Key Skills: {', '.join(skills[:15])}")

                    if application.parsed_experience:
                        exp = application.parsed_experience if isinstance(application.parsed_experience, list) else []
                        if exp:
                            resume_summary_parts.append(f"Work Experience: {len(exp)} position(s)")

                    if application.parsed_education:
                        edu = application.parsed_education if isinstance(application.parsed_education, list) else []
                        if edu:
                            resume_summary_parts.append(f"Education: {len(edu)} degree(s)")

                    if application.parsed_certifications:
                        certs = application.parsed_certifications if isinstance(application.parsed_certifications, list) else []
                        if certs:
                            resume_summary_parts.append(f"Certifications: {', '.join(certs[:5])}")

                    if resume_summary_parts:
                        resume_text = "\n".join(resume_summary_parts) + "\n\n--- Full Resume Text ---\n\n" + resume_text

                except Exception as e:
                    logger.warning(f"Failed to extract resume text: {e}")
                    resume_text = ""

        # Get questions
        job_title = job.title or "the position"
        job_description = job.description or job.short_description or ""
        key_skills = []
        if job.key_skills:
            key_skills = job.key_skills if isinstance(job.key_skills, list) else []
        experience_level = job.experience_level

        llm_service = LLMService()
        questions = await llm_service.generate_interview_questions(
            resume_text=resume_text,
            job_title=job_title,
            job_description=job_description,
            key_skills=key_skills,
            experience_level=experience_level
        )

        # Find the requested question
        question_text = None
        for q in questions:
            if q.get("id") == question_id:
                question_text = q.get("text")
                break

        if not question_text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question {question_id} not found"
            )

        # Generate TTS audio
        logger.info(f"Generating TTS audio for question {question_id}: {question_text[:50]}...")
        audio_bytes = _tts_service.text_to_speech(question_text)

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=question_{question_id}.mp3"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate question audio: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{session_id}/analyze-video", status_code=status.HTTP_202_ACCEPTED)
async def trigger_video_analysis(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Manually trigger video analysis for flags (phone, multi-face)
    
    Useful for re-analyzing existing videos or testing.
    Analysis runs in the background - check /flags endpoint to see results.
    """
    from ..models.ai_sessions import AISession
    
    session = db.query(AISession).filter(AISession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    if not session.video_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No video available for session {session_id}"
        )
    
    # Trigger analysis
    background_tasks.add_task(_analyze_video_for_flags_async, session_id, session.video_url)
    logger.info(f"📋 Manual video analysis triggered for session {session_id}")
    
    return {
        "status": "analysis_started",
        "session_id": session_id,
        "video_path": session.video_url,
        "message": "Video analysis is running in the background. Check /flags endpoint in a few seconds to see results, or check Docker logs for detailed progress."
    }


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
        
        # Try to transcribe audio if video is available (non-blocking)
        # Note: This requires the video to be uploaded first via /upload-video endpoint
        # For now, we'll just log that transcription should be triggered manually
        if session.video_url and _storage_service.is_available():
            logger.info(f"Session {session_id} ended. Video available at {session.video_url}. "
                       f"Transcription can be triggered via /{session_id}/transcribe endpoint.")
        
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


@router.post("/{session_id}/upload-video", status_code=status.HTTP_200_OK)
async def upload_video(
    session_id: int,
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload video recording for a session
    
    Auth: Candidate (own session) or HR/Admin
    """
    try:
        from ..models.ai_sessions import AISession
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Check permissions
        if current_user.user_type not in ["hr", "admin"]:
            if session.application_id:
                from ...models.application import Application
                application = db.query(Application).filter(Application.id == session.application_id).first()
                if application and application.candidate_email != current_user.email:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to upload video for this session"
                    )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            content = await video_file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Upload to storage
            video_path = f"sessions/{session_id}/raw.mp4"
            if _storage_service.is_available():
                try:
                    _storage_service.upload_file(tmp_path, video_path, content_type="video/mp4")
                    logger.info(f"Uploaded video to storage: {video_path}")
                    
                    # Update session video_url
                    session.video_url = video_path
                    db.commit()
                    
                    logger.info(f"✅ Video uploaded successfully for session {session_id}, triggering background tasks...")
                    
                    # Trigger automatic transcription in background (non-blocking)
                    background_tasks.add_task(_transcribe_video_async, session_id, video_path)
                    logger.info(f"📝 Transcription task started for session {session_id} (running in background)")
                    
                    # Trigger video analysis for flags (phone detection, multi-face detection)
                    background_tasks.add_task(_analyze_video_for_flags_async, session_id, video_path)
                    logger.info(f"🔍 Video analysis task started for session {session_id} (running in background)")
                    
                    return {"status": "uploaded", "video_path": video_path}
                except Exception as e:
                    logger.error(f"Failed to upload video to storage: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to upload video: {str(e)}"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Storage service not available. Please ensure MinIO is running."
                )
        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload video: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def _analyze_video_for_flags_async(session_id: int, video_path: str):
    """Background task to analyze video for flags (phone, multi-face)"""
    from ...database import SessionLocal
    from ..utils.flag_tracker import create_phone_tracker, create_multi_face_tracker, FlagWindow
    import cv2
    import tempfile
    import os
    
    logger.info(f"🔍 VIDEO ANALYSIS TASK STARTED for session {session_id}, video_path: {video_path}")
    
    db = SessionLocal()
    try:
        from ..models.ai_sessions import AISession, FlagType, FlagSeverity
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            logger.warning(f"❌ Session {session_id} not found for video analysis")
            return
        
        logger.info(f"✅ Session {session_id} found, starting video analysis")
        
        # Create fresh trackers for this analysis (don't reuse shared trackers)
        phone_tracker = create_phone_tracker()
        multi_face_tracker = create_multi_face_tracker()
        
        # Check if storage is available
        if not _storage_service.is_available():
            logger.error(f"❌ Storage service not available for session {session_id}")
            return
        
        # Download video from storage
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            logger.info(f"📥 Downloading video from {video_path} to {tmp_path}")
            _storage_service.download_file(video_path, tmp_path)
            
            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                logger.error(f"❌ Downloaded video file is empty or doesn't exist: {tmp_path}")
                return
            
            file_size = os.path.getsize(tmp_path)
            logger.info(f"✅ Downloaded video: {tmp_path} ({file_size} bytes)")
            
            # Open video
            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                logger.error(f"❌ Failed to open video file: {tmp_path}")
                return
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            duration = total_frames / fps if fps > 0 else 0
            
            logger.info(f"📹 Video info: {total_frames} frames, {fps:.2f} fps, {duration:.2f}s duration")
            
            frame_interval = max(1, int(fps / 2))  # Sample 2 frames per second
            logger.info(f"📊 Sampling every {frame_interval} frames (2 frames/second)")
            
            frame_count = 0
            sampled_frame_count = 0  # Count of actually sampled frames
            flags_created = []
            phone_detections = 0
            multi_face_detections = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Sample frames (every Nth frame)
                if frame_count % frame_interval != 0:
                    frame_count += 1
                    continue
                
                # Calculate timestamp based on sampled frames
                # Each sampled frame represents 0.5 seconds (since we sample 2 per second)
                timestamp = sampled_frame_count * 0.5
                sampled_frame_count += 1
                frame_count += 1
                
                # Detect phone in frame
                phone_detection = _proctor_service.detect_phone_in_frame(frame, timestamp)
                if phone_detection:
                    conf = phone_detection.get("confidence", 0)
                    phone_detections += 1
                    logger.info(f"📱 Phone detected at {timestamp:.2f}s: confidence={conf:.2f}, "
                              f"bbox={phone_detection.get('metadata', {}).get('bbox', [])}")
                    
                    # Lower threshold to 0.5 for better detection
                    if conf >= 0.50:
                        logger.info(f"📊 Updating phone tracker: timestamp={timestamp:.2f}s, conf={conf:.2f}")
                        
                        # Get tracker state before update
                        active_start_before = getattr(phone_tracker, 'active_start', None)
                        max_conf_before = getattr(phone_tracker, 'max_conf', 0)
                        
                        window = phone_tracker.update(
                            timestamp,
                            conf,
                            phone_detection.get("metadata", {})
                        )
                        
                        # Get tracker state after update
                        active_start_after = getattr(phone_tracker, 'active_start', None)
                        max_conf_after = getattr(phone_tracker, 'max_conf', 0)
                        
                        if window:
                            flag = _proctor_service._create_flag(
                                session_id,
                                FlagType.PHONE,
                                window.severity,
                                window.confidence,
                                window.t_start,
                                window.t_end,
                                window.metadata
                            )
                            flags_created.append(flag)
                            logger.info(f"🚨 Phone flag created: {window.severity} at {window.t_start:.2f}s-{window.t_end:.2f}s (conf={window.confidence:.2f})")
                            logger.debug(f"📝 Flag object: t_start={flag.t_start}, t_end={flag.t_end}, type(t_start)={type(flag.t_start)}")
                        else:
                            # Log detailed tracker state to debug why no window was emitted
                            duration = timestamp - active_start_after if active_start_after else 0
                            logger.info(f"⏳ Phone tracker active but no flag yet - "
                                      f"active_start={active_start_after}, "
                                      f"max_conf={max_conf_after:.2f}, "
                                      f"duration={duration:.2f}s, "
                                      f"required_duration=0.5s, "
                                      f"last_emit_time={getattr(phone_tracker, 'last_emit_time', 0):.2f}")
                    else:
                        logger.info(f"⚠️ Phone detected but confidence {conf:.2f} < 0.50 threshold")
                else:
                    # Reset tracker when no phone detected
                    phone_tracker.update(timestamp, 0.0, {})
                
                # Detect faces in frame
                face_detection = _proctor_service.detect_faces_in_frame(frame, timestamp)
                face_count = face_detection.get("face_count", 0)
                
                # Log all face detections for debugging
                if face_count > 0:
                    logger.info(f"👤 Face detection at {timestamp:.2f}s: count={face_count}, "
                              f"faces={face_detection.get('metadata', {}).get('faces', [])}")
                
                if face_count > 1:
                    multi_face_detections += 1
                    logger.info(f"👥 Multiple faces detected at {timestamp:.2f}s: count={face_count}")
                
                # Always update tracker (even if face_count <= 1, to reset duration)
                conf = 1.0 if face_count > 1 else 0.0
                
                # Get tracker state before update
                active_start_before = getattr(multi_face_tracker, 'active_start', None)
                
                window = multi_face_tracker.update(
                    timestamp,
                    conf,
                    {"face_count": face_count, **face_detection.get("metadata", {})}
                )
                
                # Get tracker state after update
                active_start_after = getattr(multi_face_tracker, 'active_start', None)
                
                if window:
                    flag = _proctor_service._create_flag(
                        session_id,
                        FlagType.MULTI_FACE,
                        window.severity,
                        window.confidence,
                        window.t_start,
                        window.t_end,
                        window.metadata
                    )
                    flags_created.append(flag)
                    logger.info(f"🚨 Multi-face flag created: {window.severity} at {window.t_start:.2f}s-{window.t_end:.2f}s (face_count={face_count})")
                    logger.debug(f"📝 Flag object: t_start={flag.t_start}, t_end={flag.t_end}, type(t_start)={type(flag.t_start)}")
                elif face_count > 1:
                    # Log detailed tracker state when multi-face detected but no flag
                    duration = timestamp - active_start_after if active_start_after else 0
                    logger.info(f"⏳ Multi-face tracker active but no flag yet - "
                              f"active_start={active_start_after}, "
                              f"duration={duration:.2f}s, "
                              f"required_duration=0.5s, "
                              f"last_emit_time={getattr(multi_face_tracker, 'last_emit_time', 0):.2f}")
            
            cap.release()
            
            # Check for any remaining active trackers that should emit flags
            # This handles cases where detection happened but video ended before duration threshold
            final_timestamp = sampled_frame_count * 0.5
            
            # Check phone tracker
            if phone_tracker.active_start is not None:
                duration = final_timestamp - phone_tracker.active_start
                if duration >= phone_tracker.min_duration:
                    logger.info(f"📞 Phone tracker still active at end of video, creating flag (duration={duration:.2f}s)")
                    window = FlagWindow(
                        t_start=max(0, phone_tracker.active_start - 2.0),
                        t_end=final_timestamp + 2.0,
                        confidence=phone_tracker.max_conf,
                        severity=FlagSeverity.MODERATE,
                        metadata=phone_tracker.metadata.copy()
                    )
                    flag = _proctor_service._create_flag(
                        session_id,
                        FlagType.PHONE,
                        window.severity,
                        window.confidence,
                        window.t_start,
                        window.t_end,
                        window.metadata
                    )
                    flags_created.append(flag)
                    logger.info(f"🚨 Phone flag created from active tracker: {window.severity} at {window.t_start:.2f}s-{window.t_end:.2f}s")
                    logger.debug(f"📝 Flag object: t_start={flag.t_start}, t_end={flag.t_end}, type(t_start)={type(flag.t_start)}")
            
            # Check multi-face tracker
            if multi_face_tracker.active_start is not None:
                duration = final_timestamp - multi_face_tracker.active_start
                if duration >= multi_face_tracker.min_duration:
                    logger.info(f"👥 Multi-face tracker still active at end of video, creating flag (duration={duration:.2f}s)")
                    window = FlagWindow(
                        t_start=max(0, multi_face_tracker.active_start - 2.0),
                        t_end=final_timestamp + 2.0,
                        confidence=multi_face_tracker.max_conf,
                        severity=FlagSeverity.HIGH,
                        metadata=multi_face_tracker.metadata.copy()
                    )
                    flag = _proctor_service._create_flag(
                        session_id,
                        FlagType.MULTI_FACE,
                        window.severity,
                        window.confidence,
                        window.t_start,
                        window.t_end,
                        window.metadata
                    )
                    flags_created.append(flag)
                    logger.info(f"🚨 Multi-face flag created from active tracker: {window.severity} at {window.t_start:.2f}s-{window.t_end:.2f}s")
                    logger.debug(f"📝 Flag object: t_start={flag.t_start}, t_end={flag.t_end}, type(t_start)={type(flag.t_start)}")
            
            logger.info(f"📊 Analysis complete: {phone_detections} phone detections, {multi_face_detections} multi-face detections")
            
            # Save flags to database
            if flags_created:
                for flag in flags_created:
                    logger.debug(f"💾 Saving flag: type={flag.flag_type}, t_start={flag.t_start}, t_end={flag.t_end}")
                    db.add(flag)
                db.commit()
                logger.info(f"✅ Created {len(flags_created)} flags from video analysis for session {session_id}")
                
                # Verify flags were saved correctly
                from ..models.ai_sessions import AISessionFlag
                saved_flags = db.query(AISessionFlag).filter(
                    AISessionFlag.session_id == session_id
                ).order_by(AISessionFlag.t_start).all()
                logger.info(f"✅ Verified {len(saved_flags)} flags in database for session {session_id}")
                for f in saved_flags:
                    logger.debug(f"📋 Saved flag: id={f.id}, type={f.flag_type}, t_start={f.t_start}, t_end={f.t_end}")
            else:
                logger.warning(f"⚠️ No flags detected in video analysis for session {session_id} (phone_detections={phone_detections}, multi_face_detections={multi_face_detections})")
                
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                    logger.debug(f"🧹 Cleaned up temp file: {tmp_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove temp file {tmp_path}: {e}")
    except Exception as e:
        logger.error(f"❌ Failed to analyze video for flags for session {session_id}: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()
        logger.info(f"🏁 Video analysis task completed for session {session_id}")


async def _score_session_async(session_id: int, transcript_data: dict):
    """Internal function to score a session automatically (no auth required)"""
    from ...database import SessionLocal
    from ..models.ai_sessions import AISession
    from decimal import Decimal
    from datetime import datetime
    
    db = SessionLocal()
    try:
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            logger.warning(f"Session {session_id} not found for auto-scoring")
            return
        
        # Check if already scored
        if session.report_json and "scores" in session.report_json:
            logger.info(f"Session {session_id} already scored, skipping auto-scoring")
            return
        
        # Extract transcript text
        transcript_text = ""
        if isinstance(transcript_data, dict) and 'segments' in transcript_data:
            segments = transcript_data['segments']
            transcript_text = ' '.join([seg.get('text', '') for seg in segments if isinstance(seg, dict)])
        elif isinstance(transcript_data, dict) and 'text' in transcript_data:
            transcript_text = transcript_data['text']
        elif isinstance(transcript_data, list):
            transcript_text = ' '.join([seg.get('text', '') for seg in transcript_data if isinstance(seg, dict)])
        elif isinstance(transcript_data, str):
            transcript_text = transcript_data
        
        if not transcript_text or len(transcript_text.strip()) == 0:
            logger.warning(f"Transcript is empty for session {session_id}, cannot score")
            return
        
        logger.info(f"Auto-scoring session {session_id} with transcript length: {len(transcript_text)} chars")
        
        # Use existing service instances
        # Score using RAG
        scores = await _rag_service.score_interview(
            db,
            transcript_text,
            session_id,
            session.job_id
        )
        
        # Update session
        session.total_score = scores.final_score
        
        # Convert Decimal to float for JSON serialization
        scores_dict = scores.model_dump()
        def convert_decimals(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            return obj
        
        scores_dict = convert_decimals(scores_dict)
        
        session.report_json = {
            "scores": scores_dict,
            "scored_at": str(datetime.utcnow())
        }
        
        # Calculate recommendation
        recommendation = _interview_service.calculate_recommendation(db, session_id)
        session.recommendation = recommendation
        
        db.commit()
        logger.info(f"✅ Auto-scoring completed for session {session_id}: score={scores.final_score}, recommendation={recommendation}")
        
    except Exception as e:
        logger.error(f"Failed to auto-score session {session_id}: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

async def _transcribe_video_async(session_id: int, video_path: str):
    """Background task to transcribe video after upload"""
    from ...database import SessionLocal
    db = SessionLocal()
    try:
        from ..models.ai_sessions import AISession
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            logger.warning(f"Session {session_id} not found for transcription")
            return
        
        logger.info(f"Starting automatic transcription for session {session_id}")
        
        # Download video from storage
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            _storage_service.download_file(video_path, tmp_path)
            logger.info(f"Downloaded video for transcription: {tmp_path}")
            
            # Extract audio and transcribe (ASR service handles audio extraction)
            transcript = await _asr_service.transcribe_file(tmp_path, language="en", with_timestamps=True)
            logger.info(f"Transcription completed for session {session_id}")
            
            # Save transcript to storage
            transcript_path = _storage_service.get_transcript_path(session_id)
            import json
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_json:
                json.dump(transcript, tmp_json, indent=2)
                tmp_json_path = tmp_json.name
            
            try:
                if _storage_service.is_available():
                    _storage_service.upload_file(tmp_json_path, transcript_path, content_type="application/json")
                    logger.info(f"Uploaded transcript to storage: {transcript_path}")
                
                # Update session
                session.transcript_url = transcript_path
                db.commit()
                logger.info(f"Session {session_id} transcript saved successfully")
                
                # Automatically trigger scoring after transcription completes
                try:
                    logger.info(f"🤖 Auto-triggering scoring for session {session_id} after transcription")
                    await _score_session_async(session_id, transcript)
                    logger.info(f"✅ Auto-scoring completed for session {session_id}")
                except Exception as e:
                    logger.error(f"⚠️ Failed to auto-score session {session_id}: {e}", exc_info=True)
                    # Don't fail transcription if scoring fails
            finally:
                if os.path.exists(tmp_json_path):
                    os.remove(tmp_json_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        logger.error(f"Failed to transcribe video for session {session_id}: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

"""ASR router for transcription"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import logging
import tempfile
import os
from ...database import get_db
from ...api.auth import get_current_user
from ...models.user import User
from ..services.asr_service import ASRService
from ..services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter()

_asr_service = ASRService()
_storage_service = StorageService()


@router.post("/{session_id}/transcribe")
async def transcribe_audio(
    session_id: int,
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Transcribe audio file for a session
    
    Auth: Candidate (own session) or HR/Admin
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await audio_file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Transcribe
            transcript = await _asr_service.transcribe_file(
                tmp_path,
                language="en",
                with_timestamps=True
            )
            
            # Save transcript to storage
            storage_path = _storage_service.get_transcript_path(session_id)
            
            # Upload transcript JSON to storage
            import json
            if _storage_service.is_available():
                try:
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_json:
                        json.dump(transcript, tmp_json, indent=2)
                        tmp_json_path = tmp_json.name
                    
                    try:
                        _storage_service.upload_file(tmp_json_path, storage_path, content_type="application/json")
                        logger.info(f"Uploaded transcript to storage: {storage_path}")
                    finally:
                        if os.path.exists(tmp_json_path):
                            os.remove(tmp_json_path)
                except Exception as e:
                    logger.warning(f"Failed to upload transcript to storage: {e}")
            
            # Update session transcript_url
            from ..models.ai_sessions import AISession
            session = db.query(AISession).filter(AISession.id == session_id).first()
            if session:
                session.transcript_url = storage_path
                db.commit()
            
            return transcript
        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        logger.error(f"Failed to transcribe audio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


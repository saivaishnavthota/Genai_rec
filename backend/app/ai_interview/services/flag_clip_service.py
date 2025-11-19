"""Service for generating clips for flags after interview ends"""
import logging
import asyncio
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.ai_sessions import AISessionFlag, AISession
from .storage_service import StorageService
from .clip_service import ClipService

logger = logging.getLogger(__name__)


class FlagClipService:
    """Service for generating video clips for flags"""
    
    def __init__(self, storage_service: StorageService, clip_service: ClipService):
        self.storage = storage_service
        self.clip_service = clip_service
    
    async def generate_clips_for_flags(
        self,
        db: Session,
        session_id: int
    ) -> int:
        """
        Generate video clips for all flags that don't have clips yet
        
        Args:
            db: Database session
            session_id: Session ID
            
        Returns:
            Number of clips generated
        """
        # Get session
        session = db.query(AISession).filter(AISession.id == session_id).first()
        if not session:
            logger.error(f"Session {session_id} not found")
            return 0
        
        # Check if video URL exists
        if not session.video_url:
            logger.warning(f"Session {session_id} has no video URL, cannot generate clips")
            return 0
        
        # Get all flags without clips
        flags = db.query(AISessionFlag).filter(
            AISessionFlag.session_id == session_id,
            AISessionFlag.clip_url.is_(None)
        ).all()
        
        if not flags:
            logger.info(f"No flags without clips for session {session_id}")
            return 0
        
        # Get video recording path
        video_path = session.video_url
        if not video_path.startswith('/') and not video_path.startswith('sessions/'):
            # Assume it's a storage path
            video_path = f"sessions/{session_id}/raw.mp4"
        
        # Download video to temp file for clip generation
        import tempfile
        import os
        temp_video = None
        
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                temp_video = tmp.name
            
            # Download video from storage
            try:
                self.storage.download_file(video_path, temp_video)
            except Exception as e:
                logger.warning(f"Failed to download video from storage, trying local path: {e}")
                # Try as local file path
                if os.path.exists(video_path):
                    temp_video = video_path
                else:
                    raise ValueError(f"Video file not found at {video_path}")
            
            # Generate clips for each flag
            clips_generated = 0
            for flag in flags:
                try:
                    clip_url = await self.clip_service.generate_and_upload_clip(
                        session_id,
                        flag.id,
                        temp_video,
                        float(flag.t_start),
                        float(flag.t_end)
                    )
                    
                    # Update flag with clip URL
                    flag.clip_url = clip_url
                    clips_generated += 1
                    logger.info(f"Generated clip for flag {flag.id} at {flag.t_start}s-{flag.t_end}s")
                    
                except Exception as e:
                    logger.error(f"Failed to generate clip for flag {flag.id}: {e}")
                    # Continue with other flags
            
            # Commit all updates
            db.commit()
            logger.info(f"Generated {clips_generated} clips for session {session_id}")
            
            return clips_generated
            
        except Exception as e:
            logger.error(f"Failed to generate clips for session {session_id}: {e}")
            db.rollback()
            return 0
        finally:
            # Cleanup temp video file (only if we created it)
            if temp_video and temp_video.startswith(tempfile.gettempdir()):
                try:
                    if os.path.exists(temp_video):
                        os.remove(temp_video)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp video file: {e}")


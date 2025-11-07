"""Clip service for generating video clips"""
import os
import subprocess
import logging
from typing import Optional
from datetime import timedelta
from pathlib import Path
from ...config import settings
from ..utils.timecode import Timecode
from .storage_service import StorageService

logger = logging.getLogger(__name__)


class ClipService:
    """Service for generating video clips from recordings"""
    
    def __init__(self, storage_service: StorageService):
        self.storage = storage_service
        self.clip_duration_min = settings.clip_duration_min
        self.clip_duration_max = settings.clip_duration_max
    
    def generate_clip(
        self,
        input_path: str,
        t_start: float,
        t_end: float,
        output_path: str,
        add_padding: bool = True
    ) -> str:
        """
        Generate video clip using ffmpeg
        
        Args:
            input_path: Input video/audio file path
            t_start: Start time in seconds
            t_end: End time in seconds
            output_path: Output clip file path
            add_padding: Add 2s pre/post padding
            
        Returns:
            Path to generated clip
        """
        # Calculate duration
        duration = t_end - t_start
        
        # Add padding if requested
        if add_padding:
            t_start = max(0, t_start - 2.0)
            t_end = t_end + 2.0
            duration = t_end - t_start
        
        # Clamp duration
        duration = Timecode.clamp(duration, self.clip_duration_min, self.clip_duration_max)
        t_end = t_start + duration
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-ss", str(t_start),
            "-t", str(duration),
            "-c", "copy",  # Copy codec (faster)
            "-avoid_negative_ts", "make_zero",
            "-y",  # Overwrite output
            output_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            logger.info(f"Generated clip: {output_path} ({duration:.2f}s)")
            return output_path
        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg timeout for clip generation")
            raise RuntimeError("Clip generation timeout")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            raise RuntimeError(f"Failed to generate clip: {e.stderr}")
    
    async def generate_and_upload_clip(
        self,
        session_id: int,
        flag_id: int,
        recording_path: str,
        t_start: float,
        t_end: float
    ) -> str:
        """
        Generate clip and upload to storage
        
        Args:
            session_id: Session ID
            flag_id: Flag ID
            recording_path: Path to raw recording
            t_start: Start time
            t_end: End time
            
        Returns:
            Presigned URL to clip
        """
        # Generate temporary clip
        temp_clip = f"/tmp/clip_{session_id}_{flag_id}.mp4"
        
        try:
            # Generate clip
            clip_path = self.generate_clip(
                recording_path,
                t_start,
                t_end,
                temp_clip
            )
            
            # Upload to storage
            storage_path = self.storage.get_clip_path(session_id, flag_id)
            self.storage.upload_file(clip_path, storage_path, content_type="video/mp4")
            
            # Get presigned URL
            url = self.storage.get_presigned_url(storage_path, expires=timedelta(days=7))
            
            # Cleanup temp file
            if os.path.exists(temp_clip):
                os.remove(temp_clip)
            
            return url
        except Exception as e:
            logger.error(f"Failed to generate/upload clip: {e}")
            # Cleanup on error
            if os.path.exists(temp_clip):
                os.remove(temp_clip)
            raise


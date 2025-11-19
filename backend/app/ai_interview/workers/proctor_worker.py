"""Background worker for proctoring processing"""
import logging
import asyncio
from typing import Optional
from sqlalchemy.orm import Session
from ...database import SessionLocal
from ..services.proctor_service import ProctorService
from ..services.clip_service import ClipService
from ..services.storage_service import StorageService

logger = logging.getLogger(__name__)


class ProctorWorker:
    """Background worker for processing proctoring frames"""
    
    def __init__(self):
        self.storage = StorageService()
        self.clip_service = ClipService(self.storage)
        self.proctor_service = ProctorService(self.clip_service)
        self.running = False
    
    async def process_frame_batch(
        self,
        session_id: int,
        frames: list,
        recording_path: Optional[str] = None
    ):
        """
        Process a batch of frames
        
        Args:
            session_id: Session ID
            frames: List of (frame, timestamp) tuples
            recording_path: Optional path to recording
        """
        db = SessionLocal()
        try:
            flags = []
            for frame, timestamp in frames:
                flag = self.proctor_service.process_frame(
                    session_id,
                    frame,
                    timestamp,
                    recording_path
                )
                if flag:
                    flags.append(flag)
            
            # Save flags
            for flag in flags:
                db.add(flag)
            db.commit()
            
            logger.info(f"Processed {len(frames)} frames, emitted {len(flags)} flags")
        except Exception as e:
            logger.error(f"Failed to process frame batch: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def start(self):
        """Start the worker"""
        self.running = True
        logger.info("Proctor worker started")
        # In production, would connect to Redis queue or similar
    
    async def stop(self):
        """Stop the worker"""
        self.running = False
        logger.info("Proctor worker stopped")


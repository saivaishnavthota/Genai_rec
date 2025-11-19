import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database import get_db
from ..models.resume_update_tracking import ResumeUpdateRequest
from .resume_update_service import resume_update_service

logger = logging.getLogger(__name__)

class SchedulerService:
    """Background scheduler for resume update emails and other periodic tasks"""
    
    def __init__(self):
        self.running = False
        self.check_interval_minutes = 60  # Check every hour
    
    async def start_scheduler(self):
        """Start the background scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        logger.info("Starting resume update email scheduler")
        
        while self.running:
            try:
                await self.run_scheduled_tasks()
                # Wait for next check interval
                await asyncio.sleep(self.check_interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                # Wait a bit before retrying to avoid rapid error loops
                await asyncio.sleep(300)  # 5 minutes
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.running = False
        logger.info("Stopping resume update email scheduler")
    
    async def run_scheduled_tasks(self):
        """Run all scheduled tasks"""
        try:
            # Get database session
            db = next(get_db())
            
            # Check and send resume update emails
            emails_sent = await self.check_resume_update_emails(db)
            
            # Check for expired requests
            expired_count = await self.mark_expired_requests(db)
            
            if emails_sent > 0 or expired_count > 0:
                logger.info(f"Scheduler run completed: {emails_sent} emails sent, {expired_count} requests expired")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error in scheduled tasks: {e}")
    
    async def check_resume_update_emails(self, db: Session) -> int:
        """Check for and send scheduled resume update emails"""
        try:
            emails_sent = await resume_update_service.check_and_send_scheduled_emails(db)
            return emails_sent
        except Exception as e:
            logger.error(f"Error checking resume update emails: {e}")
            return 0
    
    async def mark_expired_requests(self, db: Session) -> int:
        """Mark requests as expired if 24 hours have passed without resume update"""
        try:
            now = datetime.utcnow()
            
            # Find requests where email was sent but no resume update received within 24 hours
            expired_requests = db.query(ResumeUpdateRequest).filter(
                and_(
                    ResumeUpdateRequest.status == "email_sent",
                    ResumeUpdateRequest.last_email_sent_at <= now - timedelta(hours=24),
                    ResumeUpdateRequest.update_attempts_count < ResumeUpdateRequest.max_attempts
                )
            ).all()
            
            expired_count = 0
            
            for request in expired_requests:
                # Check if this attempt should be marked as expired and next email scheduled
                # or if max attempts reached
                if request.update_attempts_count < request.max_attempts:
                    # Schedule next email (will be picked up in next scheduler run)
                    request.status = "llm_approved"
                    request.next_email_due_at = now
                    expired_count += 1
                    logger.info(f"Scheduling next email for application {request.application_id}, attempt {request.update_attempts_count + 1}")
                else:
                    # Max attempts reached, mark as failed
                    request.status = "completed_failure"
                    request.completion_reason = "Max attempts reached without resume update"
                    request.completed_at = now
                    request.application.status = "rejected"
                    expired_count += 1
                    logger.info(f"Application {request.application_id} marked as rejected - max attempts reached")
            
            if expired_count > 0:
                db.commit()
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Error marking expired requests: {e}")
            db.rollback()
            return 0

# Create global scheduler instance
scheduler_service = SchedulerService()

# Background task runner
async def run_background_scheduler():
    """Function to run the scheduler in the background"""
    await scheduler_service.start_scheduler()

# Manual trigger for testing
async def trigger_scheduled_tasks():
    """Manually trigger scheduled tasks (for testing)"""
    try:
        db = next(get_db())
        
        emails_sent = await scheduler_service.check_resume_update_emails(db)
        expired_count = await scheduler_service.mark_expired_requests(db)
        
        db.close()
        
        return {
            "success": True,
            "emails_sent": emails_sent,
            "expired_requests": expired_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in manual trigger: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

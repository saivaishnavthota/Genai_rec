from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, date, time, timedelta
from ..models.application import Application
from ..models.interview_schedule import InterviewSchedule
from ..models.interview_review import InterviewReview
from ..models.interviewer_token import InterviewerToken
from ..models.user import User
from ..config import settings
from ..utils.interview_emails import (
    send_candidate_selection_email,
    send_hr_notification_email,
    send_availability_request_email,
    send_interview_confirmation_email
)
from .google_calendar_service import google_calendar_service
import logging
import json

logger = logging.getLogger(__name__)

class InterviewService:
    def __init__(self):
        self.shortlist_threshold = settings.shortlist_threshold
    
    def generate_interview_slots(self, start_date: date, weeks: int = 2) -> List[dict]:
        """
        Generate available slots Mon-Fri, 12 PM - 6 PM
        Starting 1 week after selection email
        """
        slots = []
        current_date = start_date + timedelta(days=7)  # Start 1 week later
        end_date = current_date + timedelta(weeks=weeks)
        
        while current_date < end_date:
            # Only Monday to Friday (0-4)
            if current_date.weekday() < 5:
                # 12 PM to 6 PM (6 slots per day)
                for hour in range(12, 18):
                    slots.append({
                        "date": current_date.isoformat(),
                        "time": f"{hour:02d}:00",
                        "available": True,
                        "display": f"{current_date.strftime('%A, %B %d')} at {hour}:00 PM",
                        "datetime_display": f"{current_date.strftime('%Y-%m-%d')} {hour:02d}:00"
                    })
            current_date += timedelta(days=1)
        
        return slots
    
    async def trigger_selection_flow(self, db: Session, application: Application) -> bool:
        """
        Trigger the selection flow for candidates with score ≥70
        Send emails to candidate and HR
        """
        try:
            # Send candidate selection email
            try:
                candidate_success = send_candidate_selection_email(
                    application.email,
                    application.full_name,
                    application.job.title
                )
                if candidate_success:
                    application.selection_email_sent_at = datetime.utcnow()
                    logger.info(f"Selection email sent to candidate: {application.email}")
            except Exception as e:
                logger.warning(f"Candidate email failed but continuing: {e}")
                candidate_success = False
            
            # Send HR notification emails
            hr_users = db.query(User).filter(
                User.user_type == 'hr',
                User.company_id == application.job.company_id
            ).all()
            
            hr_success = False
            for hr_user in hr_users:
                try:
                    success = send_hr_notification_email(
                        hr_user.email,
                        application.full_name,
                        application.job.title,
                        application.id
                    )
                    if success:
                        hr_success = True
                except Exception as e:
                    logger.warning(f"HR email to {hr_user.email} failed but continuing: {e}")
            
            if hr_success:
                application.hr_notification_sent_at = datetime.utcnow()
                logger.info(f"HR notification emails sent for application: {application.id}")
            
            db.commit()
            # Return True for testing even if emails fail
            return True
            
        except Exception as e:
            logger.error(f"Error in selection flow for application {application.id}: {e}")
            db.rollback()
            return False
    
    async def fetch_availability_slots(self, db: Session, application_id: int) -> dict:
        """
        HR clicks 'Fetch Availability' - generate slots and send to candidate
        """
        try:
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                raise ValueError(f"Application {application_id} not found")
            
            # Check if interview schedule already exists
            interview_schedule = db.query(InterviewSchedule).filter(
                InterviewSchedule.application_id == application_id
            ).first()
            
            if not interview_schedule:
                # Create new interview schedule
                interview_schedule = InterviewSchedule(
                    application_id=application_id,
                    status="pending"
                )
                db.add(interview_schedule)
                db.flush()  # Get the ID
            
            # Generate available slots
            today = date.today()
            available_slots = self.generate_interview_slots(today)
            
            # Update interview schedule
            interview_schedule.availability_requested_at = datetime.utcnow()
            interview_schedule.available_slots = available_slots
            interview_schedule.slots_generated_from = today + timedelta(days=7)
            interview_schedule.slots_generated_to = today + timedelta(days=21)
            
            # Send availability request email to candidate
            try:
                email_success = send_availability_request_email(
                    application.email,
                    application.full_name,
                    application.job.title,
                    available_slots,
                    application_id  # Used as token for slot selection
                )
            except Exception as e:
                logger.warning(f"Email sending failed but continuing: {e}")
                email_success = False
            
            # Update application status regardless of email success (for testing)
            application.status = "availability_requested"
            db.commit()
            
            return {
                "success": True,
                "message": "Availability slots generated" + (" and sent to candidate" if email_success else " (email failed)"),
                "slots_count": len(available_slots),
                "slots_from": interview_schedule.slots_generated_from,
                "slots_to": interview_schedule.slots_generated_to,
                "email_sent": email_success
            }
            
        except Exception as e:
            logger.error(f"Error fetching availability for application {application_id}: {e}")
            db.rollback()
            return {"success": False, "message": str(e)}
    
    async def process_slot_selection(self, db: Session, application_id: int, selected_date: str, selected_time: str) -> dict:
        """
        Process candidate's slot selection
        """
        try:
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                raise ValueError(f"Application {application_id} not found")
            
            interview_schedule = db.query(InterviewSchedule).filter(
                InterviewSchedule.application_id == application_id
            ).first()
            
            if not interview_schedule:
                raise ValueError(f"Interview schedule not found for application {application_id}")
            
            # Parse and validate the selected slot
            try:
                slot_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
                slot_time = datetime.strptime(selected_time, "%H:%M").time()
            except ValueError as e:
                raise ValueError(f"Invalid date/time format: {e}")
            
            # Update interview schedule with selection
            interview_schedule.selected_slot_date = slot_date
            interview_schedule.selected_slot_time = slot_time
            interview_schedule.candidate_selected_at = datetime.utcnow()
            
            # Update application status
            application.status = "slot_selected"
            
            db.commit()
            
            return {
                "success": True,
                "message": "Interview slot selected successfully",
                "selected_date": selected_date,
                "selected_time": selected_time
            }
            
        except Exception as e:
            logger.error(f"Error processing slot selection for application {application_id}: {e}")
            db.rollback()
            return {"success": False, "message": str(e)}
    
    async def schedule_interview(self, db: Session, application_id: int, interviewer_data: dict) -> dict:
        """
        HR schedules interview with primary and backup interviewers including Google Meet integration
        """
        try:
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                raise ValueError(f"Application {application_id} not found")
            
            interview_schedule = db.query(InterviewSchedule).filter(
                InterviewSchedule.application_id == application_id
            ).first()
            
            if not interview_schedule or not interview_schedule.selected_slot_date:
                raise ValueError(f"No slot selected for application {application_id}")
            
            # Update interview schedule with interviewer details
            interview_schedule.primary_interviewer_name = interviewer_data.get("primary_interviewer_name")
            interview_schedule.primary_interviewer_email = interviewer_data.get("primary_interviewer_email")
            interview_schedule.backup_interviewer_name = interviewer_data.get("backup_interviewer_name")
            interview_schedule.backup_interviewer_email = interviewer_data.get("backup_interviewer_email")
            interview_schedule.interview_scheduled_at = datetime.utcnow()
            interview_schedule.status = "confirmed"
            
            # Create Google Calendar/Meet integration
            google_meet_result = None
            
            if google_calendar_service.is_available():
                try:
                    # Format datetime for Google Calendar API
                    start_time_formatted = f"{interview_schedule.selected_slot_date.strftime('%Y-%m-%d')} {interview_schedule.selected_slot_time.strftime('%H:%M')}"
                    
                    google_meet_result = google_calendar_service.create_interview_meeting(
                        candidate_email=application.email,
                        candidate_name=application.full_name,
                        primary_interviewer_email=interview_schedule.primary_interviewer_email,
                        primary_interviewer_name=interview_schedule.primary_interviewer_name,
                        backup_interviewer_email=interview_schedule.backup_interviewer_email,
                        backup_interviewer_name=interview_schedule.backup_interviewer_name,
                        interview_date=interview_schedule.selected_slot_date.strftime('%Y-%m-%d'),
                        interview_time=interview_schedule.selected_slot_time.strftime('%H:%M'),
                        interview_duration=interview_schedule.interview_duration,
                        application_id=application.id,
                        job_title=application.job.title
                    )
                    
                    if google_meet_result.get("success"):
                        interview_schedule.google_meet_link = google_meet_result.get("meet_link")
                        interview_schedule.google_calendar_event_id = google_meet_result.get("calendar_event_id")
                        interview_schedule.google_meet_created = datetime.utcnow()
                        logger.info(f"Google Calendar/Meet event created for application {application_id}: {google_meet_result.get('meet_link')}")
                    else:
                        logger.warning(f"Google Calendar/Meet creation failed: {google_meet_result.get('error')}")
                        
                except Exception as e:
                    logger.warning(f"Google Calendar/Meet integration failed but continuing: {e}")
                    google_meet_result = {
                        "success": False,
                        "error": str(e),
                        "meet_link": None,
                        "event_id": None
                    }
            else:
                logger.warning("Google Calendar service not available - OAuth credentials not configured")
                logger.info("To enable automatic Google Calendar/Meet creation:")
                logger.info("1. Set up OAuth credentials (credentials.json) or service account")
                logger.info("2. Configure environment variables in .env")
                logger.info("3. Restart the backend")
                
                # Without API access, we cannot create meeting rooms automatically
                google_meet_result = {
                    "success": False,
                    "error": "Google Calendar API not configured - manual meeting creation required",
                    "meet_link": None,
                    "event_id": None,
                    "requires_manual_setup": True
                }
            
            # Prepare interview details
            interview_details = {
                "candidate_name": application.full_name,
                "candidate_email": application.email,
                "job_title": application.job.title,
                "interview_date": interview_schedule.selected_slot_date.strftime("%Y-%m-%d"),  # Raw format for calendar
                "interview_time": interview_schedule.selected_slot_time.strftime("%H:%M"),     # Raw format for calendar
                "interview_date_display": interview_schedule.selected_slot_date.strftime("%A, %B %d, %Y"),  # Display format
                "interview_time_display": interview_schedule.selected_slot_time.strftime("%I:%M %p"),       # Display format
                "primary_interviewer": interview_schedule.primary_interviewer_name,
                "primary_interviewer_email": interview_schedule.primary_interviewer_email,
                "backup_interviewer": interview_schedule.backup_interviewer_name,
                "backup_interviewer_email": interview_schedule.backup_interviewer_email,
                "duration": interview_schedule.interview_duration,
                "google_meet_link": interview_schedule.google_meet_link,
                "google_calendar_event_id": interview_schedule.google_calendar_event_id
            }
            
            # Send confirmation emails with graceful error handling
            candidate_success = False
            primary_success = False
            backup_success = False
            
            try:
                candidate_success = send_interview_confirmation_email(
                    application.email,
                    "candidate",
                    interview_details
                )
            except Exception as e:
                logger.warning(f"Candidate email failed but continuing: {e}")
            
            try:
                primary_success = send_interview_confirmation_email(
                    interview_schedule.primary_interviewer_email,
                    "interviewer",
                    interview_details
                )
            except Exception as e:
                logger.warning(f"Primary interviewer email failed but continuing: {e}")
            
            if interview_schedule.backup_interviewer_email:
                try:
                    backup_success = send_interview_confirmation_email(
                        interview_schedule.backup_interviewer_email,
                        "interviewer",
                        interview_details
                    )
                except Exception as e:
                    logger.warning(f"Backup interviewer email failed but continuing: {e}")
            
            # Update application status regardless of email success (for testing)
            application.status = "interview_confirmed"
            application.interview_schedule_id = interview_schedule.id
            
            db.commit()
            
            # Prepare response message
            email_status = " (emails failed)" if not (candidate_success or primary_success) else ""
            google_meet_status = ""
            if google_meet_result:
                if google_meet_result["success"]:
                    google_meet_status = " with Google Meet integration"
                else:
                    google_meet_status = " (Google Meet failed)"
            
            return {
                "success": True,
                "message": f"Interview scheduled successfully{google_meet_status}{email_status}",
                "interview_details": interview_details,
                "google_meet": google_meet_result,
                "emails_sent": {
                    "candidate": candidate_success,
                    "primary_interviewer": primary_success,
                    "backup_interviewer": backup_success
                }
            }
                
        except Exception as e:
            logger.error(f"Error scheduling interview for application {application_id}: {e}")
            db.rollback()
            return {"success": False, "message": str(e)}
    
    async def mark_interview_completed(self, db: Session, application_id: int) -> dict:
        """
        HR marks interview as completed and automatically sends review tokens
        """
        try:
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                raise ValueError(f"Application {application_id} not found")
            
            interview_schedule = db.query(InterviewSchedule).filter(
                InterviewSchedule.application_id == application_id
            ).first()
            
            if interview_schedule:
                interview_schedule.status = "completed"
            
            # Update application status
            application.status = "interview_completed"
            
            db.commit()
            
            # Automatically send review tokens to interviewers
            logger.info(f"Automatically sending review tokens for completed interview (application {application_id})")
            review_result = await self.send_review_tokens_after_interview(db, application_id, skip_time_check=True)
            
            if review_result["success"]:
                return {
                    "success": True,
                    "message": f"Interview marked as completed and review tokens sent successfully! {review_result['tokens_created']} tokens created, {review_result['emails_sent']} emails sent.",
                    "review_tokens": review_result
                }
            else:
                # Interview marked as completed but review tokens failed
                logger.warning(f"Interview marked as completed but review token sending failed: {review_result['message']}")
                return {
                    "success": True,
                    "message": f"Interview marked as completed, but review token sending failed: {review_result['message']}",
                    "review_tokens": review_result
                }
            
        except Exception as e:
            logger.error(f"Error marking interview completed for application {application_id}: {e}")
            db.rollback()
            return {"success": False, "message": str(e)}
    
    def get_interview_details(self, db: Session, application_id: int) -> Optional[dict]:
        """
        Get interview details for an application
        """
        try:
            interview_schedule = db.query(InterviewSchedule).filter(
                InterviewSchedule.application_id == application_id
            ).first()
            
            if not interview_schedule:
                return None
            
            return {
                "id": interview_schedule.id,
                "application_id": interview_schedule.application_id,
                "status": interview_schedule.status,
                "selected_slot_date": interview_schedule.selected_slot_date.isoformat() if interview_schedule.selected_slot_date else None,
                "selected_slot_time": interview_schedule.selected_slot_time.strftime("%H:%M") if interview_schedule.selected_slot_time else None,
                "primary_interviewer_name": interview_schedule.primary_interviewer_name,
                "primary_interviewer_email": interview_schedule.primary_interviewer_email,
                "backup_interviewer_name": interview_schedule.backup_interviewer_name,
                "backup_interviewer_email": interview_schedule.backup_interviewer_email,
                "interview_duration": interview_schedule.interview_duration,
                "google_meet_link": interview_schedule.google_meet_link,
                "google_calendar_event_id": interview_schedule.google_calendar_event_id,
                "availability_requested_at": interview_schedule.availability_requested_at.isoformat() if interview_schedule.availability_requested_at else None,
                "candidate_selected_at": interview_schedule.candidate_selected_at.isoformat() if interview_schedule.candidate_selected_at else None,
                "interview_scheduled_at": interview_schedule.interview_scheduled_at.isoformat() if interview_schedule.interview_scheduled_at else None,
                "available_slots": interview_schedule.available_slots
            }
            
        except Exception as e:
            logger.error(f"Error getting interview details for application {application_id}: {e}")
            return None
    
    async def send_review_tokens_after_interview(self, db: Session, application_id: int, skip_time_check: bool = False) -> dict:
        """Send review tokens to interviewers after interview completion"""
        try:
            # Get interview schedule
            interview_schedule = db.query(InterviewSchedule).filter(
                InterviewSchedule.application_id == application_id
            ).first()
            
            if not interview_schedule:
                return {"success": False, "message": "Interview schedule not found"}
            
            # Check if interview slot is selected
            if not interview_schedule.selected_slot_date or not interview_schedule.selected_slot_time:
                return {"success": False, "message": "Interview slot not selected"}
            
            # Check if interview time has passed (unless skipped)
            if not skip_time_check:
                # Combine date and time
                interview_datetime = datetime.combine(
                    interview_schedule.selected_slot_date,
                    interview_schedule.selected_slot_time
                )
                
                # Add interview duration to get end time
                interview_end_time = interview_datetime + timedelta(minutes=interview_schedule.interview_duration)
                
                # Check if interview has ended
                if datetime.utcnow() < interview_end_time:
                    return {"success": False, "message": "Interview has not completed yet"}
            
            # Get application details
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                return {"success": False, "message": "Application not found"}
            
            tokens_created = []
            
            # Create token for primary interviewer
            if interview_schedule.primary_interviewer_email:
                # Check if token already exists
                existing_token = db.query(InterviewerToken).filter(
                    InterviewerToken.application_id == application_id,
                    InterviewerToken.interviewer_email == interview_schedule.primary_interviewer_email,
                    InterviewerToken.interviewer_type == "primary"
                ).first()
                
                if not existing_token:
                    primary_token = InterviewerToken.create_token(
                        interviewer_email=interview_schedule.primary_interviewer_email,
                        interviewer_name=interview_schedule.primary_interviewer_name,
                        application_id=application_id,
                        interviewer_type="primary"
                    )
                    db.add(primary_token)
                    tokens_created.append({
                        "email": interview_schedule.primary_interviewer_email,
                        "name": interview_schedule.primary_interviewer_name,
                        "type": "primary",
                        "token": primary_token.token
                    })
            
            # Create token for backup interviewer
            if interview_schedule.backup_interviewer_email:
                # Check if token already exists
                existing_token = db.query(InterviewerToken).filter(
                    InterviewerToken.application_id == application_id,
                    InterviewerToken.interviewer_email == interview_schedule.backup_interviewer_email,
                    InterviewerToken.interviewer_type == "backup"
                ).first()
                
                if not existing_token:
                    backup_token = InterviewerToken.create_token(
                        interviewer_email=interview_schedule.backup_interviewer_email,
                        interviewer_name=interview_schedule.backup_interviewer_name,
                        application_id=application_id,
                        interviewer_type="backup"
                    )
                    db.add(backup_token)
                    tokens_created.append({
                        "email": interview_schedule.backup_interviewer_email,
                        "name": interview_schedule.backup_interviewer_name,
                        "type": "backup",
                        "token": backup_token.token
                    })
            
            db.commit()
            
            # Send review emails
            emails_sent = 0
            for token_info in tokens_created:
                try:
                    success = await self._send_review_token_email(
                        token_info["email"],
                        token_info["name"],
                        token_info["token"],
                        application.full_name,
                        application.job.title,
                        token_info["type"]
                    )
                    if success:
                        emails_sent += 1
                except Exception as e:
                    logger.warning(f"Failed to send review email to {token_info['email']}: {e}")
            
            return {
                "success": True,
                "message": f"Review tokens created and {emails_sent} emails sent",
                "tokens_created": len(tokens_created),
                "emails_sent": emails_sent
            }
            
        except Exception as e:
            logger.error(f"Error sending review tokens for application {application_id}: {e}")
            db.rollback()
            return {"success": False, "message": "Failed to send review tokens"}
    
    async def _send_review_token_email(
        self, 
        interviewer_email: str, 
        interviewer_name: str, 
        token: str, 
        candidate_name: str, 
        job_title: str,
        interviewer_type: str
    ) -> bool:
        """Send review token email to interviewer"""
        try:
            from ..utils.email import send_email
            
            review_url = f"{settings.frontend_url}/interviewer-review/{token}"
            
            subject = f"Interview Review Required - {candidate_name} for {job_title}"
            
            body = f"""
Dear {interviewer_name},

Thank you for conducting the interview for {candidate_name} for the {job_title} position.

🔐 INTERVIEW REVIEW ACCESS
==========================

You have been provided with secure access to submit your interview review. No additional login credentials are required.

REVIEW LINK: {review_url}
⏰ This link is valid for 24 hours only
🔒 This is a one-time use secure link

HOW TO ACCESS:
1. Click the review link above (or copy and paste it into your browser)
2. The system will automatically authenticate you using this secure token
3. Complete the review form with your evaluation
4. Submit the review - no username/password required

EVALUATION CRITERIA:
- Technical Skills & Knowledge (1-10 scale)
- Communication & Presentation (1-10 scale) 
- Problem-Solving Ability (1-10 scale)
- Cultural Fit & Team Collaboration (1-10 scale)
- Leadership Potential (1-10 scale)
- Overall Rating (1-10 scale)
- Key Strengths (detailed feedback)
- Areas for Improvement (detailed feedback)
- Overall Recommendation (Hire/Maybe/Reject)

IMPORTANT NOTES:
• No separate login credentials needed - the link contains your authentication
• The review form will be pre-populated with candidate and job information
• Please provide detailed, constructive feedback to help us make the best hiring decision
• If the link doesn't work, please contact HR immediately

If you have any questions or technical issues, please contact HR.

Best regards,
GenAI Hiring Team
            """
            
            html_body = f"""
            <html>
                <body>
                    <h2 style="color: #2563eb;">Interview Review Required</h2>
                    <p>Dear {interviewer_name},</p>
                    <p>Thank you for conducting the interview for <strong>{candidate_name}</strong> for the <strong>{job_title}</strong> position.</p>
                    
                    <div style="background-color: #dcfce7; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #16a34a;">
                        <h3 style="color: #16a34a; margin: 0 0 15px 0;">🔒 Secure Access Provided</h3>
                        <p style="margin: 0 0 10px 0;"><strong>No additional login credentials are required.</strong></p>
                        <p style="margin: 0;">Click the button below to access your personalized review form:</p>
                    </div>
                    
                    <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                        <h3 style="margin: 0 0 15px 0;">Submit Your Review</h3>
                        <p><a href="{review_url}" style="background-color: #2563eb; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold;">🔗 Access Review Form</a></p>
                        <p style="font-size: 12px; color: #6b7280; margin: 10px 0 0 0;">⏰ Valid for 24 hours only | 🔒 One-time use secure link</p>
                    </div>
                    
                    <div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin: 0 0 10px 0;">📋 How to Access:</h3>
                        <ol style="margin: 0; padding-left: 20px;">
                            <li>Click the "Access Review Form" button above</li>
                            <li>The system will automatically authenticate you using the secure token</li>
                            <li>Complete the review form with your evaluation</li>
                            <li>Submit the review - no username/password required</li>
                        </ol>
                    </div>
                    
                    <div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h3>Evaluation Criteria:</h3>
                        <ul>
                            <li>Technical Skills & Knowledge (1-10 scale)</li>
                            <li>Communication & Presentation (1-10 scale)</li>
                            <li>Problem-Solving Ability (1-10 scale)</li>
                            <li>Cultural Fit & Team Collaboration (1-10 scale)</li>
                            <li>Leadership Potential (1-10 scale)</li>
                            <li>Overall Recommendation (Hire/Reject/Maybe)</li>
                        </ul>
                    </div>
                    
                    <div style="background-color: #fee2e2; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ef4444;">
                        <h3 style="color: #dc2626; margin: 0 0 10px 0;">⚠️ Important Notes:</h3>
                        <ul style="margin: 0; padding-left: 20px; color: #7f1d1d;">
                            <li>No separate login credentials needed - the link contains your authentication</li>
                            <li>The review form will be pre-populated with candidate and job information</li>
                            <li>Please provide detailed, constructive feedback</li>
                            <li>If the link doesn't work, contact HR immediately</li>
                        </ul>
                    </div>
                    
                    <p>Please provide detailed feedback to help us make the best hiring decision.</p>
                    <p>If you have any questions or technical issues, please contact HR.</p>
                    
                    <br>
                    <p>Best regards,<br><strong>GenAI Hiring Team</strong></p>
                </body>
            </html>
            """
            
            return send_email([interviewer_email], subject, body, html_body)
            
        except Exception as e:
            logger.error(f"Error sending review token email: {e}")
            return False

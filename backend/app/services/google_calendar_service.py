import os
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

# Python 3.9+ stdlib timezone support
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # For Python <3.9: pip install backports.zoneinfo and import from backports.zoneinfo
    from backports.zoneinfo import ZoneInfo  # type: ignore

from google.oauth2.service_account import Credentials as SA_Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from ..config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_calendar_service():
    """
    Returns an authenticated Google Calendar service using either:
    - OAuth client credentials (credentials.json) and token.json (after first consent), or
    - Workspace Service Account with domain-wide delegation.
    """
    use_service_account = getattr(settings, 'use_service_account', False)

    if use_service_account:
        sa_path = getattr(settings, 'service_account_file', 'service_account.json')
        impersonate_user = getattr(settings, 'impersonate_user', None)
        if not os.path.exists(sa_path):
            raise FileNotFoundError("Missing service account key file at SERVICE_ACCOUNT_FILE path.")
        if not impersonate_user:
            raise ValueError("IMPERSONATE_USER is required for domain-wide delegation.")

        creds = SA_Credentials.from_service_account_file(
            sa_path,
            scopes=SCOPES,
            subject=impersonate_user,
        )
        return build("calendar", "v3", credentials=creds)

    # OAuth installed app flow
    token_path = getattr(settings, 'token_file', 'token.json')
    creds = None
    if os.path.exists(token_path):
        # Reuse existing token
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save token for next runs (headless thereafter)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def schedule_google_meet(
    subject: str,
    start_time_local: str,
    duration_minutes: int,
    attendees: List[str],
    timezone_str: str = "Asia/Kolkata",
    description: Optional[str] = None,
    calendar_id: str = "primary",
) -> dict:
    """
    Create a Calendar event with a Google Meet link and email the invites.

    Args:
        subject: Event title.
        start_time_local: Start in '%Y-%m-%d %H:%M' (e.g., '2025-10-02 16:30') in the given timezone.
        duration_minutes: Meeting length.
        attendees: List of attendee email strings.
        timezone_str: IANA timezone (default 'Asia/Kolkata').
        description: Optional event description.
        calendar_id: Calendar to insert into (default 'primary').

    Returns:
        The created event resource (dict). Includes 'hangoutLink' (Meet URL).
    """
    tz = ZoneInfo(timezone_str)
    start_dt = datetime.strptime(start_time_local, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    event_body = {
        "summary": subject,
        "description": description or "",
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": timezone_str,
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": timezone_str,
        },
        # Add attendees
        "attendees": [{"email": e.strip()} for e in attendees if e.strip()],
        # Auto-generate a Google Meet link
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
        # Optional reminders
        "reminders": {
            "useDefault": True
        },
    }

    service = get_calendar_service()

    # sendUpdates='all' ensures Google emails the invites to all attendees
    event = (
        service.events()
        .insert(
            calendarId=calendar_id,
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates="all",
        )
        .execute()
    )

    return event


class GoogleCalendarService:
    def __init__(self):
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Calendar service with authentication."""
        try:
            self.service = get_calendar_service()
            logger.info("Google Calendar service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar service: {e}")
            self.service = None
    
    def is_available(self) -> bool:
        """Check if Google Calendar service is available."""
        try:
            # Try to create a service if not available
            if self.service is None:
                self.service = get_calendar_service()
            return self.service is not None
        except Exception as e:
            logger.error(f"Google Calendar service not available: {e}")
            return False
    
    def create_interview_meeting(
        self,
        candidate_email: str,
        candidate_name: str,
        primary_interviewer_email: str,
        primary_interviewer_name: str,
        backup_interviewer_email: Optional[str],
        backup_interviewer_name: Optional[str],
        interview_date: str,
        interview_time: str,
        interview_duration: int,
        application_id: int,
        job_title: str
    ) -> Dict[str, Any]:
        """
        Create a Google Calendar event with Meet link for interview using the working schedule_google_meet function.
        
        Args:
            candidate_email: Candidate's email
            candidate_name: Candidate's name
            primary_interviewer_email: Primary interviewer's email
            primary_interviewer_name: Primary interviewer's name
            backup_interviewer_email: Backup interviewer's email
            backup_interviewer_name: Backup interviewer's name
            interview_date: Interview date (YYYY-MM-DD)
            interview_time: Interview time (HH:MM)
            duration_minutes: Interview duration in minutes
            job_title: Job title for the interview
            
        Returns:
            Dict containing meeting details including Google Meet link
        """
        try:
            # Prepare attendees
            attendees = [
                candidate_email,
                primary_interviewer_email
            ]
            if backup_interviewer_email:
                attendees.append(backup_interviewer_email)
            
            # Create meeting subject and description
            subject = f"Interview: {candidate_name} - {job_title}"
            description_parts = [
                "Interview Details:",
                f"- Candidate: {candidate_name} ({candidate_email})",
                f"- Position: {job_title}",
                f"- Primary Interviewer: {primary_interviewer_name} ({primary_interviewer_email})"
            ]
            
            if backup_interviewer_name and backup_interviewer_email:
                description_parts.append(f"- Backup Interviewer: {backup_interviewer_name} ({backup_interviewer_email})")
            
            description_parts.extend([
                f"- Duration: {interview_duration} minutes",
                f"- Application ID: {application_id}",
                "",
                "This is an automated interview scheduled through the GenAI Hiring System.",
                "",
                "🎥 Google Meet Link: Available in this calendar event",
                "📧 All participants will receive calendar invites automatically", 
                "⏰ Please join the meeting on time",
                "",
                "For technical support, contact HR."
            ])
            
            description = "\n".join(description_parts)
            
            # Format start time
            start_time_local = f"{interview_date} {interview_time}"
            
            # Create the calendar event with Google Meet using the working function
            event = schedule_google_meet(
                subject=subject,
                start_time_local=start_time_local,
                duration_minutes=interview_duration,
                attendees=attendees,
                timezone_str=settings.meet_timezone,
                description=description,
                calendar_id=settings.meet_calendar_id
            )
            
            # Extract meeting details
            meet_link = event.get("hangoutLink")
            calendar_event_id = event.get("id")
            
            logger.info(f"Successfully created Google Meet for interview: {meet_link}")
            
            return {
                "success": True,
                "meet_link": meet_link,
                "calendar_event_id": calendar_event_id,
                "event_url": event.get("htmlLink"),
                "start_time": event["start"]["dateTime"],
                "end_time": event["end"]["dateTime"]
            }
            
        except Exception as e:
            logger.error(f"Failed to create Google Meet interview: {e}")
            return {
                "success": False,
                "error": str(e),
                "meet_link": None,
                "calendar_event_id": None
            }

# Create a global instance
google_calendar_service = GoogleCalendarService()
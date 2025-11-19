import uuid
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def generate_ics_content(
    title: str,
    description: str,
    start_datetime: datetime,
    end_datetime: datetime,
    location: str = "Video Call",
    organizer_email: str = "hr@company.com",
    organizer_name: str = "HR Team",
    attendees: list = None
) -> str:
    """Generate ICS (iCalendar) content for email attachments"""
    
    if attendees is None:
        attendees = []
    
    # Generate unique UID
    event_uid = str(uuid.uuid4())
    
    # Format datetime for ICS (UTC format)
    def format_datetime(dt):
        return dt.strftime("%Y%m%dT%H%M%SZ")
    
    # Current timestamp
    now = datetime.utcnow()
    
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//GenAI Recruitment//Interview Scheduler//EN
CALSCALE:GREGORIAN
METHOD:REQUEST
BEGIN:VEVENT
UID:{event_uid}
DTSTAMP:{format_datetime(now)}
DTSTART:{format_datetime(start_datetime)}
DTEND:{format_datetime(end_datetime)}
SUMMARY:{title}
DESCRIPTION:{description}
LOCATION:{location}
ORGANIZER;CN={organizer_name}:MAILTO:{organizer_email}
STATUS:CONFIRMED
SEQUENCE:0
PRIORITY:5"""

    # Add attendees
    for attendee in attendees:
        email = attendee.get('email', '')
        name = attendee.get('name', email)
        role = attendee.get('role', 'REQ-PARTICIPANT')
        ics_content += f"\nATTENDEE;CN={name};ROLE={role};PARTSTAT=NEEDS-ACTION;RSVP=TRUE:MAILTO:{email}"
    
    # Add reminder (15 minutes before)
    ics_content += """
BEGIN:VALARM
TRIGGER:-PT15M
ACTION:DISPLAY
DESCRIPTION:Interview Reminder
END:VALARM
END:VEVENT
END:VCALENDAR"""
    
    return ics_content

def create_interview_calendar_invite(
    candidate_name: str,
    candidate_email: str,
    job_title: str,
    interview_date: str,  # YYYY-MM-DD
    interview_time: str,  # HH:MM
    duration_minutes: int = 60,
    primary_interviewer_name: str = "",
    primary_interviewer_email: str = "",
    backup_interviewer_name: str = "",
    backup_interviewer_email: str = "",
    meeting_link: str = ""
) -> str:
    """Create calendar invite for interview"""
    
    try:
        # Parse datetime
        start_datetime = datetime.strptime(f"{interview_date} {interview_time}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        
        # Create title and description
        title = f"Interview: {job_title} - {candidate_name}"
        
        description = f"""Interview Details:
        
Position: {job_title}
Candidate: {candidate_name}
Date: {start_datetime.strftime('%A, %B %d, %Y')}
Time: {start_datetime.strftime('%I:%M %p')} - {end_datetime.strftime('%I:%M %p')}

Primary Interviewer: {primary_interviewer_name}
Backup Interviewer: {backup_interviewer_name or 'N/A'}

{f'Meeting Link: {meeting_link}' if meeting_link else 'Meeting details will be shared separately.'}

Please prepare to discuss:
- Technical skills and experience
- Problem-solving approach
- Career goals and motivation
- Questions about the role and company

For technical interviews, please be ready to:
- Share your screen if needed
- Discuss your previous projects
- Walk through code examples
- Solve technical problems

Contact HR if you have any questions or need to reschedule.
"""
        
        # Create attendees list
        attendees = [
            {'email': candidate_email, 'name': candidate_name, 'role': 'REQ-PARTICIPANT'},
            {'email': primary_interviewer_email, 'name': primary_interviewer_name, 'role': 'REQ-PARTICIPANT'}
        ]
        
        if backup_interviewer_email:
            attendees.append({
                'email': backup_interviewer_email, 
                'name': backup_interviewer_name, 
                'role': 'OPT-PARTICIPANT'
            })
        
        # Generate ICS content
        ics_content = generate_ics_content(
            title=title,
            description=description,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            location=meeting_link if meeting_link else "Video Call",
            attendees=attendees
        )
        
        return ics_content
        
    except Exception as e:
        logger.error(f"Error creating calendar invite: {e}")
        return ""

def create_ics_filename(candidate_name: str, job_title: str, interview_date: str) -> str:
    """Create a safe filename for the ICS file"""
    # Clean filename
    safe_candidate = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_job = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_')).strip()
    
    return f"Interview_{safe_candidate}_{safe_job}_{interview_date}.ics"

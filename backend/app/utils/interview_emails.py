from .email import send_email
from .calendar_utils import create_interview_calendar_invite, create_ics_filename
from ..config import settings
from datetime import date
import logging

logger = logging.getLogger(__name__)

def send_candidate_selection_email(candidate_email: str, candidate_name: str, job_title: str) -> bool:
    """Send selection notification email to candidate"""
    subject = f"🎉 Congratulations! You've been selected for {job_title}"
    
    body = f"""
Dear {candidate_name},

Congratulations! We are pleased to inform you that you have been SELECTED for the {job_title} position based on your excellent application and scoring.

Next Steps:
- Our HR team will contact you shortly to schedule an interview
- Please keep an eye on your email for interview scheduling details
- The interview will be conducted by our technical team

We look forward to meeting you soon!

Best regards,
GenAI Hiring Team
    """
    
    html_body = f"""
    <html>
        <body>
            <h2 style="color: #16a34a;">🎉 Congratulations!</h2>
            <p>Dear {candidate_name},</p>
            <p>We are pleased to inform you that you have been <strong>SELECTED</strong> for the <strong>{job_title}</strong> position based on your excellent application and scoring.</p>
            
            <h3>Next Steps:</h3>
            <ul>
                <li>Our HR team will contact you shortly to schedule an interview</li>
                <li>Please keep an eye on your email for interview scheduling details</li>
                <li>The interview will be conducted by our technical team</li>
            </ul>
            
            <p>We look forward to meeting you soon!</p>
            <br>
            <p>Best regards,<br><strong>GenAI Hiring Team</strong></p>
        </body>
    </html>
    """
    
    return send_email([candidate_email], subject, body, html_body)

def send_hr_notification_email(hr_email: str, candidate_name: str, job_title: str, application_id: int) -> bool:
    """Send HR notification email for selected candidate"""
    subject = f"🚨 Action Required: Schedule Interview for {candidate_name}"
    
    body = f"""
Dear HR Team,

A candidate has been automatically selected based on their high score (≥70%):

Candidate Details:
- Name: {candidate_name}
- Position: {job_title}
- Application ID: {application_id}

ACTION REQUIRED:
Please log into the HR dashboard and click "Fetch Availability" to proceed with interview scheduling.

Dashboard Link: {settings.frontend_url}/applications/{application_id}

Best regards,
GenAI Hiring System
    """
    
    html_body = f"""
    <html>
        <body>
            <h2 style="color: #dc2626;">🚨 Action Required</h2>
            <p>Dear HR Team,</p>
            <p>A candidate has been automatically selected based on their high score (≥70%):</p>
            
            <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h3>Candidate Details:</h3>
                <ul>
                    <li><strong>Name:</strong> {candidate_name}</li>
                    <li><strong>Position:</strong> {job_title}</li>
                    <li><strong>Application ID:</strong> {application_id}</li>
                </ul>
            </div>
            
            <p><strong>ACTION REQUIRED:</strong><br>
            Please log into the HR dashboard and click "Fetch Availability" to proceed with interview scheduling.</p>
            
            <p><a href="{settings.frontend_url}/applications/{application_id}" style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Application</a></p>
            
            <br>
            <p>Best regards,<br><strong>GenAI Hiring System</strong></p>
        </body>
    </html>
    """
    
    return send_email([hr_email], subject, body, html_body)

def send_availability_request_email(candidate_email: str, candidate_name: str, job_title: str, available_slots: list, application_id: int, slots_from: date = None, slots_to: date = None) -> bool:
    """Send availability request email with slots to candidate"""
    subject = f"Interview Scheduling - Please select your preferred time slot"
    
    # Format date range if provided
    date_range_text = ""
    date_range_html = ""
    if slots_from and slots_to:
        date_range_text = f"\nAvailable slots are from {slots_from.strftime('%B %d, %Y')} to {slots_to.strftime('%B %d, %Y')}.\n"
        date_range_html = f'<div style="background-color: #f0f9ff; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #2563eb;"><p style="margin: 0; color: #1e40af;"><strong>📅 Date Range:</strong> {slots_from.strftime("%B %d, %Y")} to {slots_to.strftime("%B %d, %Y")}</p></div>'
    
    # Format slots by week
    slots_text = ""
    for slot in available_slots[:20]:  # Limit to first 20 slots for email
        slots_text += f"{slot['display']}\n"
    
    body = f"""
Dear {candidate_name},

Thank you for your patience. We would like to schedule your interview for the {job_title} position.
{date_range_text}
Please select your preferred time slot from the available options below:

AVAILABLE SLOTS (All times are 1-hour interviews):
{slots_text}

To select your slot, please click here: {settings.frontend_url}/select-slot/{application_id}

If none of these slots work for you, please reply to this email with your preferred times.

Best regards,
GenAI Hiring Team
    """
    
    # Create HTML slots list
    slots_html = ""
    for slot in available_slots[:20]:
        slots_html += f"<li>{slot['display']}</li>"
    
    html_body = f"""
    <html>
        <body>
            <h2>Interview Scheduling</h2>
            <p>Dear {candidate_name},</p>
            <p>Thank you for your patience. We would like to schedule your interview for the <strong>{job_title}</strong> position.</p>
            
            {date_range_html}
            
            <p>Please select your preferred time slot from the available options below:</p>
            
            <h3>Available Slots (1-hour interviews):</h3>
            <ul style="line-height: 1.6;">
                {slots_html}
            </ul>
            
            <p><a href="{settings.frontend_url}/select-slot/{application_id}" style="background-color: #16a34a; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Select Your Slot</a></p>
            
            <p><em>If none of these slots work for you, please reply to this email with your preferred times.</em></p>
            
            <br>
            <p>Best regards,<br><strong>GenAI Hiring Team</strong></p>
        </body>
    </html>
    """
    
    return send_email([candidate_email], subject, body, html_body)

def send_interview_confirmation_email(recipient_email: str, recipient_type: str, interview_details: dict) -> bool:
    """Send interview confirmation email to candidate or interviewer"""
    
    # Handle case when Google Meet API is not configured
    manual_setup_instructions = """🎥 VIDEO CALL SETUP:

The interviewer will create a Google Meet and share the link with all participants before the interview.

Please check your email for the meeting link or contact HR if you don't receive it 15 minutes before the interview."""
    
    # HTML versions to avoid f-string backslash issues
    google_meet_html = '<div style="background-color: #dcfce7; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #16a34a; text-align: center;"><h3 style="color: #16a34a; margin: 0 0 15px 0;">🎥 Join Google Meet Interview</h3><a href="{}" style="background-color: #16a34a; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; font-size: 16px;">JOIN MEETING</a><p style="margin: 10px 0 5px 0; font-size: 14px; color: #374151;">Meeting Link: <a href="{}" style="color: #16a34a; text-decoration: underline;">{}</a></p><p style="margin: 0; font-size: 12px; color: #6b7280;">Click the button or link above to join at the scheduled time</p></div>'
    
    manual_setup_html = '<div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #6c757d;"><h3 style="color: #495057; margin: 0 0 15px 0;">🎥 Video Call Setup</h3><p style="margin: 0; color: #495057; text-align: left;">The interviewer will create a Google Meet and share the link with all participants before the interview.<br><br>Please check your email for the meeting link or contact HR if you don' + "'" + 't receive it 15 minutes before the interview.</p></div>'
    
    if recipient_type == "candidate":
        subject = f"Interview Confirmed - {interview_details['interview_date_display']} at {interview_details['interview_time_display']}"
        
        body = f"""
Dear {interview_details['candidate_name']},

Your interview has been confirmed with the following details:

INTERVIEW DETAILS:
- Position: {interview_details['job_title']}
- Date: {interview_details['interview_date_display']}
- Time: {interview_details['interview_time_display']} ({interview_details['duration']} minutes)
- Primary Interviewer: {interview_details['primary_interviewer']}
- Backup Interviewer: {interview_details['backup_interviewer']}

{f"🎥 GOOGLE MEET LINK: {interview_details['google_meet_link']}" if interview_details.get('google_meet_link') else manual_setup_instructions}

Please be prepared to discuss your technical skills, experience, and career goals.

Best regards,
GenAI Hiring Team
        """
        
        html_body = f"""
        <html>
            <body>
                <h2 style="color: #16a34a;">Interview Confirmed</h2>
                <p>Dear {interview_details['candidate_name']},</p>
                <p>Your interview has been confirmed with the following details:</p>
                
                <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Interview Details:</h3>
                    <ul>
                        <li><strong>Position:</strong> {interview_details['job_title']}</li>
                        <li><strong>Date:</strong> {interview_details['interview_date_display']}</li>
                        <li><strong>Time:</strong> {interview_details['interview_time_display']} ({interview_details['duration']} minutes)</li>
                        <li><strong>Primary Interviewer:</strong> {interview_details['primary_interviewer']}</li>
                        <li><strong>Backup Interviewer:</strong> {interview_details['backup_interviewer']}</li>
                    </ul>
                </div>
                
{google_meet_html.format(interview_details["google_meet_link"], interview_details["google_meet_link"], interview_details["google_meet_link"]) if interview_details.get('google_meet_link') else manual_setup_html}
                
                <p>Please be prepared to discuss your technical skills, experience, and career goals.</p>
                
                <br>
                <p>Best regards,<br><strong>GenAI Hiring Team</strong></p>
            </body>
        </html>
        """
        
    else:  # interviewer
        subject = f"Interview Assignment - {interview_details['candidate_name']} for {interview_details['job_title']}"
        
        body = f"""
Dear Interviewer,

You have been assigned to conduct an interview with the following details:

INTERVIEW DETAILS:
- Candidate: {interview_details['candidate_name']} ({interview_details['candidate_email']})
- Position: {interview_details['job_title']}
- Date: {interview_details['interview_date_display']}
- Time: {interview_details['interview_time_display']} ({interview_details['duration']} minutes)
- Backup Interviewer: {interview_details['backup_interviewer']}

{f"🎥 GOOGLE MEET LINK: {interview_details['google_meet_link']}" if interview_details.get('google_meet_link') else manual_setup_instructions}

EVALUATION CRITERIA:
Please assess the candidate on the following parameters (1-10 scale):
1. Technical Skills & Knowledge
2. Communication & Presentation
3. Problem-Solving Ability
4. Cultural Fit & Team Collaboration
5. Leadership Potential

REVIEW SUBMISSION:
After completing the interview, you will receive a temporary login link to submit your review through our online form. The review link will be sent only after the scheduled interview time has passed.

Best regards,
GenAI Hiring Team
        """
        
        html_body = f"""
        <html>
            <body>
                <h2 style="color: #2563eb;">Interview Assignment</h2>
                <p>Dear Interviewer,</p>
                <p>You have been assigned to conduct an interview with the following details:</p>
                
                <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Interview Details:</h3>
                    <ul>
                        <li><strong>Candidate:</strong> {interview_details['candidate_name']} ({interview_details['candidate_email']})</li>
                        <li><strong>Position:</strong> {interview_details['job_title']}</li>
                        <li><strong>Date:</strong> {interview_details['interview_date_display']}</li>
                        <li><strong>Time:</strong> {interview_details['interview_time_display']} ({interview_details['duration']} minutes)</li>
                        <li><strong>Backup Interviewer:</strong> {interview_details['backup_interviewer']}</li>
                    </ul>
                </div>
                
{google_meet_html.format(interview_details["google_meet_link"], interview_details["google_meet_link"], interview_details["google_meet_link"]) if interview_details.get('google_meet_link') else manual_setup_html}
                
                <div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3>Evaluation Criteria:</h3>
                    <p>Please assess the candidate on the following parameters (1-10 scale):</p>
                    <ol>
                        <li>Technical Skills & Knowledge</li>
                        <li>Communication & Presentation</li>
                        <li>Problem-Solving Ability</li>
                        <li>Cultural Fit & Team Collaboration</li>
                        <li>Leadership Potential</li>
                    </ol>
                </div>
                
                <div style="background-color: #dcfce7; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #16a34a;">
                    <h3 style="color: #16a34a; margin: 0 0 10px 0;">Review Submission</h3>
                    <p style="margin: 0;">After completing the interview, you will receive a temporary login link to submit your review through our online form. The review link will be sent only after the scheduled interview time has passed.</p>
                </div>
                
                <br>
                <p>Best regards,<br><strong>GenAI Hiring Team</strong></p>
            </body>
        </html>
        """
    
    # Create calendar invite for ALL recipients (candidate and interviewers)
    attachments = []
    try:
        ics_content = create_interview_calendar_invite(
            candidate_name=interview_details['candidate_name'],
            candidate_email=interview_details['candidate_email'],
            job_title=interview_details['job_title'],
            interview_date=interview_details['interview_date'],
            interview_time=interview_details['interview_time'],
            duration_minutes=int(interview_details['duration']),
            primary_interviewer_name=interview_details['primary_interviewer'],
            primary_interviewer_email=interview_details.get('primary_interviewer_email', ''),
            backup_interviewer_name=interview_details['backup_interviewer'],
            backup_interviewer_email=interview_details.get('backup_interviewer_email', ''),
            meeting_link=interview_details.get('google_meet_link', '')
        )
        
        if ics_content:
            filename = create_ics_filename(
                interview_details['candidate_name'],
                interview_details['job_title'],
                interview_details['interview_date']
            )
            attachments.append({
                'content': ics_content.encode('utf-8'),
                'filename': filename
            })
            logger.info(f"Calendar invite created for {recipient_type}: {filename}")
        else:
            logger.warning(f"Calendar invite content was empty for {recipient_type}")
    except Exception as e:
        logger.warning(f"Failed to create calendar invite for {recipient_type}: {e}")
    
    return send_email([recipient_email], subject, body, html_body, attachments)

def send_ai_interview_invitation_email(
    candidate_email: str,
    candidate_name: str,
    job_title: str,
    interview_link: str
) -> bool:
    """Send AI interview invitation email to candidate with interview link"""
    subject = f"🎥 AI Interview Invitation - {job_title}"
    
    body = f"""
Dear {candidate_name},

We are pleased to invite you to complete an AI-powered interview for the {job_title} position.

INTERVIEW DETAILS:
- Position: {job_title}
- Interview Type: AI-Powered Video Interview
- Duration: Approximately 2 minutes (2 questions, 1 minute each)
- Format: You will answer personalized questions based on your resume and the job requirements

INTERVIEW LINK:
{interview_link}

IMPORTANT INSTRUCTIONS:
1. Click the link above to start your interview
2. Ensure you have a working camera and microphone
3. Find a quiet, well-lit environment
4. You will have 1 minute to answer each question
5. The interview will be automatically recorded for review

PREPARATION TIPS:
- Review the job description before starting
- Have your resume handy for reference
- Test your camera and microphone beforehand
- Ensure a stable internet connection

If you experience any technical issues, please contact our HR team immediately.

Best regards,
GenAI Hiring Team
    """
    
    html_body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">🎥 AI Interview Invitation</h2>
                <p>Dear {candidate_name},</p>
                <p>We are pleased to invite you to complete an <strong>AI-powered interview</strong> for the <strong>{job_title}</strong> position.</p>
                
                <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563eb;">
                    <h3 style="color: #2563eb; margin: 0 0 15px 0;">Interview Details:</h3>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li><strong>Position:</strong> {job_title}</li>
                        <li><strong>Interview Type:</strong> AI-Powered Video Interview</li>
                        <li><strong>Duration:</strong> Approximately 2 minutes (2 questions, 1 minute each)</li>
                        <li><strong>Format:</strong> You will answer personalized questions based on your resume and the job requirements</li>
                    </ul>
                </div>
                
                <div style="background-color: #dcfce7; padding: 25px; border-radius: 8px; margin: 25px 0; text-align: center; border: 2px solid #16a34a;">
                    <h3 style="color: #16a34a; margin: 0 0 15px 0;">🚀 Start Your Interview</h3>
                    <p style="margin: 0 0 20px 0; font-size: 14px; color: #374151;">Click the button below to begin your AI interview:</p>
                    <a href="{interview_link}" style="background-color: #16a34a; color: white; padding: 15px 30px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; font-size: 16px;">START INTERVIEW</a>
                    <p style="margin: 15px 0 0 0; font-size: 12px; color: #6b7280;">Or copy this link: <a href="{interview_link}" style="color: #2563eb; word-break: break-all;">{interview_link}</a></p>
                </div>
                
                <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                    <h3 style="color: #92400e; margin: 0 0 15px 0;">⚠️ Important Instructions:</h3>
                    <ol style="margin: 0; padding-left: 20px; color: #78350f;">
                        <li>Click the link above to start your interview</li>
                        <li>Ensure you have a working camera and microphone</li>
                        <li>Find a quiet, well-lit environment</li>
                        <li>You will have 1 minute to answer each question</li>
                        <li>The interview will be automatically recorded for review</li>
                    </ol>
                </div>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin: 0 0 15px 0;">💡 Preparation Tips:</h3>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>Review the job description before starting</li>
                        <li>Have your resume handy for reference</li>
                        <li>Test your camera and microphone beforehand</li>
                        <li>Ensure a stable internet connection</li>
                    </ul>
                </div>
                
                <p style="color: #6b7280; font-size: 14px;">If you experience any technical issues, please contact our HR team immediately.</p>
                
                <br>
                <p>Best regards,<br><strong>GenAI Hiring Team</strong></p>
            </div>
        </body>
    </html>
    """
    
    return send_email([candidate_email], subject, body, html_body)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from ..config import settings
import logging

logger = logging.getLogger(__name__)

def send_email(
    to_emails: List[str],
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    attachments: Optional[List[dict]] = None
) -> bool:
    """Send an email"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.email_from
        msg['To'] = ', '.join(to_emails)
        
        # Add text part
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        # Add HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["filename"]}'
                )
                msg.attach(part)
        
        # Send email
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_emails}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def send_application_confirmation(candidate_email: str, candidate_name: str, job_title: str, reference_number: str) -> bool:
    """Send application confirmation email to candidate"""
    subject = f"Application Received - {job_title}"
    
    body = f"""
Dear {candidate_name},

Thank you for your interest in the {job_title} position with us.

We have successfully received your application. Your reference number is: {reference_number}

We will review your application and get back to you within 5-7 business days.

Best regards,
Hiring Team
    """
    
    html_body = f"""
    <html>
        <body>
            <h2>Application Received</h2>
            <p>Dear {candidate_name},</p>
            <p>Thank you for your interest in the <strong>{job_title}</strong> position with us.</p>
            <p>We have successfully received your application. Your reference number is: <strong>{reference_number}</strong></p>
            <p>We will review your application and get back to you within 5-7 business days.</p>
            <br>
            <p>Best regards,<br>Hiring Team</p>
        </body>
    </html>
    """
    
    return send_email([candidate_email], subject, body, html_body)

def send_shortlist_notification(candidate_email: str, candidate_name: str, job_title: str) -> bool:
    """Send shortlist notification email to candidate"""
    subject = f"Congratulations! You've been shortlisted for {job_title}"
    
    body = f"""
Dear {candidate_name},

Congratulations! We are pleased to inform you that you have been shortlisted for the {job_title} position.

Our HR team will be in touch with you shortly to schedule the next steps in the interview process.

We look forward to speaking with you soon.

Best regards,
Hiring Team
    """
    
    html_body = f"""
    <html>
        <body>
            <h2>Congratulations!</h2>
            <p>Dear {candidate_name},</p>
            <p>We are pleased to inform you that you have been <strong>shortlisted</strong> for the <strong>{job_title}</strong> position.</p>
            <p>Our HR team will be in touch with you shortly to schedule the next steps in the interview process.</p>
            <p>We look forward to speaking with you soon.</p>
            <br>
            <p>Best regards,<br>Hiring Team</p>
        </body>
    </html>
    """
    
    return send_email([candidate_email], subject, body, html_body)

def send_requalification_request(candidate_email: str, candidate_name: str, job_title: str, required_skills: List[str]) -> bool:
    """Send requalification email asking for additional skill details"""
    subject = f"Additional Information Required - {job_title}"
    
    skills_list = ', '.join(required_skills)
    
    body = f"""
Dear {candidate_name},

Thank you for your application for the {job_title} position.

After reviewing your application, we would like to know more about your experience with the following skills:
{skills_list}

Please reply to this email with detailed information about your experience with these technologies/skills.

Best regards,
Hiring Team
    """
    
    html_body = f"""
    <html>
        <body>
            <h2>Additional Information Required</h2>
            <p>Dear {candidate_name},</p>
            <p>Thank you for your application for the <strong>{job_title}</strong> position.</p>
            <p>After reviewing your application, we would like to know more about your experience with the following skills:</p>
            <ul>
                {''.join([f'<li>{skill}</li>' for skill in required_skills])}
            </ul>
            <p>Please reply to this email with detailed information about your experience with these technologies/skills.</p>
            <br>
            <p>Best regards,<br>Hiring Team</p>
        </body>
    </html>
    """
    
    return send_email([candidate_email], subject, body, html_body)

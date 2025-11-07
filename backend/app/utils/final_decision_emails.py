"""
Email utility functions for final hiring decisions
"""
from .email import send_email
import logging

logger = logging.getLogger(__name__)

def send_candidate_hired_email(candidate_email: str, candidate_name: str, job_title: str, company_name: str = "Our Company"):
    """Send congratulations email to hired candidate"""
    
    subject = f"🎉 Congratulations! You've been selected for {job_title}"
    
    # Plain text version
    text_body = f"""
Dear {candidate_name},

Congratulations! We are delighted to inform you that you have been selected for the position of {job_title} at {company_name}.

We were impressed by your qualifications, experience, and performance throughout the interview process. Your skills and enthusiasm make you an excellent fit for our team.

NEXT STEPS:
• Our HR team will contact you within 2-3 business days with your offer letter
• The offer letter will include details about salary, benefits, start date, and other terms
• Please keep this information confidential until the formal offer is extended

We are excited about the possibility of you joining our team and contributing to our continued success.

If you have any immediate questions, please feel free to reach out to our HR team.

Welcome to the team!

Best regards,
{company_name} Hiring Team

---
This is an automated message from the {company_name} hiring system.
"""

    # HTML version
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Congratulations - You're Hired!</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="margin: 0; font-size: 28px;">🎉 Congratulations!</h1>
        <p style="margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;">You've been selected!</p>
    </div>
    
    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
        <p style="font-size: 16px; margin-bottom: 20px;">Dear <strong>{candidate_name}</strong>,</p>
        
        <div style="background: white; padding: 25px; border-radius: 8px; border-left: 4px solid #28a745; margin: 20px 0;">
            <p style="margin: 0; font-size: 16px;">
                We are <strong>delighted to inform you</strong> that you have been selected for the position of 
                <strong style="color: #28a745;">{job_title}</strong> at {company_name}.
            </p>
        </div>
        
        <p>We were impressed by your qualifications, experience, and performance throughout the interview process. Your skills and enthusiasm make you an excellent fit for our team.</p>
        
        <div style="background: #e7f3ff; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; margin: 25px 0;">
            <h3 style="margin: 0 0 15px 0; color: #007bff; font-size: 18px;">📋 Next Steps:</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li style="margin-bottom: 8px;">Our HR team will contact you within <strong>2-3 business days</strong> with your offer letter</li>
                <li style="margin-bottom: 8px;">The offer letter will include details about <strong>salary, benefits, start date</strong>, and other terms</li>
                <li style="margin-bottom: 8px;">Please keep this information <strong>confidential</strong> until the formal offer is extended</li>
            </ul>
        </div>
        
        <p>We are excited about the possibility of you joining our team and contributing to our continued success.</p>
        
        <p>If you have any immediate questions, please feel free to reach out to our HR team.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <div style="background: #28a745; color: white; padding: 15px 30px; border-radius: 25px; display: inline-block; font-weight: bold; font-size: 16px;">
                🎊 Welcome to the team! 🎊
            </div>
        </div>
        
        <p style="margin-top: 30px;">
            Best regards,<br>
            <strong>{company_name} Hiring Team</strong>
        </p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="font-size: 12px; color: #666; text-align: center;">
            This is an automated message from the {company_name} hiring system.
        </p>
    </div>
</body>
</html>
"""

    try:
        send_email(
            to_emails=[candidate_email],
            subject=subject,
            body=text_body,
            html_body=html_body
        )
        logger.info(f"Hired notification email sent to {candidate_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send hired email to {candidate_email}: {e}")
        return False

def send_candidate_rejected_email(candidate_email: str, candidate_name: str, job_title: str, company_name: str = "Our Company"):
    """Send rejection email to candidate"""
    
    subject = f"Update on your application for {job_title}"
    
    # Plain text version
    text_body = f"""
Dear {candidate_name},

Thank you for your interest in the {job_title} position at {company_name} and for taking the time to participate in our interview process.

After careful consideration and evaluation of all candidates, we have decided to move forward with another candidate whose experience more closely aligns with our current needs.

This decision was not easy, as we were impressed by your qualifications and the professionalism you demonstrated throughout the process. We encourage you to apply for future opportunities that match your skills and interests.

We will keep your resume on file and may reach out if a suitable position becomes available in the future.

Thank you again for your time and interest in {company_name}. We wish you all the best in your job search and future endeavors.

Best regards,
{company_name} Hiring Team

---
This is an automated message from the {company_name} hiring system.
"""

    # HTML version
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Application Update</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="margin: 0; font-size: 24px;">Application Update</h1>
        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">{job_title} Position</p>
    </div>
    
    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
        <p style="font-size: 16px; margin-bottom: 20px;">Dear <strong>{candidate_name}</strong>,</p>
        
        <p>Thank you for your interest in the <strong>{job_title}</strong> position at {company_name} and for taking the time to participate in our interview process.</p>
        
        <div style="background: white; padding: 25px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 20px 0;">
            <p style="margin: 0; font-size: 16px;">
                After careful consideration and evaluation of all candidates, we have decided to move forward with another candidate whose experience more closely aligns with our current needs.
            </p>
        </div>
        
        <p>This decision was not easy, as we were impressed by your qualifications and the professionalism you demonstrated throughout the process. We encourage you to apply for future opportunities that match your skills and interests.</p>
        
        <div style="background: #e7f3ff; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; margin: 25px 0;">
            <p style="margin: 0; font-size: 14px;">
                <strong>📝 Future Opportunities:</strong><br>
                We will keep your resume on file and may reach out if a suitable position becomes available in the future.
            </p>
        </div>
        
        <p>Thank you again for your time and interest in {company_name}. We wish you all the best in your job search and future endeavors.</p>
        
        <p style="margin-top: 30px;">
            Best regards,<br>
            <strong>{company_name} Hiring Team</strong>
        </p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        <p style="font-size: 12px; color: #666; text-align: center;">
            This is an automated message from the {company_name} hiring system.
        </p>
    </div>
</body>
</html>
"""

    try:
        send_email(
            to_emails=[candidate_email],
            subject=subject,
            body=text_body,
            html_body=html_body
        )
        logger.info(f"Rejection notification email sent to {candidate_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send rejection email to {candidate_email}: {e}")
        return False

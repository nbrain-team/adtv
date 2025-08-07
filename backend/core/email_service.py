import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Gmail SMTP configuration
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("GMAIL_EMAIL", "linda@adtvmedia.com")
        self.sender_password = os.getenv("GMAIL_PASSWORD", "")  # Should be set via environment variable
        self.sender_name = "ADTV Media"
    
    def get_base_url(self):
        """Get the correct base URL for production or development"""
        if os.getenv("RENDER"):
            return "https://adtv.nbrain.ai"  # Use the actual frontend domain
        return os.getenv("APP_BASE_URL", "http://localhost:3000")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[dict]] = None
    ) -> bool:
        """
        Send an email via Gmail SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML body content
            text_body: Plain text body (optional)
            attachments: List of attachments [{filename: str, content: bytes}]
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)
            
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
            
            # Connect to Gmail SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable TLS encryption
                server.login(self.sender_email, self.sender_password)
                
                # Send email
                server.send_message(msg)
                
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_agreement_email(
        self,
        to_email: str,
        to_name: str,
        agreement_url: str,
        campaign_name: str,
        start_date: str,
        setup_fee: str,
        monthly_fee: str
    ) -> bool:
        """
        Send an agreement signing email
        """
        subject = f"Your {campaign_name} Agreement is Ready for Signature"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .details {{
                    background: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>ADTV Media</h1>
                    <p>Your Agreement is Ready</p>
                </div>
                
                <div class="content">
                    <p>Dear {to_name},</p>
                    
                    <p>Thank you for your interest in partnering with ADTV Media. Your personalized service agreement is now ready for review and signature.</p>
                    
                    <div class="details">
                        <h3>Agreement Details:</h3>
                        <ul>
                            <li><strong>Campaign:</strong> {campaign_name}</li>
                            <li><strong>Start Date:</strong> {start_date}</li>
                            <li><strong>One-time Setup Fee:</strong> ${setup_fee}</li>
                            <li><strong>Monthly Service Fee:</strong> ${monthly_fee}</li>
                        </ul>
                    </div>
                    
                    <p>Please click the button below to review and sign your agreement:</p>
                    
                    <center>
                        <a href="{agreement_url}" class="button">Review & Sign Agreement</a>
                    </center>
                    
                    <p><small>This link is unique to you and will expire in 30 days. If you have any questions, please don't hesitate to reach out.</small></p>
                    
                    <p>Best regards,<br>
                    The ADTV Media Team</p>
                </div>
                
                <div class="footer">
                    <p>© 2024 ADTV Media. All rights reserved.</p>
                    <p>This email was sent to {to_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Dear {to_name},
        
        Thank you for your interest in partnering with ADTV Media. Your personalized service agreement is now ready for review and signature.
        
        Agreement Details:
        - Campaign: {campaign_name}
        - Start Date: {start_date}
        - One-time Setup Fee: ${setup_fee}
        - Monthly Service Fee: ${monthly_fee}
        
        Please visit the following link to review and sign your agreement:
        {agreement_url}
        
        This link is unique to you and will expire in 30 days.
        
        Best regards,
        The ADTV Media Team
        """
        
        return self.send_email(to_email, subject, html_body, text_body)

# Create a singleton instance
email_service = EmailService() 
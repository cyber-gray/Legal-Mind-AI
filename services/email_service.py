"""
Email Service for Legal-Mind-AI
Handles sending PDF reports and notifications via email
"""

import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, List
import logging

# Optional: SendGrid for cloud email delivery
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

logger = logging.getLogger(__name__)

class EmailService:
    """
    Email service for sending Legal-Mind-AI reports and notifications
    """
    
    def __init__(self):
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "legalmind@yourcompany.com")
        
        # SMTP settings (fallback)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        
    async def send_report(
        self,
        to_email: str,
        subject: str,
        report_content: str,
        pdf_attachment: Optional[bytes] = None,
        attachment_name: str = "Legal-Mind-AI-Report.pdf"
    ) -> bool:
        """
        Send a report via email with optional PDF attachment
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            report_content: Text content of the report
            pdf_attachment: PDF file as bytes
            attachment_name: Name for the PDF attachment
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if SENDGRID_AVAILABLE and self.sendgrid_api_key:
                return await self._send_via_sendgrid(
                    to_email, subject, report_content, pdf_attachment, attachment_name
                )
            else:
                return await self._send_via_smtp(
                    to_email, subject, report_content, pdf_attachment, attachment_name
                )
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        content: str,
        pdf_attachment: Optional[bytes],
        attachment_name: str
    ) -> bool:
        """Send email via SendGrid"""
        try:
            # Create email content
            html_content = self._format_email_content(content)
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            # Add PDF attachment if provided
            if pdf_attachment:
                import base64
                encoded_file = base64.b64encode(pdf_attachment).decode()
                
                attachment = Attachment(
                    FileContent(encoded_file),
                    FileName(attachment_name),
                    FileType("application/pdf"),
                    Disposition("attachment")
                )
                message.attachment = attachment
            
            # Send via SendGrid
            sg = SendGridAPIClient(api_key=self.sendgrid_api_key)
            response = sg.send(message)
            
            logger.info(f"Email sent via SendGrid. Status: {response.status_code}")
            return response.status_code < 400
            
        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            return False
    
    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        content: str,
        pdf_attachment: Optional[bytes],
        attachment_name: str
    ) -> bool:
        """Send email via SMTP"""
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.error("SMTP credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body
            html_content = self._format_email_content(content)
            msg.attach(MIMEText(html_content, 'html'))
            
            # Add PDF attachment if provided
            if pdf_attachment:
                pdf_part = MIMEApplication(pdf_attachment, _subtype='pdf')
                pdf_part.add_header(
                    'Content-Disposition', 
                    f'attachment; filename={attachment_name}'
                )
                msg.attach(pdf_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent via SMTP to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False
    
    def _format_email_content(self, content: str) -> str:
        """Format content for HTML email"""
        # Convert plain text to HTML with basic formatting
        html_content = content.replace('\n\n', '</p><p>').replace('\n', '<br>')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #1f4e79; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                h1, h2, h3 {{ color: #1f4e79; }}
                .highlight {{ background-color: #e7f3ff; padding: 10px; border-left: 4px solid #2e75b6; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 Legal-Mind-AI Report</h1>
                <p>AI-Powered Legal Policy Analysis</p>
            </div>
            
            <div class="content">
                <div class="highlight">
                    <strong>Generated on:</strong> {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
                </div>
                
                <br>
                <p>{html_content}</p>
            </div>
            
            <div class="footer">
                <p>This report was generated by Legal-Mind-AI. Please verify critical information with official sources.</p>
                <p>© {datetime.now().year} Legal-Mind-AI. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
    
    async def send_notification(
        self,
        to_emails: List[str],
        subject: str,
        message: str,
        priority: str = "normal"
    ) -> bool:
        """
        Send a notification email to multiple recipients
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            message: Notification message
            priority: Email priority (low, normal, high)
            
        Returns:
            bool: True if sent successfully to at least one recipient
        """
        success_count = 0
        
        for email in to_emails:
            try:
                # Format subject with priority if high
                formatted_subject = f"[HIGH PRIORITY] {subject}" if priority == "high" else subject
                
                if await self.send_report(email, formatted_subject, message):
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to send notification to {email}: {str(e)}")
        
        return success_count > 0
    
    async def send_daily_digest(
        self,
        to_emails: List[str],
        news_content: str,
        policy_updates: str
    ) -> bool:
        """
        Send daily digest of AI policy news and updates
        """
        subject = f"Daily AI Policy Digest - {datetime.now().strftime('%B %d, %Y')}"
        
        content = f"""
        <h2>🗞️ Daily AI Policy Digest</h2>
        
        <h3>Latest News</h3>
        {news_content}
        
        <h3>Policy Updates</h3>
        {policy_updates}
        
        <hr>
        <p><em>Stay informed with Legal-Mind-AI's daily digest service.</em></p>
        """
        
        return await self.send_notification(to_emails, subject, content)

# Global email service instance
email_service = EmailService()

"""
Notification Service for SmartSPD v2

Provides email and SMS alerting capabilities for:
- Document processing completion
- Query performance alerts
- System health notifications
- User activity alerts
- Audit compliance notifications
"""

import asyncio
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional
from pathlib import Path

import aiohttp
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.audit import AuditLog
from app.services.audit_service import AuditService
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending email and SMS notifications"""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', None)
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', None)
        self.smtp_from_email = getattr(settings, 'SMTP_FROM_EMAIL', None)
        
        # SMS configuration (Twilio)
        self.twilio_account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.twilio_auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.twilio_from_number = getattr(settings, 'TWILIO_FROM_NUMBER', None)
        
        # Notification preferences
        self.enable_email = getattr(settings, 'ENABLE_EMAIL_NOTIFICATIONS', True)
        self.enable_sms = getattr(settings, 'ENABLE_SMS_NOTIFICATIONS', False)
        
    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send email notification"""
        
        if not self.enable_email or not self.smtp_username or not self.smtp_password:
            logger.warning("Email notifications not configured or disabled")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from_email or self.smtp_username
            msg['To'] = ', '.join(to_emails)
            
            # Add text content
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML content if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.smtp_username, to_emails, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message"""
        try:
            file_path = attachment.get('file_path')
            filename = attachment.get('filename')
            
            if file_path and Path(file_path).exists():
                with open(file_path, "rb") as attachment_file:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment_file.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename or Path(file_path).name}'
                )
                msg.attach(part)
                
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment}: {e}")
    
    async def send_sms(
        self,
        to_numbers: List[str],
        message: str
    ) -> bool:
        """Send SMS notification via Twilio"""
        
        if not self.enable_sms or not self.twilio_account_sid or not self.twilio_auth_token:
            logger.warning("SMS notifications not configured or disabled")
            return False
        
        try:
            # Twilio API endpoint
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
            
            # Authentication
            auth = aiohttp.BasicAuth(self.twilio_account_sid, self.twilio_auth_token)
            
            async with aiohttp.ClientSession(auth=auth) as session:
                for phone_number in to_numbers:
                    data = {
                        'From': self.twilio_from_number,
                        'To': phone_number,
                        'Body': message
                    }
                    
                    async with session.post(url, data=data) as response:
                        if response.status == 201:
                            logger.info(f"SMS sent successfully to {phone_number}")
                        else:
                            error_text = await response.text()
                            logger.error(f"Failed to send SMS to {phone_number}: {error_text}")
                            return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    async def notify_document_processed(
        self,
        db: Session,
        document_id: str,
        document_name: str,
        user_email: str,
        processing_status: str,
        processing_time: float
    ):
        """Notify when document processing is complete"""
        
        subject = f"Document Processing {'Complete' if processing_status == 'completed' else 'Failed'} - {document_name}"
        
        if processing_status == "completed":
            body = f"""
Document Processing Complete

Document: {document_name}
Status: Successfully processed
Processing Time: {processing_time:.1f} seconds
Document ID: {document_id}

The document has been processed and is now available for queries.
You can start asking questions about this health plan document.

Best regards,
SmartSPD Team
"""
            html_body = f"""
<html>
<body>
    <h2>✅ Document Processing Complete</h2>
    
    <div style="background: #f0f9ff; padding: 15px; border-radius: 5px; margin: 10px 0;">
        <p><strong>Document:</strong> {document_name}</p>
        <p><strong>Status:</strong> <span style="color: green;">Successfully processed</span></p>
        <p><strong>Processing Time:</strong> {processing_time:.1f} seconds</p>
        <p><strong>Document ID:</strong> {document_id}</p>
    </div>
    
    <p>The document has been processed and is now available for queries.</p>
    <p>You can start asking questions about this health plan document.</p>
    
    <hr>
    <p><em>Best regards,<br>SmartSPD Team</em></p>
</body>
</html>
"""
        else:
            body = f"""
Document Processing Failed

Document: {document_name}
Status: Processing failed
Document ID: {document_id}

There was an issue processing your document. Please try uploading again or contact support.

Best regards,
SmartSPD Team
"""
            html_body = f"""
<html>
<body>
    <h2>❌ Document Processing Failed</h2>
    
    <div style="background: #fef2f2; padding: 15px; border-radius: 5px; margin: 10px 0;">
        <p><strong>Document:</strong> {document_name}</p>
        <p><strong>Status:</strong> <span style="color: red;">Processing failed</span></p>
        <p><strong>Document ID:</strong> {document_id}</p>
    </div>
    
    <p>There was an issue processing your document. Please try uploading again or contact support.</p>
    
    <hr>
    <p><em>Best regards,<br>SmartSPD Team</em></p>
</body>
</html>
"""
        
        await self.send_email([user_email], subject, body, html_body)
        
        # Log notification
        await AuditService.log_system_event(
            db=db,
            tpa_id=None,
            action="notification_sent",
            description=f"Document processing notification sent to {user_email}",
            metadata={
                "document_id": document_id,
                "notification_type": "email",
                "processing_status": processing_status
            }
        )
    
    async def notify_system_alert(
        self,
        db: Session,
        alert_type: str,
        message: str,
        severity: str = "medium",
        admin_emails: Optional[List[str]] = None
    ):
        """Send system alert notifications to administrators"""
        
        if not admin_emails:
            # Get admin users from database
            admin_users = db.query(User).filter(
                User.role.in_(["tpa_admin", "cs_manager"]),
                User.is_active == True
            ).all()
            admin_emails = [user.email for user in admin_users]
        
        if not admin_emails:
            logger.warning("No admin emails found for system alert")
            return
        
        severity_colors = {
            "low": "#10b981",      # Green
            "medium": "#f59e0b",   # Yellow
            "high": "#ef4444",     # Red
            "critical": "#dc2626"  # Dark red
        }
        
        severity_icons = {
            "low": "ℹ️",
            "medium": "⚠️", 
            "high": "🚨",
            "critical": "🔥"
        }
        
        subject = f"{severity_icons.get(severity, '🔔')} SmartSPD System Alert - {alert_type}"
        
        body = f"""
SmartSPD System Alert

Alert Type: {alert_type}
Severity: {severity.upper()}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{message}

Please review the system and take appropriate action if necessary.

SmartSPD Monitoring System
"""
        
        html_body = f"""
<html>
<body>
    <h2>{severity_icons.get(severity, '🔔')} SmartSPD System Alert</h2>
    
    <div style="background: #f9fafb; padding: 15px; border-radius: 5px; border-left: 4px solid {severity_colors.get(severity, '#6b7280')}; margin: 10px 0;">
        <p><strong>Alert Type:</strong> {alert_type}</p>
        <p><strong>Severity:</strong> <span style="color: {severity_colors.get(severity, '#6b7280')}; font-weight: bold;">{severity.upper()}</span></p>
        <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
    
    <div style="background: #f3f4f6; padding: 15px; border-radius: 5px; margin: 10px 0;">
        <h3>Message:</h3>
        <p>{message}</p>
    </div>
    
    <p>Please review the system and take appropriate action if necessary.</p>
    
    <hr>
    <p><em>SmartSPD Monitoring System</em></p>
</body>
</html>
"""
        
        await self.send_email(admin_emails, subject, body, html_body)
        
        # Log alert notification
        await AuditService.log_system_event(
            db=db,
            tpa_id=None,
            action="system_alert_sent",
            description=f"System alert sent: {alert_type}",
            severity=severity,
            metadata={
                "alert_type": alert_type,
                "recipients": len(admin_emails),
                "notification_type": "email"
            }
        )
    
    async def notify_user_activity_alert(
        self,
        db: Session,
        user_id: str,
        alert_type: str,
        details: str,
        manager_emails: Optional[List[str]] = None
    ):
        """Send user activity alerts to managers"""
        
        # Get user info
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found for activity alert: {user_id}")
            return
        
        if not manager_emails:
            # Get managers for the user's TPA
            managers = db.query(User).filter(
                User.tpa_id == user.tpa_id,
                User.role.in_(["tpa_admin", "cs_manager"]),
                User.is_active == True
            ).all()
            manager_emails = [manager.email for manager in managers]
        
        if not manager_emails:
            logger.warning(f"No manager emails found for user activity alert: {user_id}")
            return
        
        subject = f"User Activity Alert - {user.first_name} {user.last_name}"
        
        body = f"""
User Activity Alert

User: {user.first_name} {user.last_name} ({user.email})
Alert Type: {alert_type}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Details:
{details}

Please review the user's activity and take appropriate action if necessary.

SmartSPD User Activity Monitoring
"""
        
        html_body = f"""
<html>
<body>
    <h2>👤 User Activity Alert</h2>
    
    <div style="background: #fef3c7; padding: 15px; border-radius: 5px; border-left: 4px solid #f59e0b; margin: 10px 0;">
        <p><strong>User:</strong> {user.first_name} {user.last_name} ({user.email})</p>
        <p><strong>Alert Type:</strong> {alert_type}</p>
        <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
    
    <div style="background: #f3f4f6; padding: 15px; border-radius: 5px; margin: 10px 0;">
        <h3>Details:</h3>
        <p>{details}</p>
    </div>
    
    <p>Please review the user's activity and take appropriate action if necessary.</p>
    
    <hr>
    <p><em>SmartSPD User Activity Monitoring</em></p>
</body>
</html>
"""
        
        await self.send_email(manager_emails, subject, body, html_body)
        
        # Log activity alert notification
        await AuditService.log_security_event(
            db=db,
            tpa_id=user.tpa_id,
            action="user_activity_alert_sent",
            description=f"User activity alert sent for {user.email}: {alert_type}",
            user_id=user_id,
            metadata={
                "alert_type": alert_type,
                "recipients": len(manager_emails),
                "notification_type": "email"
            }
        )
    
    async def send_welcome_email(
        self,
        user_email: str,
        user_name: str,
        temporary_password: Optional[str] = None
    ):
        """Send welcome email to new users"""
        
        subject = "Welcome to SmartSPD - Your Health Plan Assistant"
        
        body = f"""
Welcome to SmartSPD!

Dear {user_name},

Welcome to SmartSPD, your AI-powered health plan assistant. Your account has been created and you can now access the system.

Login Information:
- Email: {user_email}
{"- Temporary Password: " + temporary_password if temporary_password else "- Please use the password provided by your administrator"}

Getting Started:
1. Log in to the SmartSPD dashboard
2. Upload your health plan documents
3. Start asking questions about benefits and coverage

If you need help, please contact your administrator or visit our help documentation.

Best regards,
SmartSPD Team
"""
        
        html_body = f"""
<html>
<body>
    <h2>🎉 Welcome to SmartSPD!</h2>
    
    <p>Dear {user_name},</p>
    
    <p>Welcome to SmartSPD, your AI-powered health plan assistant. Your account has been created and you can now access the system.</p>
    
    <div style="background: #eff6ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <h3>Login Information:</h3>
        <p><strong>Email:</strong> {user_email}</p>
        {"<p><strong>Temporary Password:</strong> " + temporary_password + "</p>" if temporary_password else "<p><strong>Password:</strong> Please use the password provided by your administrator</p>"}
    </div>
    
    <div style="background: #f0f9ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <h3>Getting Started:</h3>
        <ol>
            <li>Log in to the SmartSPD dashboard</li>
            <li>Upload your health plan documents</li>
            <li>Start asking questions about benefits and coverage</li>
        </ol>
    </div>
    
    <p>If you need help, please contact your administrator or visit our help documentation.</p>
    
    <hr>
    <p><em>Best regards,<br>SmartSPD Team</em></p>
</body>
</html>
"""
        
        await self.send_email([user_email], subject, body, html_body)
    
    async def send_audit_compliance_report(
        self,
        db: Session,
        recipient_emails: List[str],
        report_period: str,
        report_data: Dict[str, Any]
    ):
        """Send audit compliance report to administrators"""
        
        subject = f"SmartSPD Audit Compliance Report - {report_period}"
        
        body = f"""
SmartSPD Audit Compliance Report

Report Period: {report_period}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Summary:
- Total Activities: {report_data.get('total_activities', 0)}
- Successful Activities: {report_data.get('successful_activities', 0)}
- Failed Activities: {report_data.get('failed_activities', 0)}
- Success Rate: {report_data.get('success_rate', 0):.1%}
- Security Events: {report_data.get('security_events', 0)}

Please review the attached detailed report for compliance purposes.

SmartSPD Compliance Team
"""
        
        html_body = f"""
<html>
<body>
    <h2>📊 SmartSPD Audit Compliance Report</h2>
    
    <div style="background: #f8fafc; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Report Period:</strong> {report_period}</p>
        <p><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
    
    <div style="background: #f0f9ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <h3>Summary:</h3>
        <ul>
            <li><strong>Total Activities:</strong> {report_data.get('total_activities', 0):,}</li>
            <li><strong>Successful Activities:</strong> {report_data.get('successful_activities', 0):,}</li>
            <li><strong>Failed Activities:</strong> {report_data.get('failed_activities', 0):,}</li>
            <li><strong>Success Rate:</strong> {report_data.get('success_rate', 0):.1%}</li>
            <li><strong>Security Events:</strong> {report_data.get('security_events', 0):,}</li>
        </ul>
    </div>
    
    <p>Please review the attached detailed report for compliance purposes.</p>
    
    <hr>
    <p><em>SmartSPD Compliance Team</em></p>
</body>
</html>
"""
        
        await self.send_email(recipient_emails, subject, body, html_body)
        
        # Log compliance report notification
        await AuditService.log_admin_action(
            db=db,
            user_id=None,
            tpa_id=None,
            action="compliance_report_sent",
            description=f"Audit compliance report sent for period: {report_period}",
            metadata={
                "report_period": report_period,
                "recipients": len(recipient_emails),
                "notification_type": "email"
            }
        )

# Singleton instance
notification_service = NotificationService()

# Convenience functions
async def notify_document_processed(*args, **kwargs):
    return await notification_service.notify_document_processed(*args, **kwargs)

async def notify_system_alert(*args, **kwargs):
    return await notification_service.notify_system_alert(*args, **kwargs)

async def notify_user_activity_alert(*args, **kwargs):
    return await notification_service.notify_user_activity_alert(*args, **kwargs)

async def send_welcome_email(*args, **kwargs):
    return await notification_service.send_welcome_email(*args, **kwargs)

async def send_audit_compliance_report(*args, **kwargs):
    return await notification_service.send_audit_compliance_report(*args, **kwargs)
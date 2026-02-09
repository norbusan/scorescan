import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""

    def __init__(self):
        self.settings = get_settings()

    def _create_smtp_connection(self) -> Optional[smtplib.SMTP]:
        """Create and return an SMTP connection

        Supports both authenticated and unauthenticated SMTP modes.
        """
        try:
            # Validate credentials are both present or both absent
            has_username = bool(self.settings.smtp_username)
            has_password = bool(self.settings.smtp_password)

            if has_username != has_password:
                logger.error(
                    "SMTP configuration error: Both username and password must be "
                    "provided together, or both must be empty for unauthenticated mode."
                )
                return None

            requires_auth = has_username and has_password

            logger.info(
                f"Connecting to SMTP server: {self.settings.smtp_host}:{self.settings.smtp_port}"
            )

            # Create connection
            smtp = smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port)
            smtp.starttls()

            # Conditional authentication
            if requires_auth:
                logger.info("Authenticating with provided credentials")
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            else:
                logger.info("Using unauthenticated SMTP mode")

            return smtp

        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {str(e)}")
            return None

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """
        Send password reset email to user

        Args:
            to_email: Recipient email address
            reset_token: Password reset token

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Build reset URL
            reset_url = (
                f"{self.settings.frontend_url}/reset-password?token={reset_token}"
            )

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Password Reset Request - ScoreScan"
            message["From"] = (
                f"{self.settings.smtp_from_name} <{self.settings.smtp_from_email or self.settings.smtp_username}>"
            )
            message["To"] = to_email

            # Create plain text version
            text_content = f"""
Hello,

You requested to reset your password for ScoreScan.

Click the link below to reset your password:
{reset_url}

This link will expire in {self.settings.password_reset_token_expire_hours} hours.

If you did not request a password reset, please ignore this email.

Best regards,
The ScoreScan Team
"""

            # Create HTML version
            html_content = f"""
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
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #4F46E5;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 30px;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Password Reset Request</h2>
        <p>Hello,</p>
        <p>You requested to reset your password for ScoreScan.</p>
        <p>Click the button below to reset your password:</p>
        <a href="{reset_url}" class="button">Reset Password</a>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #4F46E5;">{reset_url}</p>
        <p>This link will expire in {self.settings.password_reset_token_expire_hours} hours.</p>
        <p>If you did not request a password reset, please ignore this email.</p>
        <div class="footer">
            <p>Best regards,<br>The ScoreScan Team</p>
        </div>
    </div>
</body>
</html>
"""

            # Attach parts
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            message.attach(part1)
            message.attach(part2)

            # Send email
            smtp = self._create_smtp_connection()
            if not smtp:
                logger.warning(f"Skipping email to {to_email} - SMTP not configured")
                logger.info(f"Password reset URL (not sent): {reset_url}")
                return False

            smtp.sendmail(
                self.settings.smtp_from_email or self.settings.smtp_username,
                to_email,
                message.as_string(),
            )
            smtp.quit()

            logger.info(f"Password reset email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
            return False


# Singleton instance
email_service = EmailService()

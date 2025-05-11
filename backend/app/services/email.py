from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import List
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAILS_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_FROM_NAME=settings.PROJECT_NAME,
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER='./templates/email'
)

async def send_password_reset_email(
    email_to: str,
    token: str
) -> None:
    """
    Send password reset email.
    """
    try:
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        message = MessageSchema(
            subject=f"{settings.PROJECT_NAME} - Password Reset",
            recipients=[email_to],
            body=f"""
            <html>
                <body>
                    <h1>Password Reset Request</h1>
                    <p>You have requested to reset your password.</p>
                    <p>Click the link below to reset your password:</p>
                    <p><a href="{reset_link}">Reset Password</a></p>
                    <p>If you did not request this, please ignore this email.</p>
                    <p>This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes.</p>
                </body>
            </html>
            """,
            subtype="html"
        )
        
        fm = FastMail(conf)
        await fm.send_message(message)
        
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        raise

async def send_verification_email(
    email_to: str,
    token: str
) -> None:
    """
    Send email verification email.
    """
    try:
        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        
        message = MessageSchema(
            subject=f"{settings.PROJECT_NAME} - Verify Your Email",
            recipients=[email_to],
            body=f"""
            <html>
                <body>
                    <h1>Email Verification</h1>
                    <p>Thank you for registering with {settings.PROJECT_NAME}.</p>
                    <p>Please click the link below to verify your email address:</p>
                    <p><a href="{verification_link}">Verify Email</a></p>
                    <p>If you did not create an account, please ignore this email.</p>
                </body>
            </html>
            """,
            subtype="html"
        )
        
        fm = FastMail(conf)
        await fm.send_message(message)
        
    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}")
        raise 
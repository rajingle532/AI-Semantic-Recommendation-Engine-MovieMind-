import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.config import settings
from pydantic import EmailStr

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD.replace(" ", ""),
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=None
)

async def send_reset_password_email(email: EmailStr, token: str):
    """Send password reset email with a verification link."""
    # Build the reset link
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #141414; color: #ffffff; padding: 40px; text-align: center;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #000000; border: 1px solid #e50914; border-radius: 8px; padding: 20px;">
            <h1 style="color: #e50914;">MovieMind</h1>
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password. Click the button below to set a new one:</p>
            <a href="{reset_link}" style="display: inline-block; padding: 12px 24px; background-color: #e50914; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; margin: 20px 0;">Reset Password</a>
            <p style="font-size: 0.8rem; color: #888;">If you didn't request this, please ignore this email.</p>
            <p style="font-size: 0.8rem; color: #888;">This link will expire in 1 hour.</p>
        </div>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="MovieMind — Password Reset",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

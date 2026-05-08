import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

def send_reset_password_email(email: str, token: str):
    """Send password reset email using standard smtplib for maximum reliability."""
    try:
        print(f"SMTP: Attempting to send email to {email} via Port 465...")
        
        # Build the reset link
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "MovieMind — Password Reset"
        message["From"] = settings.MAIL_FROM
        message["To"] = email

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #141414; color: #ffffff; padding: 40px; text-align: center;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #000000; border: 1px solid #e50914; border-radius: 8px; padding: 20px;">
                <h1 style="color: #e50914;">MovieMind</h1>
                <h2 style="color: #ffffff;">Password Reset Request</h2>
                <p style="color: #cccccc;">You requested to reset your password. Click the button below to set a new one:</p>
                <a href="{reset_link}" style="padding: 12px 24px; background-color: #e50914; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; margin: 20px 0; display: inline-block;">Reset Password</a>
                <p style="font-size: 0.8rem; color: #888;">If you didn't request this, please ignore this email.</p>
            </div>
        </body>
        </html>
        """
        message.attach(MIMEText(html, "html"))

        # Connect and send
        # We use SSL for port 465
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            # Strip any spaces from the password
            clean_password = settings.MAIL_PASSWORD.replace(" ", "")
            server.login(settings.MAIL_USERNAME, clean_password)
            server.sendmail(settings.MAIL_FROM, email, message.as_string())
            
        print(f"SMTP SUCCESS: Email sent to {email}")
        return True
    except Exception as e:
        print(f"SMTP CRITICAL ERROR: {str(e)}")
        return False

import os
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

def send_reset_password_email(email: str, token: str):
    """Send password reset email with forced IPv4 for cloud compatibility."""
    try:
        print(f"SMTP: Starting send to {email}...")
        
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

        # FORCE IPv4 (Crucial for Render/Cloud)
        # We resolve smtp.gmail.com to its IPv4 address
        print("SMTP: Resolving smtp.gmail.com to IPv4...")
        try:
            target_ip = socket.gethostbyname("smtp.gmail.com")
            print(f"SMTP: Resolved to {target_ip}")
        except Exception as e:
            print(f"SMTP WARNING: Failed to resolve via IPv4, using hostname. Error: {e}")
            target_ip = "smtp.gmail.com"

        # Connect using Port 587 (Standard for STARTTLS)
        print(f"SMTP: Connecting to {target_ip} on Port 587...")
        server = smtplib.SMTP(target_ip, 587, timeout=15)
        
        server.set_debuglevel(1) # Show full conversation in logs
        server.starttls() # Secure the connection
        
        clean_password = settings.MAIL_PASSWORD.replace(" ", "")
        print(f"SMTP: Logging in as {settings.MAIL_USERNAME}...")
        server.login(settings.MAIL_USERNAME, clean_password)
        
        print(f"SMTP: Sending to {email}...")
        server.sendmail(settings.MAIL_FROM, email, message.as_string())
        server.quit()
            
        print(f"SMTP SUCCESS: Email delivered to {email}")
        return True
    except Exception as e:
        print(f"SMTP CRITICAL ERROR: {str(e)}")
        return False

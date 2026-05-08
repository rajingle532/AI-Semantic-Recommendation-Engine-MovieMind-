import requests
from app.config import settings

def send_reset_password_email(email: str, token: str):
    """Send password reset email using Resend HTTP API."""
    try:
        api_key = settings.RESEND_API_KEY
        if not api_key:
            print("RESEND ERROR: RESEND_API_KEY is missing!")
            return False

        # Build the reset link
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        # Build HTML content
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

        # Resend API endpoint
        url = "https://api.resend.com/emails"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Onboarding sender (required for free tier without domain verification)
        sender = "MovieMind <onboarding@resend.dev>"
        
        payload = {
            "from": sender,
            "to": [email],
            "subject": "MovieMind — Password Reset",
            "html": html
        }
        
        print(f"RESEND: Sending email to {email}...")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"RESEND SUCCESS: Email sent to {email}")
            return True
        else:
            print(f"RESEND ERROR: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"RESEND CRITICAL ERROR: {str(e)}")
        return False

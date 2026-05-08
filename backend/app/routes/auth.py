"""
Auth routes — signup and login endpoints.
"""
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.models.user import UserSignup, UserLogin, UserResponse, TokenResponse, GoogleLogin
from app.utils.security import hash_password, verify_password, create_token
from app.config import settings
from app.database import get_collection
import jwt
from bson import ObjectId

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserSignup):
    """Register a new user account."""
    users = get_collection("users")
    email = user_data.email.lower().strip()

    # Check if email already exists
    if users.find_one({"email": email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password and save user
    user_doc = {
        "name": user_data.name,
        "email": email,
        "phone": user_data.phone,
        "password_hash": hash_password(user_data.password),
    }
    result = users.insert_one(user_doc)
    user_id = str(result.inserted_id)

    # Generate JWT token
    token = create_token(user_id, user_data.email)

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id, 
            name=user_data.name, 
            email=email,
            phone=user_data.phone
        )
    )


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin):
    """Login with email and password, returns JWT token."""
    users = get_collection("users")

    # Find user by email
    email = credentials.email.lower().strip()
    user = users.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    user_id = str(user["_id"])
    token = create_token(user_id, credentials.email)

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=str(user["_id"]), 
            name=user["name"], 
            email=user["email"],
            phone=user.get("phone")
        )
    )


@router.post("/google", response_model=TokenResponse)
def google_auth(data: GoogleLogin):
    """Verify Google ID token and login/register user."""
    try:
        # Verify the ID token from Google
        idinfo = id_token.verify_oauth2_token(
            data.token, 
            google_requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )

        # ID token is valid. Get user's info.
        email = idinfo['email']
        name = idinfo.get('name', email.split('@')[0])
        
        users = get_collection("users")
        
        # Check if user exists
        user = users.find_one({"email": email})
        
        if not user:
            # Create new user for Google login
            user_doc = {
                "name": name,
                "email": email,
                "google_id": idinfo['sub'],
                # No password for Google users
                "password_hash": None 
            }
            result = users.insert_one(user_doc)
            user_id = str(result.inserted_id)
        else:
            user_id = str(user["_id"])
            update_data = {}
            
            # Link google_id if missing (IMPORTANT FIX)
            if not user.get("google_id"):
                update_data["google_id"] = idinfo['sub']
            
            # Update name if it changed
            if user.get("name") != name:
                update_data["name"] = name
                
            if update_data:
                users.update_one({"_id": user["_id"]}, {"$set": update_data})

        # Generate MovieMind JWT token
        token = create_token(user_id, email)

        return TokenResponse(
            access_token=token,
            user=UserResponse(id=user_id, name=name, email=email)
        )

    except ValueError:
        # Invalid token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
@router.post("/forgot-password")
async def forgot_password(data: dict, background_tasks: BackgroundTasks):
    """Handle password reset request."""
    email = data.get("email", "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    users = get_collection("users")
    user = users.find_one({"email": email})
    
    # Security best practice: Don't reveal if email exists, 
    # but for this project's simplicity we'll check it.
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
    
    from app.utils.email import send_reset_password_email
    
    print(f"DEBUG: Forgot password request received for: {email}")
    
    # Generate a reset token (re-using create_token for simplicity)
    user_id = str(user["_id"])
    reset_token = create_token(user_id, email)
    
    # Send the email DIRECTLY (synchronous to avoid background task death)
    print(f"DEBUG: Attempting direct Resend API call for {email}")
    success = send_reset_password_email(email, reset_token)
    
    if success:
        return {"message": "Reset link sent successfully"}
    else:
        # If it fails, we show why in the logs
        print(f"DEBUG: Resend API call FAILED for {email}")
        raise HTTPException(status_code=500, detail="Failed to send email. Check logs.")

@router.post("/reset-password")
def reset_password(data: dict):
    """Verify reset token and update user password."""
    token = data.get("token")
    new_password = data.get("new_password")
    
    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token and password are required")
    
    try:
        # Decode the token (same secret as login)
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token")
            
        users = get_collection("users")
        
        # Update user's password
        hashed_pwd = hash_password(new_password)
        result = users.update_one(
            {"_id": ObjectId(user_id)}, 
            {"$set": {"password_hash": hashed_pwd}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"message": "Password updated successfully"}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset link has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid reset link")
    except Exception as e:
        print(f"RESET ERROR: {e}")
        raise HTTPException(status_code=500, detail="Failed to update password")

"""
Security utilities — JWT token creation/verification and password hashing.
"""
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

# Bearer token extractor for protected routes
security_scheme = HTTPBearer()


# ═══════════════════════════════════════════
# Password Hashing (bcrypt)
# ═══════════════════════════════════════════

def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


# ═══════════════════════════════════════════
# JWT Token Management
# ═══════════════════════════════════════════

def create_token(user_id: str, email: str) -> str:
    """Create a JWT access token with user_id and email in payload."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token. Returns the payload dict."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# ═══════════════════════════════════════════
# Auth Dependency (use in protected routes)
# ═══════════════════════════════════════════

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """
    FastAPI dependency — extracts and verifies JWT from Authorization header.
    Usage: @router.get("/protected", dependencies=[Depends(get_current_user)])
    """
    token = credentials.credentials
    payload = decode_token(token)
    return {
        "user_id": payload["user_id"],
        "email": payload["email"]
    }

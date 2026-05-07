"""
User schemas — Pydantic models for auth request/response validation.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserSignup(BaseModel):
    """Schema for user registration request."""
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Schema for user login request."""
    email: EmailStr
    password: str


class GoogleLogin(BaseModel):
    """Schema for Google login request."""
    token: str


class UserResponse(BaseModel):
    """Schema for user data in API responses (never includes password)."""
    id: str
    name: str
    email: str


class TokenResponse(BaseModel):
    """Schema for auth token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

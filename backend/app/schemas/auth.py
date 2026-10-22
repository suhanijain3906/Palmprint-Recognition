"""Schemas for the authentication endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    is_demo_account: bool


TokenResponse.model_rebuild()


__all__ = ["LoginRequest", "RegisterRequest", "TokenResponse", "UserResponse"]

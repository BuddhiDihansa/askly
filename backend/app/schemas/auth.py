from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=100)


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    is_active: bool = True
    education_level: str | None = None
    learning_goal: str | None = None
    preferred_language: str = "English"
    study_subjects: list[str] = Field(default_factory=list)
    daily_study_minutes: int | None = None
    study_style: str | None = None
    onboarding_completed: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TokenResponse(BaseModel):
    token: str
    user: UserResponse

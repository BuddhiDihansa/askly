from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


EducationLevel = Literal[
    "secondary",
    "undergraduate",
    "postgraduate",
    "professional",
    "other",
]
StudyStyle = Literal["visual", "reading", "practice", "discussion", "mixed"]


class ProfileFields(BaseModel):
    education_level: EducationLevel | None = None
    learning_goal: str | None = Field(default=None, min_length=2, max_length=160)
    preferred_language: str = Field(default="English", min_length=2, max_length=40)
    study_subjects: list[str] = Field(default_factory=list, max_length=20)
    daily_study_minutes: int | None = Field(default=None, ge=10, le=720)
    study_style: StudyStyle | None = None

    @field_validator("learning_goal", "preferred_language")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("study_subjects")
    @classmethod
    def validate_subjects(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if any(not value for value in cleaned):
            raise ValueError("study_subjects cannot contain empty values")
        if len(set(value.casefold() for value in cleaned)) != len(cleaned):
            raise ValueError("study_subjects cannot contain duplicates")
        return cleaned


class ProfileUpdate(ProfileFields):
    name: str | None = Field(default=None, min_length=2, max_length=80)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class OnboardingRequest(ProfileFields):
    education_level: EducationLevel
    learning_goal: str = Field(min_length=2, max_length=160)
    preferred_language: str = Field(min_length=2, max_length=40)
    study_subjects: list[str] = Field(min_length=1, max_length=20)
    daily_study_minutes: int = Field(ge=10, le=720)
    study_style: StudyStyle


class UserProfileResponse(ProfileFields):
    id: str
    name: str
    email: EmailStr
    is_active: bool = True
    onboarding_completed: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

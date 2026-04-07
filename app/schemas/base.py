# app/schemas/base.py

from pydantic import BaseModel, EmailStr, Field, ConfigDict, ValidationError, model_validator
from typing import Optional
from uuid import UUID
from datetime import datetime

# Base user schema with common fields
class UserBase(BaseModel):
    first_name: str = Field(max_length=50, example="John")
    last_name: str = Field(max_length=50, example="Doe")
    email: EmailStr = Field(example="john.doe@example.com")
    username: str = Field(min_length=3, max_length=50, example="johndoe")

    model_config = ConfigDict(from_attributes=True)

# Password validation mixin
class PasswordMixin(BaseModel):
    password: str = Field(min_length=6, max_length=128, example="SecurePass123")

    @model_validator(mode="before")
    @classmethod
    def validate_password(cls, values: dict) -> dict:
        password = values.get("password")
        if not password:
            raise ValidationError("Password is required", model=cls)  # pragma: no cover
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one digit")
        return values

# Schema for creating a new user
class UserCreate(UserBase, PasswordMixin):
    pass

# Schema for login input
class UserLogin(PasswordMixin):
    username: str = Field(
        description="Username or email",
        min_length=3,
        max_length=50,
        example="johndoe123"
    )
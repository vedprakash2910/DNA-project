import re

from pydantic import BaseModel, Field, field_validator

from config import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=254, description="Account email")
    password: str = Field(..., max_length=MAX_PASSWORD_LENGTH)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not _EMAIL_RE.match(value):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("password")
    @classmethod
    def strong_enough(cls, value: str) -> str:
        if len(value) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
        return value


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=1, max_length=MAX_PASSWORD_LENGTH)


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    created_at: str


class RegisterResponse(BaseModel):
    success: bool = True
    message: str = "Account created"
    user: UserOut


class TokenResponse(BaseModel):
    success: bool = True
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Seconds until the token expires")
    user: UserOut


class MeResponse(BaseModel):
    success: bool = True
    user: UserOut

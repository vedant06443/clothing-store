from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional
import re


def normalize_indian_phone(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = v.strip()
    if not v:
        return None
    # Strip common formatting characters: spaces, hyphens, parentheses, dots, plus
    cleaned = re.sub(r'[\s\-\(\)\.\+]', '', v)
    # Handle country code +91 or 91 with 12 digits total
    if len(cleaned) == 12 and cleaned.startswith('91'):
        cleaned = cleaned[2:]
    # Handle leading 0 with 11 digits total (e.g. 09405611628)
    elif len(cleaned) == 11 and cleaned.startswith('0'):
        cleaned = cleaned[1:]

    if not re.match(r'^[6-9]\d{9}$', cleaned):
        raise ValueError("Enter a valid 10-digit Indian mobile number")
    return cleaned


class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    confirm_password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("phone")
    @classmethod
    def phone_valid(cls, v):
        return normalize_indian_phone(v)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def phone_valid(cls, v):
        return normalize_indian_phone(v)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    phone: Optional[str]
    is_admin: bool
    profile_image: Optional[str]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

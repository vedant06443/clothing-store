from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional
import re


class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
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
        v = v.strip()
        if not re.match(r'^[6-9]\d{9}$', v):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


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

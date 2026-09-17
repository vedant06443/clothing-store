from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserRegister, UserLogin
from app.services.auth_service import register_user, authenticate_user, create_user_token
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
async def register(data: UserRegister, db: Session = Depends(get_db)):
    user = register_user(db, data)
    token = create_user_token(user)
    return {"message": "Registration successful", "token": token, "user_id": user.id}


@router.post("/login")
async def login(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.email, data.password)
    token = create_user_token(user)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return {"message": "Login successful", "is_admin": user.is_admin}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}

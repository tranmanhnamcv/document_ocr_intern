from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.auth_service import AuthService
from schemas.user import UserCreate, TokenResponse, LoginRequest
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from core.security import decode_token, blacklist_token
from api.dependencies import get_current_user, bearer_scheme
from models.user import User

router = APIRouter()

@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    return AuthService(db).register(data)

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return AuthService(db).login(data.email, data.password)

@router.post("/logout", status_code=200)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
):
    from fastapi.security import HTTPBearer
    payload = decode_token(credentials.credentials)
    blacklist_token(payload["jti"], payload["exp"])
    return {"message": "Logged out successfully"}
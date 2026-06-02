from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.auth_service import AuthService
from schemas.user import UserCreate, TokenResponse, LoginRequest

router = APIRouter()

@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    return AuthService(db).register(data)

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return AuthService(db).login(data.email, data.password)
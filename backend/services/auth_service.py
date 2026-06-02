from sqlalchemy.orm import Session
from repositories.user_repository import UserRepository
from schemas.user import UserCreate, TokenResponse, UserResponse
from core.security import verify_password, create_access_token
from fastapi import HTTPException, status

class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def register(self, data: UserCreate) -> TokenResponse:
        if self.repo.get_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        user = self.repo.create(data)
        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        token = create_access_token({"sub": str(user.id)})
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user))
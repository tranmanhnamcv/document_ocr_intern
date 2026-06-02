from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "change-this-in-production-use-secrets"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7   # 7 days
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/document_ocr"

    # File storage
    UPLOAD_DIR: str = "/uploads"

    # App
    APP_NAME: str = "OCR Document Search"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables that don't yet exist. Called on app startup."""
    # Import all models so SQLAlchemy knows about them before create_all
    import models.document  # noqa: F401
    import models.ocr_result  # noqa: F401

    Base.metadata.create_all(bind=engine)
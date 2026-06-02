from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from core.database import get_db
from models.user import User
from schemas.document import SearchResponse
from services.search_service import SearchService

router = APIRouter()


@router.get("/", response_model=SearchResponse)
def search_documents(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SearchService(db).search(q, page=page, limit=limit, user_id=current_user.id)
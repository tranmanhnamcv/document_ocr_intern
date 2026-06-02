# backend/services/search_service.py
from sqlalchemy.orm import Session
from repositories.document_repository import DocumentRepository
from schemas.document import SearchResponse, SearchResultItem, DocumentResponse


class SearchService:

    def __init__(self, db: Session):
        self.repo = DocumentRepository(db)

    def search(self, query: str, page: int = 1, limit: int = 20) -> SearchResponse:
        query = query.strip()
        if not query:
            return SearchResponse(query=query, total=0, results=[], page=page, limit=limit)

        skip = (page - 1) * limit
        rows = self.repo.search(query, skip=skip, limit=limit)
        total = self.repo.search_count(query)

        results = [
            SearchResultItem(
                document=DocumentResponse.model_validate(row["document"]),
                rank=row["rank"],
                headline=row["headline"],
            )
            for row in rows
        ]

        return SearchResponse(
            query=query,
            total=total,
            results=results,
            page=page,
            limit=limit,
        )
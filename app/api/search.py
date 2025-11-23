from fastapi import APIRouter, Query, status
from core.storage import search_by_keyword
from app.utils.responses import success_response

router = APIRouter()

@router.get("/", status_code=status.HTTP_200_OK)
def search(
    q: str = Query(..., description="검색어"),
    limit: int = Query(10, ge=1, le=100)
):
    results = search_by_keyword(q, limit=limit)
    return success_response(
        data={
            "query": q,
            "total": len(results),
            "results": results
        },
            message="검색 성공"
    )
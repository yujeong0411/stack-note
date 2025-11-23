from fastapi import APIRouter, status, HTTPException
from typing import Optional
from core.storage import get_categories, get_tags
from app.utils.responses import success_response
from core.storage import get_activity_metrics

router = APIRouter()

@router.get("/categories", status_code=status.HTTP_200_OK)
def list_categories_endpoint(date: Optional[str] = None):
    categories = get_categories(date=date)

    return success_response(
        data={"categories": categories},
        message="카테고리 목록 조회 성공"
    )

@router.get("/tags", status_code=status.HTTP_200_OK)
def list_tags(category: Optional[str] = None, limit: int = 100):
    tags = get_tags(category=category, limit=limit)
    if not tags:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="태그를 찾을 수가 없습니다."
        )
    
    return success_response(
        data={"tags": tags},
        message="태그 목록 조회 성공"
    )

@router.get("/metrics", status_code=status.HTTP_200_OK)
def get_metrics():
    """오늘의 활동 통계"""    
    metrics = get_activity_metrics()
    
    return success_response(
        data=metrics,
        message="통계 조회 성공"
    )
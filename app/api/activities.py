from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, status
from typing import Optional
from app.schemas.activity import ActivityCreate, ActivityUpdate
from app.utils.responses import success_response
from core.storage import get_activities, get_activity_by_id, delete_activity, update_activity
from core.url_collector import process_url_auto
from core.vector_store import init_vectorstore, delete_activity_from_vector

router = APIRouter()

@router.get("/", status_code=status.HTTP_200_OK)
def list_activities_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    category: Optional[str] = None,
    tags: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    source_type: Optional[str] = None
):
    """활동 목록 조회"""
    tag_list = tags.split(',') if tags else None

    # core 호출
    result = get_activities(
        page=page,
        page_size=page_size,
        category=category,
        tags=tag_list,
        start_date=start_date,
        end_date=end_date,
        source_type=source_type
    )

    return success_response(
        data=result,
        message="활동 목록 조회 성공"
    )

@router.get("/{activity_id}", status_code=status.HTTP_200_OK)
def get_activityy_endpoint(activity_id: int):
    """활동 상세 조회"""
    activity = get_activity_by_id(activity_id)

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="활동을 찾을 수가 없습니다."
        )
    
    return success_response(
        data=activity,
        message="활동 조회 성공"
    )

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def create_activity_endpoint(data: ActivityCreate, background_tasks: BackgroundTasks):
    """URL 제출 및 활동 생성 (백그라운드 처리)"""
    # 백그라운드 처리
    vectorstore = init_vectorstore()
    background_tasks.add_task(
        process_url_auto,
        str(data.url),
        vectorstore
    )

    return success_response(
        message="URL이 처리 대기열에 추가되었습니다"
    )


@router.put("/{activity_id}", status_code=status.HTTP_200_OK)
def updated_activity_endpoint(activity_id: int, data: ActivityUpdate):
    """활동 수정"""
    # 수정할 데이터만 추출
    update_data = data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 데이터가 없습니다"
        )
    
    updated_activity = update_activity(activity_id, update_data)
    if not updated_activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )
    
    return success_response(
        data=updated_activity,
        message="Updated activity"
    )

@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity_endpoint(activity_id: int):
    """활동 삭제"""
    # DB 삭제
    success = delete_activity(activity_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found"
        )
    
    # vector store 삭제
    vectorstore = init_vectorstore()
    delete_activity_from_vector(vectorstore, activity_id)

    return # 204는 body 반환 안 함
from fastapi import APIRouter, status, BackgroundTasks
from core.agent import create_agent_graph, run_agent
from core.storage import get_briefings
from app.utils.responses import success_response
from app.schemas.briefing import BriefingRequest

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_briefing(request: BriefingRequest, background_tasks: BackgroundTasks = None):
    agent_graph = create_agent_graph()
    result = run_agent(
        f"최근 {request.days}일간의 활동을 분석하여 브리핑을 생성해줘.",
        agent_graph
    )

    return success_response(
        data=result,
        message="브리핑 생성 성공"
    )

@router.get("/", status_code=status.HTTP_200_OK)
def list_briefings(limit: int = 10):
    briefings = get_briefings(limit=limit)
    return success_response(
        data={"items": briefings},
        message="브리핑 목록 조회 성공"
    )
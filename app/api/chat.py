from fastapi import APIRouter, status
from core.agent import create_agent_graph, run_agent
from app.utils.responses import success_response
from app.schemas.chat import ChatRequest

router = APIRouter()

@router.post("/", status_code=status.HTTP_200_OK)
def chat(request: ChatRequest):
    agent_graph = create_agent_graph()
    
    result = run_agent(request.message, agent_graph)
    
    return success_response(
        data={
            "response": result["response"]
        },
        message="응답 생성 성공"
    )
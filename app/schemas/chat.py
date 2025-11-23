from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str
    conversation_id: Optional[str] = None


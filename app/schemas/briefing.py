from pydantic import BaseModel
from typing import Optional

class BriefingRequest(BaseModel):
    """브리핑 생성 요청"""
    days: int = 7


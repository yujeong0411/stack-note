from pydantic import BaseModel, HttpUrl
from typing import List, Optional

# POST 요청용
class ActivityCreate(BaseModel):
    url: HttpUrl
    title: str
    timestamp: Optional[str] = None

# PUT 요청용
class ActivityUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


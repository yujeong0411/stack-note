from datetime import datetime
from typing import Any
from fastapi import status

def success_response(
    data: Any = None,
    message: str = "success",
    code: int = status.HTTP_200_OK
):
    return {
        "isSuccess": True,
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

def error_response(
    data: Any = None,
    message: str = "error",
    code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
):
    return {
        "isSuccess": False,
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
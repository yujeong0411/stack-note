from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.utils.responses import error_response
from utils.logging import logger

async def validation_exception_handler(request: Request, exc:RequestValidationError):
    """Pydantic 검증 오류"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error['loc']),
            "message":error['msg']
        })

    return JSONResponse(
        status_code=400,
        content=error_response(
            message="입력값 검증 실패",
            code=400,
            data={"errors": errors}
        )
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPException 처리"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.detail,
            code=exc.status_code
        )
    )

async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=error_response(
            message="서버 내부 오류",
            code=500
        )
    )
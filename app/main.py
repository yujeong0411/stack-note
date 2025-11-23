# uvicorn app.main:app --reload
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi import status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from utils.logging import logger
from app.utils.responses import success_response, error_response
from config.settings import DB_PATH
from core.vector_store import init_vectorstore
from app.api import activities, analytics, briefings, chat, search
from app.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    global_exception_handler
)

app = FastAPI(
    title="Stacknote API"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["*"],
    allow_headers=["*"]
)
# error exception handler 등록
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# 라우터 등록 나중에
app.include_router(activities.router, prefix="/api/activities", tags=["Activities"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(briefings.router, prefix="/api/briefings", tags=["Briefings"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])

# root endpoint
@app.get("/")
def root():
    return success_response(
        data={
            "name": "Stacknote API",
            "version": "1.0.0",
            "docs": "/docs"
        },
        message="API info"
    )

# 헬스체크
@app.get("/health")
def health():
    # DB 확연
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = "disconnected"
        logger.error(f"DB 오류: {e}")

    # vector store 확인
    try:
        vectorstore = init_vectorstore()
        vector_status = "connected"
    except Exception as e:
        vector_status = "disconnected"
        logger.error(f"Vector Store 오류 : {e}")

    is_healthy = (db_status == "connected" and vector_status == "connected")

    if is_healthy:
        return success_response(
            data={
                "status": "healthy" if is_healthy else "unhealthy",
                "database": db_status,
                "vector_store": vector_status
            },
            message="시스템 정상",
            code=status.HTTP_200_OK
        )
    else:
        return error_response(
            data={
                "status": "healthy" if is_healthy else "unhealthy",
                "database": db_status,
                "vector_store": vector_status
            },
            message="시스템 이상",
            code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

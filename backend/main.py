import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.logging import setup_logging
from app.routers.routers import api_router
from app.utils.exceptions import BaseAppException

# 環境変数の読み込み
load_dotenv()

# ログ設定の初期化
setup_logging()

logger = logging.getLogger(__name__)

# アプリケーションとログの設定
app = FastAPI(
    redirect_slashes=False,
)

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# グローバル例外ハンドラー
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """
    Handle application-specific exceptions.

    Args:
        request: The FastAPI request object
        exc: The application exception

    Returns:
        JSONResponse: Error response with user-friendly message
    """
    logger.error(
        f"Application exception: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
        },
    )

    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.user_message,
                "details": exc.details,
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Args:
        request: The FastAPI request object
        exc: The unexpected exception

    Returns:
        JSONResponse: Generic error response
    """
    logger.error(
        f"Unexpected exception: {exc}",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
            }
        },
    )


# ルーターの登録
app.include_router(api_router)


# アプリケーション起動時のログ
@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info("Application starting up")


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Application shutting down")

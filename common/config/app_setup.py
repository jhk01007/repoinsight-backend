import logging
import os

from fastapi import FastAPI
from fastapi.logger import logger as fastapi_logger
from starlette.middleware.cors import CORSMiddleware
from common.config.middleware.ip_rate_limit_middleware import  IPRateLimitMiddleware
from common.config.middleware.log_request_time_middleware import LogRequestTimeMiddleware

from common.exception_handers import register_exception_handlers


def setup_logging() -> None:
    """기본 로깅 설정."""
    logging.basicConfig(level=logging.INFO)
    fastapi_logger.setLevel(logging.INFO)


def setup_cors(app: FastAPI) -> None:
    """CORS 설정."""
    origins = [
        os.getenv("FRONTEND_URL")
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # 임시 허용
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def setup_common_middleware(app: FastAPI) -> None:
    """ 공통 미들웨어 설정"""
    app.add_middleware(IPRateLimitMiddleware)
    app.add_middleware(LogRequestTimeMiddleware)


def setup_app(app: FastAPI) -> None:
    """
    FastAPI 앱에 공통 설정을 적용한다.
    - 로그 레벨
    - 공통 미들웨어
    - CORS
    - 예외 핸들러
    """
    setup_logging() # 로그 레벨 설정
    # 미들웨어 적용 순서 중요 (CORS가 제일 바깥쪽)
    setup_common_middleware(app)  # 공통 미들웨어
    setup_cors(app) # CORS
    register_exception_handlers(app) # 예외 핸들러
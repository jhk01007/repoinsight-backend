import logging

from fastapi import FastAPI
from fastapi.logger import logger as fastapi_logger
from starlette.middleware.cors import CORSMiddleware

from common.exception_handers import register_exception_handlers
from common.config.middleware import add_middlewares


def setup_logging() -> None:
    """기본 로깅 설정."""
    logging.basicConfig(level=logging.INFO)
    fastapi_logger.setLevel(logging.INFO)


def setup_cors(app: FastAPI) -> None:
    """CORS 설정."""
    origins = [
        "http://localhost:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_app(app: FastAPI) -> None:
    """
    FastAPI 앱에 공통 설정을 적용한다.
    - 로깅
    - CORS
    - 예외 핸들러
    - 공통 미들웨어
    """
    setup_logging()
    setup_cors(app)
    add_middlewares(app)
    register_exception_handlers(app)
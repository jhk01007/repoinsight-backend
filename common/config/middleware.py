import time

from fastapi import FastAPI
from fastapi.logger import logger


def add_middlewares(app: FastAPI) -> None:
    """공통 미들웨어 등록."""

    @app.middleware("http")
    async def log_request_time(request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start

        path = request.url.path
        method = request.method

        logger.info(f"[{method}] {path} - {elapsed:.4f}s")

        return response
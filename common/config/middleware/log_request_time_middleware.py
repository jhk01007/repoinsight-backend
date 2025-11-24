import time

from fastapi import Request
from fastapi.logger import logger
from starlette.responses import Response

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class LogRequestTimeMiddleware(BaseHTTPMiddleware):
    """ API 요청 시간 로거 미들웨어"""
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        logger.info(f"요청자: {request.client.host}:{request.client.port}")
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start

        path = request.url.path
        method = request.method

        logger.info(f"[{method}] {path} - {elapsed:.4f}s")

        return response
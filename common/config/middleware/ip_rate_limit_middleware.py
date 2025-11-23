from fastapi import Request
from fastapi.logger import logger
from fastapi.responses import JSONResponse
from starlette.responses import Response

from common.config.redis_client import get_redis_client
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# 한 IP당 허용할 시간 당 요청 수
WINDOW_SECONDS = 3600   # 1시간에
RATE_LIMIT = 60      #  60번 까지

# Limit을 적용할 엔드포인트
ENDPOINT_BLACK_LIST = ["/api/v1/repositories/search"]

redis_client = get_redis_client()


class IPRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Redis를 이용한 IP 레이트 리미터.
        - key: rate_limit:{ip}
        - 값: 현재 윈도우에서의 요청 횟수
        """
        path = request.url.path

        # 블랙 리스트에 포함되지 않는 엔드포인트면 통과
        if path not in ENDPOINT_BLACK_LIST:
            return await call_next(request)

        client_ip = request.client.host

        # IP별 카운터 키
        key = f"rate_limit:{client_ip}"

        try:
            # 첫 요청에서만 TTL 설정
            current_count = redis_client.incr(key)
            if current_count == 1:
                await redis_client.expire(key, WINDOW_SECONDS)

            if current_count > RATE_LIMIT:
                # 제한 초과 → 429 반환
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "요청 횟수가 너무 많습니다. 시간이 지난 뒤에 다시 요청해주세요.",
                    },
                )
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")

        return await call_next(request)
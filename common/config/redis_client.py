import os

import redis


def get_redis_client() -> redis.Redis:
    """
    전역에서 공유해서 쓰는 Redis 클라이언트.
    """
    redis_url = os.getenv("REDIS_URL")
    return redis.Redis.from_url(redis_url)
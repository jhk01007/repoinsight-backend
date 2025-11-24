import httpx
import os
from typing import Any

SEARCH_URL = "https://api.github.com/search/repositories"

HEADERS = {
    "Authorization": f"token {os.getenv("GIT_API_TOKEN")}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def load_search_results(
    query: str,
    sort: str,
    order: str,
    per_page: int = 5,
) -> list[dict[str, Any]]:
    """
    GitHub Search API 호출 전용 함수.

    파라미터:
    - query: 검색 쿼리 (예: 'language:python stars:>1000')
    - sort: 정렬 기준 (예: 'stars', 'forks', 'updated')
    - order: 정렬 방향 ('asc' 또는 'desc')
    - per_page: 페이지당 결과 수
    """

    params = {
        "q": query,
        "sort": sort,
        "order": order,
        "per_page": per_page,
    }

    with httpx.Client(timeout=20.0, headers=HEADERS) as client:
        response = client.get(SEARCH_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("items", [])
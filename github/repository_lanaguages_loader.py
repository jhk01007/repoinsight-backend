import httpx
from typing import Any

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}



def load_repository_languages(
    languages_url: str,
) -> dict[str, int]:
    """
    GitHub Repository 객체 하나를 받아서, languages API를 호출하고
    언어별 byte 수 dict를 그대로 반환한다.

    파라미터:
    - repository: GitHub Search API 결과의 item(dict)
      반드시 'languages_url' 키를 포함해야 한다.

    반환 예:
    {
        "Python": 40479,
        "Shell": 1352
    }
    """

    with httpx.Client(timeout=20.0, headers=HEADERS) as client:
        response = client.get(languages_url)
        response.raise_for_status()
        return response.json()
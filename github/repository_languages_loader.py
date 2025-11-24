import httpx
import os

HEADERS = {
    "Authorization": f"token {os.getenv('GIT_API_TOKEN')}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

def load_repository_languages(languages_url: str) -> dict[str, int]:
    """
    GitHub Repository의 languages_url을 호출하여
    언어별 byte 수 dict를 그대로 반환한다.

    예시 응답:
    {
        "Python": 40479,
        "Shell": 1352
    }
    """
    with httpx.Client(timeout=20.0, headers=HEADERS) as client:
        response = client.get(languages_url)
        response.raise_for_status()
        return response.json()
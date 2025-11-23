import base64
import os
import httpx
import yaml
import time
from pathlib import Path

from common.exceptions import UnsupportedLanguageError, LinguistFetchError

URL = "https://api.github.com/repos/github-linguist/linguist/contents/lib/linguist/languages.yml"
PROJECT_ROOT = Path(__file__).resolve().parents[0]  # github
CACHE_PATH = PROJECT_ROOT / "data" / "linguist_languages.yml"
CACHE_TTL = 60 * 60 * 24  # 24시간

headers = {
    "Authorization": f"token {os.getenv("GITHUB_TOKEN")}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def validate_support(languages: list[str]):
    supported = _fetch_languages_as_set()
    unsupported = [lang for lang in languages if lang.lower() not in supported]

    if unsupported:
        raise UnsupportedLanguageError(f"지원 되지 않는 언어입니다: {', '.join(unsupported)}")

def find_languages_list_by_query(query: str):
    languages = _fetch_languages_as_set()

    # 대소문자 무시하고 포함 여부 필터링
    filtered = [
        lang for lang in languages
        if query.lower() in lang.lower()
    ]

    # 알파벳 순 정렬
    filtered_sorted = sorted(filtered)

    return filtered_sorted


def _fetch_languages_as_set() -> set[str]:
    raw = _load_cached_or_fetch()
    yml = yaml.safe_load(raw)
    if not isinstance(yml, dict):
        raise LinguistFetchError("YAML root is not a mapping/dict")

    return {key.lower() for key in yml.keys()}


def _load_cached_or_fetch() -> str:
    # 캐시 디렉토리 생성
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 캐시가 있고 TTL 이내면 그대로 사용
    if CACHE_PATH.exists():
        mtime = CACHE_PATH.stat().st_mtime
        if time.time() - mtime < CACHE_TTL:
            return CACHE_PATH.read_text(encoding="utf-8")

    # 아니면 GitHub에서 새로 가져와서 저장
    with httpx.Client(timeout=20.0, headers=headers) as client:
        r = client.get(URL)
        r.raise_for_status()
        data = r.json()

    if data.get("encoding") != "base64" or "content" not in data:
        raise LinguistFetchError("Unexpected GitHub API response: no base64 content")

    b64 = data["content"].encode("utf-8")
    raw = base64.b64decode(b64).decode("utf-8")

    CACHE_PATH.write_text(raw, encoding="utf-8")
    return raw
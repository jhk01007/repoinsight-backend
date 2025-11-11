import base64
import httpx
import yaml

URL = "https://api.github.com/repos/github-linguist/linguist/contents/lib/linguist/languages.yml"

headers = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

def validate_include(languages: list):
    # 모든 언어가 지원 되는지 검사
    unsupported = [lang for lang in languages if lang not in _fetch_languages_as_set()]
    if unsupported:
        raise ValueError(f"지원 되지 않는 언어 입니다: {', '.join(unsupported)}")


def _fetch_languages_as_set() -> set[str]:
    # 1) 요청
    with httpx.Client(timeout=20.0, headers=headers) as client:
        r = client.get(URL)
        r.raise_for_status()
        data = r.json()

    # 2) Base64 디코딩
    if data.get("encoding") != "base64" or "content" not in data:
        raise ValueError("Unexpected GitHub API response: no base64 content")
    b64 = data["content"].encode("utf-8")
    raw = base64.b64decode(b64).decode("utf-8")

    # 3) YAML 파싱 → 딕셔너리의 최상위 키가 언어 이름
    yml = yaml.safe_load(raw)
    if not isinstance(yml, dict):
        raise ValueError("YAML root is not a mapping/dict")

    # 4) 최상위 key를 set으로 변환
    return set(yml.keys())

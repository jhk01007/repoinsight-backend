from __future__ import annotations

import time
from typing import Iterable, List, Tuple, Optional
import httpx
from langchain_text_splitters import MarkdownHeaderTextSplitter
from urllib.parse import urlparse


# ---- Module-level configuration and functions ----
DEFAULT_HEADERS_TO_SPLIT_ON: List[Tuple[str, str]] = [("##", "Topic")]
DEFAULT_TIMEOUT: float = 30.0
DEFAULT_MAX_RETRIES: int = 2
DEFAULT_BACKOFF_SEC: float = 0.8
DEFAULT_ACCEPT_HEADER: str = "text/markdown"
DEFAULT_FOLLOW_REDIRECTS: bool = True
DEFAULT_USER_AGENT: str = "repoinsight/1.0"


def split_url(
    doc_url: str,
    headers_to_split_on: Iterable[Tuple[str, str]] = DEFAULT_HEADERS_TO_SPLIT_ON,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_sec: float = DEFAULT_BACKOFF_SEC,
    client: Optional[httpx.Client] = None,
    accept_header: str = DEFAULT_ACCEPT_HEADER,
    follow_redirects: bool = DEFAULT_FOLLOW_REDIRECTS,
    user_agent: str = DEFAULT_USER_AGENT,
):
    """고수준 단일 호출: GitHub Docs 페이지 URL을 받아 분할된 문서 리스트 반환.

    클래스 없이 함수 중심으로 동작하도록 구성.
    외부에서 httpx.Client를 재사용하고 싶다면 client 인자를 넘기면 된다.
    """
    md_url = _get_markdown_url(doc_url)
    md_text = _fetch_markdown(
        md_url=md_url,
        timeout=timeout,
        max_retries=max_retries,
        backoff_sec=backoff_sec,
        client=client,
        accept_header=accept_header,
        follow_redirects=follow_redirects,
        user_agent=user_agent,
    )
    return _split_markdown(md_text, headers_to_split_on=headers_to_split_on)


def _get_markdown_url(doc_url: str) -> str:
    """https://docs.github.com/<lang>/... -> https://docs.github.com/api/article/body?pathname=/<lang>/..."""
    path = urlparse(doc_url).path
    return f"https://docs.github.com/api/article/body?pathname={path}"


def _fetch_markdown(
    *,
    md_url: str,
    timeout: float,
    max_retries: int,
    backoff_sec: float,
    client: Optional[httpx.Client],
    accept_header: str,
    follow_redirects: bool,
    user_agent: str,
) -> str:
    last_err: Optional[Exception] = None

    # 외부에서 client를 넘기지 않으면 이 함수 내에서 생성/정리
    owns_client = client is None
    if client is None:
        client = httpx.Client(
            timeout=timeout,
            follow_redirects=follow_redirects,
            headers={"User-Agent": user_agent},
        )

    try:
        for attempt in range(max_retries + 1):
            try:
                r = client.get(md_url, headers={"Accept": accept_header})
                r.raise_for_status()
                return r.text
            except Exception as e:
                last_err = e
                if attempt >= max_retries:
                    break
                time.sleep(backoff_sec * (2 ** attempt))
    finally:
        if owns_client:
            client.close()

    assert last_err is not None
    raise last_err


def _split_markdown(
    md_text: str,
    *,
    headers_to_split_on: Iterable[Tuple[str, str]] = DEFAULT_HEADERS_TO_SPLIT_ON,
):
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=list(headers_to_split_on),
        # 헤더를 보존하는 편이 섹션 타이틀 추출/메타 구성에 유리
        strip_headers=False,
    )
    return splitter.split_text(md_text)
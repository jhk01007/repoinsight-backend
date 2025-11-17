from __future__ import annotations

import time
from typing import List, Tuple, Optional
import httpx
from langchain_text_splitters import MarkdownHeaderTextSplitter
from urllib.parse import urlparse


# ---- Module-level configuration and functions ----
HEADERS_TO_SPLIT_ON: List[Tuple[str, str]] = [("##", "Topic")]
TIMEOUT: float = 30.0
MAX_RETRIES: int = 2
BACKOFF_SEC: float = 0.8
ACCEPT_HEADER: str = "text/markdown"
FOLLOW_REDIRECTS: bool = True
USER_AGENT: str = "repoinsight/1.0"


def split_url(doc_url: str):
    """GitHub Docs 페이지 URL을 받아 분할된 문서 리스트 반환.
    """
    md_url = _get_markdown_url(doc_url)
    md_text = _fetch_markdown(
        md_url=md_url,
    )
    return _split_markdown(md_text)


def _get_markdown_url(doc_url: str) -> str:
    """https://docs.github.com/<lang>/... -> https://docs.github.com/api/article/body?pathname=/<lang>/..."""
    path = urlparse(doc_url).path
    return f"https://docs.github.com/api/article/body?pathname={path}"


def _fetch_markdown(md_url: str) -> str:
    last_err: Optional[Exception] = None

    client = httpx.Client(
        timeout=TIMEOUT,
        follow_redirects=FOLLOW_REDIRECTS,
        headers={"User-Agent": USER_AGENT},
    )

    try:
        for attempt in range(MAX_RETRIES + 1):
            try:
                r = client.get(md_url, headers={"Accept": ACCEPT_HEADER})
                r.raise_for_status()
                return r.text
            except Exception as e:
                last_err = e
                if attempt >= MAX_RETRIES:
                    break
                time.sleep(BACKOFF_SEC * (2 ** attempt))
    finally:
        if client:
            client.close()

    assert last_err is not None
    raise last_err


def _split_markdown(
    md_text: str,
):
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=list(HEADERS_TO_SPLIT_ON),
        strip_headers=False,
    )
    return splitter.split_text(md_text)
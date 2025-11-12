from __future__ import annotations

import time
from typing import Iterable, List, Tuple, Optional
import httpx
from langchain_text_splitters import MarkdownHeaderTextSplitter
from urllib.parse import urlparse



class WebGithubDocsSplitter:
    """
    GitHub Docs URL -> Markdown API URL 변환 -> 마크다운 페치 -> 헤더 기준 분할.
    - httpx.Client 재사용으로 커넥션 비용 절감
    - 헤더 규칙/타임아웃/리트라이 등 공통 옵션 보관
    """
    def __init__(
        self,
        headers_to_split_on: Iterable[Tuple[str, str]] = (("##", "Topic"),),
        timeout: float = 30.0,
        max_retries: int = 2,
        backoff_sec: float = 0.8,
        client: Optional[httpx.Client] = None,
        accept_header: str = "text/markdown",
        follow_redirects: bool = True,
        user_agent: str = "repoinsight/1.0",
    ) -> None:
        self.headers_to_split_on: List[Tuple[str, str]] = list(headers_to_split_on)
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_sec = backoff_sec
        self.accept_header = accept_header
        self.follow_redirects = follow_redirects
        self.user_agent = user_agent
        self._owns_client = client is None
        self.client = client or httpx.Client(
            timeout=self.timeout,
            follow_redirects=self.follow_redirects,
            headers={"User-Agent": self.user_agent},
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    # ---- public API ---------------------------------------------------------
    def split_url(self, doc_url: str):
        """
        고수준 단일 호출: GitHub Docs 페이지 URL을 받아 분할된 문서 리스트 반환
        """
        md_url = self._get_markdown_url(doc_url)
        md_text = self._fetch_markdown(md_url)
        return self._split_markdown(md_text)

    # ---- helpers ------------------------------------------------------------
    @staticmethod
    def _get_markdown_url(doc_url: str) -> str:
        """
        https://docs.github.com/<lang>/...  ->  https://docs.github.com/api/article/body?pathname=/<lang>/...
        """
        path = urlparse(doc_url).path
        return f"https://docs.github.com/api/article/body?pathname={path}"

    def _fetch_markdown(self, md_url: str) -> str:
        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                r = self.client.get(md_url, headers={"Accept": self.accept_header})
                r.raise_for_status()
                return r.text
            except Exception as e:
                last_err = e
                if attempt >= self.max_retries:
                    break
                time.sleep(self.backoff_sec * (2 ** attempt))
        assert last_err is not None
        raise last_err

    def _split_markdown(self, md_text: str):
        splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            # 헤더를 보존하는 편이 섹션 타이틀 추출/메타 구성에 유리
            strip_headers=False
        )
        return splitter.split_text(md_text)
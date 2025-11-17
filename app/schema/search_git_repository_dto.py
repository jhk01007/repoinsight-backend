from pydantic import BaseModel, HttpUrl

from app.schema.langauage_ratio import LanguageRatio


class SearchGitRepositoryDTO(BaseModel):
    name: str # 리포지토리 이름
    function_summary: list[str] # 리포지토리 기능 요약
    languages: list[LanguageRatio] # 각 언어별 비율
    stargazers_count: int # 스타 수
    html_url: HttpUrl  # GitHub 리포지토리 링크

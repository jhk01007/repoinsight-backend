from pydantic import BaseModel, Field


class GithubRepoSearchReq(BaseModel):
    keyword: str = Field(max_length=50, description="키워드는 50자를 넘을 수 없습니다.") # 리포지토리 키워드
    languages: list[str] = []# 리포지토리 언어 목록
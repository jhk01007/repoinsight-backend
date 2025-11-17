from pydantic import BaseModel

class GithubRepoSearchReq(BaseModel):
    keyword: str # 리포지토리 키워드
    languages: list[str] = []# 리포지토리 언어 목록
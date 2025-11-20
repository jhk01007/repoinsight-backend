from pydantic import BaseModel


class RepoLanguagesSearchResp(BaseModel):
    results: list[str] # 검색 결과로 나온 언어
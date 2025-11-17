from fastapi import FastAPI
from pydantic import BaseModel

from schema.github_repo_search_req import GithubRepoSearchReq
from schema.github_repo_search_resp import GithubRepoSearchResp

from service.github_search_service import search

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


# API 응답용 래핑 모델
class WrappingSearchingResponse(BaseModel):
    results: list[GithubRepoSearchResp]


@app.post("/api/v1/repositories/search", response_model=WrappingSearchingResponse)
def search_repository(request: GithubRepoSearchReq):
    # 검색
    results = search(request.keyword, request.languages)
    return WrappingSearchingResponse(results=results)

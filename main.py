from fastapi import FastAPI
from pydantic import BaseModel

from schema.github_repository_search_request import GithubRepositorySearchRequest
from schema.github_repository_search_response import GithubRepositorySearchResponse

from service.github_search_service import search

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


# API 응답용 래핑 모델
class WrappingSearchingResponse(BaseModel):
    results: list[GithubRepositorySearchResponse]


@app.post("/api/v1/repositories/search", response_model=WrappingSearchingResponse)
def search_repository(request: GithubRepositorySearchRequest):
    # 검색
    results = search(request.keyword, request.languages)
    return WrappingSearchingResponse(results=results)

# main.py
from typing import Annotated

from fastapi import FastAPI
from fastapi.params import Query
from pydantic import BaseModel

from schema.repo_search_req import RepoSearchReq
from schema.repo_search_resp import RepoSearchResp
from schema.repo_lanaguages_search_resp import RepoLanguagesSearchResp

from service.github_search_service import search
from github.languages import find_languages_list_by_query

from common.config.app_setup import setup_app
from common.config.lifespan import lifespan

# lifespan으로 startup 관리
app = FastAPI(lifespan=lifespan)

# 공통 설정(로깅, CORS, 미들웨어, 예외 핸들러 등)
setup_app(app)


# API 응답용 래핑 모델
class WrappingSearchingResponse(BaseModel):
    results: list[RepoSearchResp]


@app.post("/api/v1/repositories/search", response_model=WrappingSearchingResponse)
async def search_repository(request: RepoSearchReq):
    # 검색
    results = await search(request.keyword, request.languages)
    return WrappingSearchingResponse(results=results)


@app.get(
    path="/api/v1/repositories/languages/search",
    description='깃허브 리포지토리 검색 시 지원되는 언어 목록 중에서 특정 단어가 포함되는 언어 목록을 검색',
    response_model=RepoLanguagesSearchResp,
)
def search_repository_languages_list(query: Annotated[str, Query(min_length=1)]):
    results = find_languages_list_by_query(query)
    return RepoLanguagesSearchResp(results=results)
import logging
import time
from typing import Annotated

from fastapi import FastAPI
from fastapi.logger import logger as fastapi_logger
from fastapi.params import Query
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from common.exception_handers import register_exception_handlers
from schema.repo_search_req import RepoSearchReq
from schema.repo_search_resp import RepoSearchResp
from schema.repo_lanaguages_search_resp import RepoLanguagesSearchResp

from service.github_search_service import search
from github.languages import find_languages_list_by_query

app = FastAPI()

# 기본 로깅 설정
logging.basicConfig(level=logging.INFO)

# fastapi 로거 레벨도 DEBUG로 맞춰주기
fastapi_logger.setLevel(logging.INFO)

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# API 응답용 래핑 모델
class WrappingSearchingResponse(BaseModel):
    results: list[RepoSearchResp]


@app.post("/api/v1/repositories/search", response_model=WrappingSearchingResponse)
def search_repository(request: RepoSearchReq):
    # 검색
    results = search(request.keyword, request.languages)
    return WrappingSearchingResponse(results=results)


@app.get(
    path="/api/v1/repositories/languages/search",
    description='깃허브 리포지토리 검색 시 지원되는 언어 목록 중에서 특정 단어가 포함되는 언어 목록을 검색',
    response_model=RepoLanguagesSearchResp
)
def search_repository_languages_list(query: Annotated[str, Query(min_length=1)]):
    results = find_languages_list_by_query(query)
    return RepoLanguagesSearchResp(results=results)



# 예외 핸들러 등록
register_exception_handlers(app)

# 요청 처리 시간 로그 미들웨어
@app.middleware("http")
async def log_request_time(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start

    path = request.url.path
    method = request.method

    print(f"[{method}] {path} - {elapsed:.4f}s")

    return response
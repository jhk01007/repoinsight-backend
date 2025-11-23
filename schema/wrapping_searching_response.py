# API 응답용 래핑 모델
from pydantic import BaseModel

from schema.repo_search_resp import RepoSearchResp


class WrappingSearchingResponse(BaseModel):
    results: list[RepoSearchResp]
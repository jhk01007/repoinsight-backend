from pydantic import BaseModel
from typing import List
from datetime import datetime

from schema.langauage_ratio import LanguageRatio


class RepositorySummaryDTO(BaseModel):
    name: str  # 리포지토리 이름
    description: str  # 설명
    languages: List[LanguageRatio]  # 언어
    topics: List[str]  # 토픽
    pushed_at: datetime  # 최근 수정일

from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError


class RepoSearchReq(BaseModel):
    keyword: str = Field(max_length=50, description="키워드는 50자를 넘을 수 없습니다.") # 리포지토리 키워드
    languages: list[str] = [] # 리포지토리 언어 목록

    @field_validator("keyword", mode="before")
    def validate_keyword(cls, v):
        if len(v) > 50:
            raise PydanticCustomError(
                "keyword_too_long",
                "키워드는 50자를 넘을 수 없습니다"
            )
        return v
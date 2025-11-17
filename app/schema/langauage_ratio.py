from pydantic import BaseModel


class LanguageRatio(BaseModel):
    name: str
    ratio: str
from typing import List

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from langchain.prompt.search_prompt import simple_summary_prompt, simple_summary_prompt_async

CHAT_MODEL = 'gpt-4.1-nano'


class SummaryList(BaseModel):
    # repos 순서대로, 각 리포지토리당 3줄 요약 리스트
    summaries: list[str]

class SimpleGithubRepositorySummaryChain:
    def __init__(self):
        simple_summary_prompt_template = PromptTemplate(
            template=simple_summary_prompt_async,
            input_variables=["repo"],
        )

        llm = ChatOpenAI(model=CHAT_MODEL).with_structured_output(SummaryList)
        self.summary_chain = simple_summary_prompt_template | llm

    async def ainvoke(self, metadata: dict) -> list[str]:
        """
        metadata: 리포지토리의 메타데이터 정보
        반환값: 리포지토리 3줄 요약
        """
        result: SummaryList = await self.summary_chain.ainvoke(
            {"repo": metadata}
        )
        return result.summaries
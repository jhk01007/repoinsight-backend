from typing import List

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.langchain.prompt.search_prompt import simple_summary_prompt

CHAT_MODEL = 'gpt-4.1-mini'


class SummaryList(BaseModel):
    # repos 순서대로, 각 리포지토리당 3줄 요약 리스트
    summaries: List[List[str]]


class SimpleGithubRepositorySummaryChain:
    def __init__(self):
        simple_summary_prompt_template = PromptTemplate(
            template=simple_summary_prompt,
            input_variables=["repo_list"],
        )

        llm = ChatOpenAI(model=CHAT_MODEL).with_structured_output(SummaryList)
        self.summary_chain = simple_summary_prompt_template | llm

    def invoke(self, metadata_list: list[dict]) -> list[list[str]]:
        """
        metadata_list: GithubRepositorySummaryDTO 들을 dict로 변환한 리스트
        반환값: 각 리포지토리당 3줄 요약 리스트
        """
        result: SummaryList = self.summary_chain.invoke({"repo_list": metadata_list})
        return result.summaries

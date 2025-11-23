from dotenv import load_dotenv
from fastapi.logger import logger
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_openai import ChatOpenAI

from operator import itemgetter
from datetime import datetime

from github.web_docs_loader import fetch_github_docs
from langchain.prompt.search_prompt import translate_prompt, search_query_prompt

from langchain.vector_store.github_search_qualifier_store_base import GithubSearchQualifierStoreBase

load_dotenv()

REPOSITORIES_SEARCH_DOCS_URL = "https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories"
HEADERS_TO_SPLIT_ON = [("##", "Topic")]


class GithubSearchQueryChain:
    """ GitHub Search Query Builder """

    def __init__(self, vector_db: GithubSearchQualifierStoreBase):
        """외부에서 Vector DB 주입"""


        retriever = vector_db.get_retriever(top_k=5)

        translate_chain = self._get_translation_chain()
        search_query_chain = self._get_search_query_chain()

        def debug(name):
            return RunnableLambda(lambda x: (logger.info(f"{name}: {x}"), x)[1])

        self.search_query_chain = (
                RunnablePassthrough()
                .assign(
                    current_date=RunnableLambda(lambda _: datetime.now().strftime("%Y-%m-%d")) | debug("현재 날짜"),
                    original_question=RunnableLambda(itemgetter("question")) | debug("원본 질문"),
                    languages=RunnableLambda(itemgetter("languages")) | debug("언어 목록"),
                )
                .assign(
                    translated_question=RunnableLambda(itemgetter("original_question")) | translate_chain | debug("번역된 질문"),
                )
                .assign(
                    question=RunnableLambda(itemgetter("translated_question")),
                    context=RunnableLambda(itemgetter("translated_question"))
                            | retriever
                            | RunnableLambda(lambda docs: [doc.metadata for doc in docs])
                            | debug("찾아온 문서"),
                )
                | search_query_chain
        )

    @staticmethod
    def _load_search_docs():
        md_text = fetch_github_docs(REPOSITORIES_SEARCH_DOCS_URL)
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=HEADERS_TO_SPLIT_ON, strip_headers=False)
        return splitter.split_text(md_text)

    @staticmethod
    def _get_translation_chain():
        """
        필요한 입력값: question(사용자의 요청)
        """
        llm = ChatOpenAI(model="gpt-4.1-mini")
        translate_question_template = PromptTemplate(
            template=translate_prompt,
            input_variables=["question"])
        return translate_question_template | llm | StrOutputParser()

    @staticmethod
    def _get_search_query_chain():
        """
        필요한 입력값:
            - current_date: 현재 날짜
            - question: 사용자의 요청
            - context: 검색 한정자 사용법
            - languages: 사용자가 선택한 언어 목록
        """
        llm = ChatOpenAI(model="gpt-4.1")
        search_query_template = PromptTemplate.from_template(
            search_query_prompt,
            template_format="jinja2"
        )
        return search_query_template | llm | StrOutputParser()

    def invoke(self, question: str, languages: list):
        return self.search_query_chain.invoke({"question": question, "languages": languages})
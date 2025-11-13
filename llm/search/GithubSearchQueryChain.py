from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from git_languages import validate_support
from llm.search.WebGithubDocsSplitter import WebGithubDocsSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pinecone import Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from uuid import uuid4
import os
from dotenv import load_dotenv
from prompt import translate_prompt, search_qualifier_prompt
from operator import itemgetter
from datetime import datetime

load_dotenv()

# --- 전역 변수 ---
REPOSITORIES_SEARCH_DOCS_URL = "https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories"
ISSUES_AND_PRS_DOCS_URL = "https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests"

INDEX_NAME = "github-search-qualifiers"
EMBEDDING_MODEL = 'text-embedding-3-large'
EMBEDDING_MODEL_DIMENSION = 3072
EMBEDDING_MODEL_METRIC = "cosine"

SEARCH_QUALIFIER_CHAT_MODEL = 'gpt-4.1'
TRANSLATE_CHAT_MODEL = 'gpt-4.1-mini'

REPO_QUALIFIERS_NAMESPACE = "repo-qualifiers"


# ISSUE_PR_QUALIFIERS_NAMESPACE = "issue-pr-qualifiers"

class GithubSearchQualifierChain:

    def __init__(self):

        # Pinecone 인덱스 생성
        is_created, github_search_qualifiers_index = self._create_pinecone_index(index_name=INDEX_NAME)

        # 인덱스가 새로 만들어진 경우에만 저장
        embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        if is_created:
            # 깃허브 검색 한정자 문서 쪼개기
            splitter = WebGithubDocsSplitter()
            repo_qualifiers_docs = splitter.split_url(REPOSITORIES_SEARCH_DOCS_URL)

            # 벡터 데이터베이스에 검색 한정자 저장
            self._save_docs(github_search_qualifiers_index, repo_qualifiers_docs, embedding)


        # chain 만들기
        vector_store = PineconeVectorStore(index=github_search_qualifiers_index, embedding=embedding,
                                           namespace=REPO_QUALIFIERS_NAMESPACE)
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})  # 5개의 결과를 가져오도록

        translate_chain = self._get_translation_chain()
        search_qualifier_chain = self._get_search_query_chain()


        def debug(name):
            return RunnableLambda(lambda x: (print(f"[DEBUG:{name}] {x}"), x)[1])

        self.search_qualifier_chain = (
                RunnablePassthrough().assign(
                    current_date=RunnableLambda(lambda _: datetime.now().strftime("%Y-%m-%d")) | debug("현재 날짜"),
                    query=RunnableLambda(itemgetter("query")) | translate_chain | debug("번역된 쿼리"),
                    context=RunnableLambda(itemgetter("query")) | translate_chain | retriever | debug("찾아온 문서"),
                    # context=RunnableLambda(lambda _: []) | debug("찾아온 문서"), # 참고 문서가 없는 경우 테스트
                    languages=RunnableLambda(itemgetter("languages")) | debug("언어 목록")
                )
                | search_qualifier_chain
        )

    @staticmethod
    def _create_pinecone_index(index_name: str):
        pinecone_api_key = os.environ.get("PINECONE_API_KEY")
        pc = Pinecone(api_key=pinecone_api_key)

        # 인덱스 존재 여부 확인
        if not pc.has_index(index_name):
            # 인덱스 생성
            pc.create_index(
                name=index_name,
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                # text-embedding-3-large 스펙에 맞게 지정
                dimension=EMBEDDING_MODEL_DIMENSION,
                metric=EMBEDDING_MODEL_METRIC
            )
            return True, pc.Index(index_name)
        # 생성 여부와 관계 없이 밚환
        return False, pc.Index(index_name)

    @staticmethod
    def _save_docs(github_search_qualifiers_index, repo_qualifiers_docs, embedding):
        vector_store = PineconeVectorStore(index=github_search_qualifiers_index, embedding=embedding)
        # 레포 검색 한정자 저장
        uuids = [str(uuid4()) for _ in range(len(repo_qualifiers_docs))]
        vector_store.add_documents(
            documents=repo_qualifiers_docs, ids=uuids,
            namespace=REPO_QUALIFIERS_NAMESPACE
        )

    @staticmethod
    def _get_translation_chain():
        """
        필요한 입력값: query(사용자의 요청)
        """
        translate_query_template = PromptTemplate(
            template=translate_prompt,
            input_variables=["query"])
        llm = ChatOpenAI(model=TRANSLATE_CHAT_MODEL)

        return translate_query_template | llm | StrOutputParser()

    @staticmethod
    def _get_search_query_chain():
        """
        필요한 입력값:
            - current_date: 현재 날짜
            - query: 사용자의 요청
            - context: 검색 한정자 사용법
            - languages: 사용자가 선택한 언어 목록
        """
        search_qualifier_template = PromptTemplate.from_template(
            search_qualifier_prompt,
            template_format="jinja2"
        )
        llm = ChatOpenAI(model=SEARCH_QUALIFIER_CHAT_MODEL)

        return search_qualifier_template | llm | StrOutputParser()

    def invoke(self,
               query: str, languages: list):
        # 모든 언어가 지원 되는지 검사
        validate_support(languages)

        return self.search_qualifier_chain.invoke({"query": query, "languages": languages})


# 테스트
github_search_chain = GithubSearchQualifierChain()
response = github_search_chain.invoke(query="챗봇 만들기", languages=["Java", "Python", "JavaScript"])
print(response)

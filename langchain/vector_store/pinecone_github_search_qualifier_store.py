import os
from abc import ABC
from uuid import uuid4
from dotenv import load_dotenv
from langchain_text_splitters import MarkdownHeaderTextSplitter

from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore

from langchain_openai import OpenAIEmbeddings
from langchain.vector_store.github_search_qualifier_store_base import GithubSearchQualifierStoreBase

from github.web_docs_loader import fetch_github_docs

REPOSITORIES_SEARCH_DOCS_URL = "https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories"
HEADERS_TO_SPLIT_ON = [("##", "Topic")]

load_dotenv()

class PineconeGithubSearchQualifierStore(GithubSearchQualifierStoreBase, ABC):

    def __init__(self,
                 index_name: str = "github-search-qualifiers", namespace: str ="default", dim=3072, metric="cosine"):
        self._index_name = index_name
        self._namespace = namespace
        self.pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.embedding = OpenAIEmbeddings(model="text-embedding-3-large")

        # 벡터 스토어 초기화
        self._store = self._initialize(index_name, namespace, dim, metric)

    def _initialize(self, index_name: str, namespace: str, dim: int, metric: str):

        # 인덱스 존재 여부 확인 후 존재하지 않는 경우에만 생성 및 저장
        if not self.pinecone_client.has_index(index_name):
            self.pinecone_client.create_index(
                name=index_name,
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                dimension=dim,
                metric=metric,
            )
            self._save_documents()

        index = self.pinecone_client.Index(index_name)
        return PineconeVectorStore(index=index, embedding=self.embedding, namespace=namespace)

    def get_retriever(self, top_k: int):
        return self._store.as_retriever(search_kwargs={"k": top_k})

    def _save_documents(self):
        repo_docs = self._load_search_docs()
        uuids = [str(uuid4()) for _ in range(len(repo_docs))]
        self._store.add_documents(documents=repo_docs, ids=uuids)

    def refresh_documents(self):
        """
        문서가 업데이트되는 것을 대비하여
        GitHub 검색 문서를 다시 읽어서
        현재 namespace의 벡터들을 모두 삭제하고 새로 저장한다.
        (하루 1번 스케줄링해서 호출하는 용도)
        """
        # 1) 현재 namespace의 모든 벡터 삭제
        self._store.delete(delete_all=True, namespace=self._namespace)

        # 2) 새 문서 저장
        self._save_documents()

    @staticmethod
    def _load_search_docs():
        md_text = fetch_github_docs(REPOSITORIES_SEARCH_DOCS_URL)
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=HEADERS_TO_SPLIT_ON, strip_headers=False)
        return splitter.split_text(md_text)
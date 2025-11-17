import os
from uuid import uuid4
from dotenv import load_dotenv

from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore

from langchain_openai import OpenAIEmbeddings
from langchain.vector_store.github_search_qualifier_store_base import GithubSearchQualifierStoreBase

load_dotenv()


class PineconeGithubSearchQualifierStore(GithubSearchQualifierStoreBase):

    def __init__(self, index_name: str, namespace="default", dim=3072, metric="cosine"):
        self.index_name = index_name
        self.namespace = namespace
        self.dim = dim
        self.metric = metric

        self._client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self._embedding = OpenAIEmbeddings(model="text-embedding-3-large")

    def _initialize(self):
        # 인덱스 존재 여부 확인 후 생성
        if not self._client.has_index(self.index_name):
            self._client.create_index(
                name=self.index_name,
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                dimension=self.dim,
                metric=self.metric,
            )

        return self._client.Index(self.index_name)

    def save_documents(self, documents: list):
        index = self._initialize()
        store = PineconeVectorStore(index=index, embedding=self._embedding, namespace=self.namespace)
        uuids = [str(uuid4()) for _ in range(len(documents))]
        store.add_documents(documents=documents, ids=uuids)

    def get_retriever(self, top_k: int):
        index = self._initialize()
        store = PineconeVectorStore(index=index, embedding=self._embedding, namespace=self.namespace)
        return store.as_retriever(search_kwargs={"k": top_k})
from abc import ABC, abstractmethod


class GithubSearchQualifierStoreBase(ABC):
    """벡터 DB 공통 인터페이스"""

    @abstractmethod
    def get_retriever(self, top_k: int):
        """검색기 리트리버 객체 반환"""
        pass
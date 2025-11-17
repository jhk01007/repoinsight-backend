from abc import ABC, abstractmethod


class GithubSearchQualifierStoreBase(ABC):
    """벡터 DB 공통 인터페이스"""

    @abstractmethod
    def _initialize(self):
        """DB 초기화 (없으면 생성)"""
        pass

    @abstractmethod
    def save_documents(self, documents: list[dict]):
        """문서를 벡터 DB에 저장"""
        pass

    @abstractmethod
    def get_retriever(self, top_k: int):
        """검색기 리트리버 객체 반환"""
        pass
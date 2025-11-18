class RepoInsightError(Exception):
    """도메인 공통 베이스 예외"""

class ClientError(RepoInsightError):
    """요청 잘못(400대)에 해당하는 예외"""

class ServerError(RepoInsightError):
    """서버/외부 서비스 문제(500대)에 해당하는 예외"""

class UnsupportedLanguageError(ClientError):
    """지원하지 않는 언어를 요청했을 때"""

class LinguistFetchError(ServerError):
    """GitHub linguist YAML을 못 가져오거나 파싱 실패했을 때"""
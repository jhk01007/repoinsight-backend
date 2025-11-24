import asyncio
import time

from dotenv import load_dotenv
from fastapi.logger import logger
from pydantic import HttpUrl

from github.languages import validate_support
from langchain.chain.github_search_query_chain import GithubSearchQueryChain
from langchain.chain.simple_github_repository_summary_chain import SimpleGithubRepositorySummaryChain
from langchain.vector_store.pinecone_github_search_qualifier_store import PineconeGithubSearchQualifierStore
from schema.repo_search_resp import RepoSearchResp
from schema.repo_summary_dto import RepositorySummaryDTO
from schema.langauage_ratio import LanguageRatio
from schema.order_by import OrderBy
from schema.sort_by import SortBy

from github.search_results_loader import load_search_results
from github.repository_languages_loader import load_repository_languages

_store = PineconeGithubSearchQualifierStore()
_query_chain = GithubSearchQueryChain(_store)

async def search(
    question: str,
    languages: list[str] | None = None,
    sort: SortBy = SortBy.STARS,
    order: OrderBy = OrderBy.DESC,
    per_page: int = 5,
) -> list[RepoSearchResp]:
    """
    GitHub 검색 + 언어 비율 조회 + LLM 요약을 실행하는 일종의 어셈블러 함수
    """

    # 지원 가능한 언어인지 검증
    validate_support(languages)

    if languages is None:
        languages = []

    # 1. Search Query 생성
    start = time.perf_counter()
    search_query = _build_search_query(question=question, languages=languages)
    elapsed = time.perf_counter() - start
    logger.info(f"Search Query 생성 실행 시간: {elapsed:.4f}초")
    logger.info(f"생성된 Search Query: {search_query}")

    # 2. 검색 API 호출 (로더로 분리)
    start = time.perf_counter()
    repos = load_search_results(
        query=search_query,
        sort=sort.value,
        order=order.value,
        per_page=per_page,
    )
    elapsed = time.perf_counter() - start
    logger.info(f"검색 API 실행 시간: {elapsed:.4f}초")

    # 3. 요약 입력 DTO + 보조 데이터 준비
    summary_dtos, languages_per_repo, html_urls, names, stargazers_list = await _build_summary_dtos_and_aux(repos)

    # 4. LLM 한 번 호출해서 요약 리스트 얻기
    start = time.perf_counter()
    summaries = await _summarize_repositories_parallel_async(summary_dtos) # 병렬 테스트
    elapsed = time.perf_counter() - start
    logger.info(f"리포지토리 요약 실행 시간: {elapsed:.4f}초")

    # 5. 최종 응답 DTO로 조립
    return _build_search_results(
        names=names,
        languages_per_repo=languages_per_repo,
        stargazers_list=stargazers_list,
        html_urls=html_urls,
        summaries=summaries,
    )


async def _build_summary_dtos_and_aux(
    repos: list[dict],
) -> tuple[list[RepositorySummaryDTO], list[list[LanguageRatio]], list[HttpUrl], list[str], list[int]]:
    """
    - LLM 요약 입력용 GithubRepositorySummaryDTO 리스트
    - 최종 응답 조립에 필요한 보조 데이터들
    을 한 번에 만든다.

    asyncio.to_thread 를 사용해 병렬로 처리하여 전체 응답 시간을 줄인다.
    """
    summary_dtos: list[RepositorySummaryDTO] = []
    languages_per_repo: list[list[LanguageRatio]] = []
    html_urls: list[HttpUrl] = []
    names: list[str] = []
    stargazers_list: list[int] = []

    async def build_one(repo: dict):
        # 언어 조회 API 호출은 동기 함수(load_repository_languages)를
        # 별도 스레드에서 실행하여 병렬화한다.
        lang_bytes = await asyncio.to_thread(
            load_repository_languages,
            repo["languages_url"],
        )
        languages = _convert_lang_bytes_to_ratios(lang_bytes)

        dto = RepositorySummaryDTO(
            name=repo["name"],
            description=repo.get("description") or "",
            languages=languages,
            topics=repo.get("topics", []),
            pushed_at=repo["pushed_at"],
        )
        return dto, languages, repo["html_url"], repo["name"], repo["stargazers_count"]

    # 모든 repo에 대한 작업을 동시에 실행
    results = await asyncio.gather(*(build_one(repo) for repo in repos))

    for dto, languages, html_url, name, stars in results:
        summary_dtos.append(dto)
        languages_per_repo.append(languages)
        html_urls.append(html_url)
        names.append(name)
        stargazers_list.append(stars)

    return summary_dtos, languages_per_repo, html_urls, names, stargazers_list


def _convert_lang_bytes_to_ratios(lang_bytes: dict[str, int]) -> list[LanguageRatio]:
    """
    GitHub languages API 응답(dict[str, int])을 LanguageRatio 리스트로 변환.
    예: {"Python": 40479, "Shell": 1352}
    """
    total = sum(lang_bytes.values())
    if total == 0:
        return []

    languages: list[LanguageRatio] = []
    for name, byte_count in lang_bytes.items():
        ratio_percent = byte_count / total * 100
        languages.append(LanguageRatio(name=name, ratio=f"{ratio_percent:.2f}%"))

    return languages


def _summarize_repositories(
    summary_dtos: list[RepositorySummaryDTO],
) -> list[list[str]]:
    """LLM 체인을 한 번만 호출해 각 리포지토리의 3줄 요약을 반환."""
    summary_chain = SimpleGithubRepositorySummaryChain()
    metadata_list = [dto.model_dump() for dto in summary_dtos]
    summaries: list[list[str]] = summary_chain.invoke(metadata_list)
    return summaries

async def _summarize_repositories_parallel_async(summary_dtos):
    """병렬 실행용 함수"""

    chain = SimpleGithubRepositorySummaryChain()
    async def one(dto):
        return await chain.ainvoke(dto.model_dump())

    return await asyncio.gather(*(one(dto) for dto in summary_dtos))

def _build_search_results(
    names: list[str],
    languages_per_repo: list[list[LanguageRatio]],
    stargazers_list: list[int],
    html_urls: list[HttpUrl],
    summaries: list[list[str]],
) -> list[RepoSearchResp]:
    """LLM 요약 결과와 원본 데이터를 조합해 최종 DTO 리스트를 만든다."""
    search_results: list[RepoSearchResp] = []

    for name, langs, stars, url, summary in zip(
        names, languages_per_repo, stargazers_list, html_urls, summaries
    ):
        result = RepoSearchResp(
            name=name,
            function_summary=summary,
            languages=langs,
            stargazers_count=stars,
            html_url=url,
        )
        search_results.append(result)

    return search_results

def _build_search_query(question: str, languages: list[str]):
    return _query_chain.invoke(question=question, languages=languages)
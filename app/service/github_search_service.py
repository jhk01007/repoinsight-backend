import httpx
from dotenv import load_dotenv
from pydantic import HttpUrl

from app.langchain.chain.GithubSearchQueryChain import GithubSearchQueryChain
from app.langchain.chain.SimpleGithubRepositorySummaryChain import SimpleGithubRepositorySummaryChain
from app.schema.SearchGitRepositoryDTO import SearchGitRepositoryDTO
from app.schema.GithubRepositorySummaryDTO import GithubRepositorySummaryDTO
from app.schema.LangauageRatio import LanguageRatio
from app.schema.OrderBy import OrderBy
from app.schema.SortBy import SortBy

SEARCH_URL = "https://api.github.com/search/repositories?q={query}&sort={sort}&order={order}&per_page={per_page}"

headers = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

load_dotenv()


def _fetch_language_ratios(languages_url: str, client: httpx.Client) -> list[LanguageRatio]:
    """각 리포지토리의 languages_url을 호출해서 LanguageRatio 리스트로 변환"""
    r = client.get(languages_url)
    r.raise_for_status()
    lang_bytes: dict[str, int] = r.json()  # 예: {"Python": 40479, "Shell": 1352}

    total = sum(lang_bytes.values())
    if total == 0:
        return []

    languages: list[LanguageRatio] = []
    for name, byte_count in lang_bytes.items():
        ratio_percent = byte_count / total * 100
        languages.append(LanguageRatio(name=name, ratio=f"{ratio_percent:.0f}%"))

    return languages


def _build_search_url(
    query: str,
    sort: SortBy,
    order: OrderBy,
    per_page: int,
) -> str:
    """검색 URL 문자열 생성."""
    return SEARCH_URL.format(
        query=query,
        sort=sort.value,
        order=order.value,
        per_page=per_page,
    )


def _fetch_search_items(client: httpx.Client, search_url: str) -> list[dict]:
    """GitHub 검색 API 호출 후 items 리스트만 반환."""
    r = client.get(search_url)
    r.raise_for_status()
    search_result = r.json()
    return search_result.get("items", [])


def _build_summary_dtos_and_aux(
    client: httpx.Client,
    items: list[dict],
) -> tuple[list[GithubRepositorySummaryDTO], list[list[LanguageRatio]], list[HttpUrl], list[str], list[int]]:
    """
    - LLM 요약 입력용 GithubRepositorySummaryDTO 리스트
    - 최종 응답 조립에 필요한 보조 데이터들
    을 한 번에 만든다.
    """
    summary_dtos: list[GithubRepositorySummaryDTO] = []
    languages_per_repo: list[list[LanguageRatio]] = []
    html_urls: list[HttpUrl] = []
    names: list[str] = []
    stargazers_list: list[int] = []

    for item in items:
        languages = _fetch_language_ratios(item["languages_url"], client)

        summary_dtos.append(
            GithubRepositorySummaryDTO(
                name=item["name"],
                description=item.get("description") or "",
                languages=languages,
                topics=item.get("topics", []),
                pushed_at=item["pushed_at"],
            )
        )

        languages_per_repo.append(languages)
        html_urls.append(item["html_url"])
        names.append(item["name"])
        stargazers_list.append(item["stargazers_count"])

    return summary_dtos, languages_per_repo, html_urls, names, stargazers_list


def _summarize_repositories(
    summary_dtos: list[GithubRepositorySummaryDTO],
) -> list[list[str]]:
    """LLM 체인을 한 번만 호출해 각 리포지토리의 3줄 요약을 반환."""
    summary_chain = SimpleGithubRepositorySummaryChain()
    metadata_list = [dto.model_dump() for dto in summary_dtos]
    summaries: list[list[str]] = summary_chain.invoke(metadata_list)
    return summaries


def _build_search_results(
    names: list[str],
    languages_per_repo: list[list[LanguageRatio]],
    stargazers_list: list[int],
    html_urls: list[HttpUrl],
    summaries: list[list[str]],
) -> list[SearchGitRepositoryDTO]:
    """LLM 요약 결과와 원본 데이터를 조합해 최종 DTO 리스트를 만든다."""
    search_results: list[SearchGitRepositoryDTO] = []

    for name, langs, stars, url, summary in zip(
        names, languages_per_repo, stargazers_list, html_urls, summaries
    ):
        result = SearchGitRepositoryDTO(
            name=name,
            function_summary=summary,
            languages=langs,
            stargazers_count=stars,
            html_url=url,
        )
        search_results.append(result)

    return search_results


def _build_search_query(question: str, languages: list[str]):
    query_chain = GithubSearchQueryChain()
    return query_chain.invoke(question=question, languages=languages)


def search(
    question: str,
    languages: list[str],
    sort: SortBy = SortBy.STARS,
    order: OrderBy = OrderBy.DESC,
    per_page: int = 5,
) -> list[SearchGitRepositoryDTO]:
    """
    GitHub 검색 + 언어 비율 조회 + LLM 요약까지 포함한 high-level 함수.
    """

    # 1. Search Query 생성
    search_query = _build_search_query(question=question, languages=languages)
    print(f'생성된 Search Query: {search_query}')

    # 2. Search url 생성
    search_url = _build_search_url(query=search_query, sort=sort, order=order, per_page=per_page)

    # 3. 검색
    with httpx.Client(timeout=20.0, headers=headers) as client:
        # 1) GitHub 검색
        items = _fetch_search_items(client, search_url)

        # 2) 요약 입력 DTO + 보조 데이터 준비
        summary_dtos, languages_per_repo, html_urls, names, stargazers_list = _build_summary_dtos_and_aux(
            client,
            items,
        )

        # 3) LLM 한 번 호출해서 요약 리스트 얻기
        summaries = _summarize_repositories(summary_dtos)

        # 4) 최종 응답 DTO로 조립
        return _build_search_results(
            names=names,
            languages_per_repo=languages_per_repo,
            stargazers_list=stargazers_list,
            html_urls=html_urls,
            summaries=summaries,
        )

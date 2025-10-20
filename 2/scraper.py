import asyncio
import logging
import ssl
from datetime import datetime, timedelta
from typing import Any
from collections import Counter

from aiohttp import ClientSession, ClientConnectorError, ClientError, TCPConnector
from aiolimiter import AsyncLimiter

from config import GITHUB_API_BASE_URL
from models import Repository, RepositoryAuthorCommitsNum


class GithubReposScrapper:
    def __init__(self, access_token: str, max_concurrent_requests: int = 30, requests_per_second:int = 5):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = TCPConnector(ssl=ssl_context)
        
        self._session = ClientSession(
            connector=connector,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"Bearer {access_token}",
            }
        )
        self._max_concurrent_requests = max_concurrent_requests
        self._requests_per_second = requests_per_second
        self._logger = logging.getLogger(__name__)
        
        # MCR
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        # RPS
        self._rate_limiter = AsyncLimiter(requests_per_second, 1.0)

    async def _make_request(self, endpoint: str, method: str = "GET", params: dict[str, Any] | None = None) -> Any:
        """Метод для выполнения запросов к GitHub API с учетом ограничений MCR и RPS"""
        async with self._semaphore: 
            async with self._rate_limiter: 
                try:
                    async with self._session.request(method, f"{GITHUB_API_BASE_URL}/{endpoint}", params=params) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            self._logger.error(f"HTTP {response.status} error for {endpoint}")
                            return []
                except (ClientConnectorError, ClientError) as e:
                    self._logger.error(f"Connection error for {endpoint}: {e}")
                    return []
                except Exception as e:
                    self._logger.error(f"Unexpected error for {endpoint}: {e}")
                    return []

    async def _get_top_repositories(self, limit: int = 100) -> list[dict[str, Any]]:
        """GitHub REST API: https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28#search-repositories"""
        data = await self._make_request(
            endpoint="search/repositories",
            params={"q": "stars:>1", "sort": "stars", "order": "desc", "per_page": limit},
        )
        return data.get("items", []) if isinstance(data, dict) else []

    async def _get_repository_commits(self, owner: str, repo: str) -> list[dict[str, Any]]:
        """GitHub REST API: https://docs.github.com/en/rest/commits/commits?apiVersion=2022-11-28#list-commits"""
        since_date = (datetime.now() - timedelta(days=1)).isoformat()
        data = await self._make_request(
            endpoint=f"repos/{owner}/{repo}/commits",
            params={"since": since_date},
        )
        return data if isinstance(data, list) else []

    def _count_authors_commits_today(self, commits: list[dict[str, Any]]) -> list[RepositoryAuthorCommitsNum]:
        """Подсчитываем кол-во коммитов по авторам"""
        author_commits_count = Counter()
        
        for commit in commits:
            # Проверяем наличие автора в коммите
            if commit.get("author") and commit["author"].get("login"):
                author_commits_count[commit["author"]["login"]] += 1
        
        result = [RepositoryAuthorCommitsNum(author=author, commits_num=cnt) 
            for author, cnt in author_commits_count.items()]
        return result

    async def _process_repository(self, repository: dict[str, Any], position: int) -> Repository:
        """Обрабатываем один репозиторий асинхронно"""
        commits = await self._get_repository_commits(
            owner=repository.get("owner", {}).get("login", ""),
            repo=repository.get("name", "")
        )
        
        authors_commits_num_today = self._count_authors_commits_today(commits)
        
        return Repository(
            name=repository.get("name", ""),
            owner=repository.get("owner", {}).get("login", ""),
            position=position,
            stars=repository.get("stargazers_count", 0),
            watchers=repository.get("watchers_count", 0),
            forks=repository.get("forks_count", 0),
            language=repository.get("language", ""),
            authors_commits_num_today=authors_commits_num_today
        )

    async def get_repositories(self) -> list[Repository]:
        """Получаем список репозиториев и подсчитываем количество коммитов по авторам за последний день"""
        try:
            self._logger.info("Starting get_repositories...")
            repositories = await self._get_top_repositories()
            self._logger.debug(f"Successfully fetched {len(repositories)} repositories!")
            
            tasks = [
                self._process_repository(repo, i + 1) 
                for i, repo in enumerate(repositories)
            ]
            
            result_repositories_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            valid_repositories = []
            for i, result in enumerate(result_repositories_list):
                if isinstance(result, Exception):
                    self._logger.error(f"Error processing repository {i+1}: {result}")
                else:
                    valid_repositories.append(result)
            
            self._logger.info(f"get_repositories completed! Processed {len(valid_repositories)} repositories.")
            return valid_repositories
            
        except Exception as e:
            self._logger.error(f"Error getting repositories: {e}")
            return []
    

    async def close(self):
        await self._session.close()
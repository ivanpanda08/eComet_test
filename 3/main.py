import asyncio
import logging
from scraper import GithubReposScrapper
from config import get_config


async def main():
    config = await get_config()
    logging.basicConfig(level=config.log_level)
    scrapper = GithubReposScrapper(
        access_token=config.github_api_token,
        max_concurrent_requests=config.max_concurrent_requests,
        requests_per_second=config.requests_per_second
    )
    try:
        repositories = await scrapper.get_repositories()
    finally:
        await scrapper.close()


if __name__ == "__main__":
    asyncio.run(main())

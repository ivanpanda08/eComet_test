import asyncio
import logging
from scraper import GithubReposScrapper
from config import get_config
from database import ClickHouseRepository


async def main():
    config = await get_config()
    logging.basicConfig(level=config.log_level)
    logger = logging.getLogger(__name__)
    
    batch_size = 20 # показательный малый размер батча 
    
    scrapper = GithubReposScrapper(
        access_token=config.github_api_token,
        max_concurrent_requests=config.max_concurrent_requests,
        requests_per_second=config.requests_per_second
    )
    
    db = ClickHouseRepository(config=config, batch_size=batch_size)
    
    try:
        await db.connect()
        
        total_saved = 0
        
        async for batch in scrapper.get_repositories_batched(batch_size=batch_size):
            await db.save_repositories(batch)
            total_saved += len(batch)
        
        logger.debug(f"Обработка завершена! Всего сохранено {total_saved} репозиториев")
    finally:
        await scrapper.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())

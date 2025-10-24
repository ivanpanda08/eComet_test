import logging
from datetime import date, datetime
from typing import Iterator

from aiochclient import ChClient
from aiohttp import ClientSession

from config import Config
from models import Repository


class ClickHouseRepository:
    """Класс для работы с ClickHouse используя aiochclient."""

    def __init__(self, config: Config, batch_size: int = 20):
        self._config = config
        self._batch_size = batch_size
        self._logger = logging.getLogger(__name__)
        self._client: ChClient | None = None
        self._session: ClientSession | None = None

    async def connect(self) -> None:
        """Инициализация подключения к ClickHouse."""
        self._session = ClientSession()
        self._client = ChClient(
            self._session,
            url=f"http://{self._config.clickhouse_host}:{self._config.clickhouse_port}",
            user=self._config.clickhouse_user,
            password=self._config.clickhouse_password,
            database=self._config.clickhouse_db,
        )
        self._logger.info("Соединение с ClickHouse установлено")

    async def close(self) -> None:
        """Закрытие подключения к ClickHouse."""
        if self._session:
            await self._session.close()
            self._logger.info("ClickHouse соединение закрыто")

    def _batch_data(self, data: list, batch_size: int) -> Iterator[list]:
        for i in range(0, len(data), batch_size):
            yield data[i:i + batch_size]

    async def save_repositories(self, repositories: list[Repository]) -> None:
        """Сохранение данных в ClickHouse"""
        if not repositories:
            self._logger.warning("Не найдено репозиториев для сохранения")
            return

        current_date = date.today().strftime("%Y-%m-%d")
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        repositories_data = [
            (
                repo.name,
                repo.owner,
                repo.stars,
                repo.watchers,
                repo.forks,
                repo.language or "",
                current_datetime,
            )
            for repo in repositories
        ]
        
        positions_data = [
            (
                current_date,
                repo.name,
                repo.position,
            )
            for repo in repositories
        ]
        
        commits_data = [
            (
                current_date,
                repo.name,
                author_commit.author,
                author_commit.commits_num,
            )
            for repo in repositories
            for author_commit in repo.authors_commits_num_today
        ]
        
        await self._insert_batch(
            table="repositories",
            data=repositories_data,
            batch_size=self._batch_size,
        )
        
        await self._insert_batch(
            table="repositories_positions",
            data=positions_data,
            batch_size=self._batch_size,
        )
        
        await self._insert_batch(
            table="repositories_authors_commits",
            data=commits_data,
            batch_size=self._batch_size,
        )

    async def _insert_batch(
        self, table: str, data: list[dict], batch_size: int
    ) -> None:
        """Вставка данных батчами в указанную таблицу."""
        if not data:
            return
        
        full_table_name = f"{self._config.clickhouse_db}.{table}"
        total_inserted = 0
        
        for batch in self._batch_data(data, batch_size):
            await self._client.execute(
                f"INSERT INTO {full_table_name} VALUES",
                *batch,
            )
            total_inserted += len(batch)
            self._logger.debug(
                f"Вставлено {len(batch)} записей в таблицу {table} "
                f"(всего: {total_inserted}/{len(data)})"
            )


from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator

import logging
import asyncpg
import uvicorn
from fastapi import APIRouter, FastAPI, Depends, Request, HTTPException
from config.config import get_app_config, get_db_config


async def get_pg_connection(request: Request) -> AsyncIterator[asyncpg.Connection]:
    """Зависимость для получения подключения к PostgreSQL из пула"""
    if not hasattr(request.app.state, 'pool') or not request.app.state.pool:
        raise HTTPException(
            status_code=503,
            detail="Database connection pool not available"
        )
    if not hasattr(request.app.state, 'logger') or not request.app.state.logger:
        raise HTTPException(
            status_code=500,
            detail="Something gone wrong! Check the logs!"
        )

    pool: asyncpg.Pool = request.app.state.pool
    logger: logging.Logger = request.app.state.logger
    try:
        async with pool.acquire() as connection:
            yield connection
    except asyncpg.PostgresError as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to acquire database connection: {e}"
        )


async def get_db_version(conn: Annotated[asyncpg.Connection, Depends(get_pg_connection)]):
    return await conn.fetchval("SELECT version()")


def register_routes(app: FastAPI):
    router = APIRouter(prefix="/api")
    router.add_api_route(path="/db_version",
                         endpoint=get_db_version,
                         methods=["GET"],
                         )
    app.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Менеджер жизненного цикла приложения"""
    app_config = get_app_config()
    logging.basicConfig(level=app_config.log_level)
    logger = logging.getLogger(__name__)

    db_config = get_db_config()

    try:
        app.state.logger = logger
        logger.debug(f"Connecting to database at {db_config.dsn_safe}")
        # Создаем пул подключений при запуске
        app.state.pool = await asyncpg.create_pool(
            dsn=db_config._dsn,
            min_size=db_config.pool_min_size,
            max_size=db_config.pool_max_size,
            max_inactive_connection_lifetime=db_config.command_timeout,
        )
        yield
    except Exception as e:
        err_msg = (f"Failed to create database connection pool: {e}")
        logger.error(msg=err_msg)
        raise
    finally:
        if hasattr(app.state, 'pool') and app.state.pool:
            await app.state.pool.close()


def create_app() -> FastAPI:
    app_config = get_app_config()
    app = FastAPI(
        title="e-Comet",
        host=app_config.app_host,
        port=app_config.app_port,
        debug=app_config.debug,
        version=app_config.app_version,
        lifespan=lifespan,
        reload=False,
    )

    register_routes(app)
    return app


if __name__ == "__main__":
    uvicorn.run("main:create_app", factory=True)

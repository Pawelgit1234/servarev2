import pytest_asyncio
from common.base import Base
from common.databases import engine
from common.models.assets import *  # noqa: F403
from common.models.player import *  # noqa: F403
from common.models.server import *  # noqa: F403
from common.settings import DATABASE_URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest_asyncio.fixture(scope="session", autouse=True)
async def migrate_db():  # type: ignore
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db():  # type: ignore
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(
        engine, expire_on_commit=False, autoflush=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()

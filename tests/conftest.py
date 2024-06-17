import asyncio
import os
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from models.base import Base

os.environ["DB_NAME"] = 'stsoft_test'

from src.models.db_helper import DataBaseHelper
from core.config import setting
from src.main import app


# Реквизиты подключения только для тестов
# TODO Перенести в env
DATABASE_URL_TEST = f"postgresql+asyncpg://postgres:1234@{os.getenv('DB_HOST','localhost')}:5432/{os.getenv('DB_NAME', 'stsoft')}"

engine_database_helper_test = DataBaseHelper(url=DATABASE_URL_TEST, echo=True)
engine_test = engine_database_helper_test.engine


@pytest.fixture(autouse=True, scope="session")
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# SETUP
@pytest.fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


client = TestClient(app)


@pytest.fixture(scope="session")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

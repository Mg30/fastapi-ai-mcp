from unittest.mock import create_autospec

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel
from src.chat.models import *
from src.llm.streaming import OpenAIStreaming
from src.resources.settings import Settings
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="function")
def postgres_container():
    """Start a Postgres container for testing."""
    container = PostgresContainer("postgres:17.2-bullseye", driver="psycopg")
    container.start()
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture(scope="function")
def test_client(postgres_container: PostgresContainer):
    """Create test settings with the test database URL."""
    settings = Settings(
        POSTGRES_USER=postgres_container.username,
        POSTGRES_PASSWORD=postgres_container.password,
        POSTGRES_DB=postgres_container.dbname,
        POSTGRES_HOST=postgres_container.get_container_host_ip(),
        POSTGRES_PORT=postgres_container.get_exposed_port(5432),
        OPENAI_API_KEY="test-key",
    )
    from src.api.main import app

    llm_service_mock = create_autospec(OpenAIStreaming)

    async def _generator(*args, **kwargs):
        chunks = ["hello", "world"]
        for chunk in chunks:
            yield chunk

    llm_service_mock.stream.side_effect = _generator

    app.container.shutdown_resources()
    app.container.settings.override(settings.model_dump())
    app.container.llm_streaming.override(llm_service_mock)
    app.container.init_resources()

    engine = app.container.engine()

    SQLModel.metadata.create_all(bind=engine)

    yield TestClient(app)

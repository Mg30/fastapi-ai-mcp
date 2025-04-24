from contextlib import contextmanager
from typing import Generator
from urllib.parse import quote

import sqlmodel
from sqlalchemy import Engine, create_engine

from .settings import Settings


def pg_engine(settings: dict) -> Generator[Engine, None, None]:
    password_quoted = quote(settings.get("POSTGRES_PASSWORD"))

    engine = create_engine(
        url=f"postgresql+psycopg://{settings.get('POSTGRES_USER')}:{password_quoted}@{settings.get('POSTGRES_HOST')}:{settings.get('POSTGRES_PORT')}/{settings.get('POSTGRES_DB')}",
        pool_size=10,
        max_overflow=5,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )
    try:
        yield engine
    finally:
        engine.dispose()


def session_factory(engine: Engine):
    @contextmanager
    def _factory() -> Generator[sqlmodel.Session, None, None]:
        session = sqlmodel.Session(engine)
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return _factory

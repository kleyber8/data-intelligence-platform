"""Helper de conexión a PostgreSQL."""
from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine

from src.config import settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Devuelve un Engine de SQLAlchemy cacheado para toda la aplicación."""
    return create_engine(
        settings.postgres_dsn,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        future=True,
    )

"""Helper de conexión a PostgreSQL.

Compatible con SQLAlchemy 1.4 (Airflow 2.10.2) y 2.0 (venv local).
"""
from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

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

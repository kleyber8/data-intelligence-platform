"""
Escritor de la Capa Bronze.

Lee el archivo Parquet desde Landing (data/raw/...), añade columnas
de auditoría (ingestion_run_id, ingestion_row_id, created_at,
quality_status) y lo persiste en bronze.bronze_ais_position.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import polars as pl
from sqlalchemy import text

from src.storage.db import get_engine

logger = logging.getLogger("storage.bronze_writer")

BRONZE_TABLE = "bronze.bronze_ais_position"

# Columnas destino en Bronze (sin contar SERIAL/BIGSERIAL y DEFAULT)
BRONZE_COLUMNS = [
    "ingestion_row_id",
    "mmsi", "latitude", "longitude",
    "speed_over_ground", "course_over_ground", "heading",
    "position_ts", "vessel_name", "vessel_type", "nav_status",
    "ingestion_run_id", "source_file",
]


def _resolve_local_path(ingestion_run_id: str) -> Path:
    """Busca el Parquet de una corrida en el Data Lake local."""
    from src.config import settings

    base = settings.data_lake_raw_dir / "maritime"
    matches = list(base.rglob(f"ais_positions_{ingestion_run_id}.parquet"))
    if not matches:
        raise FileNotFoundError(
            f"No se encontró el Parquet para run_id={ingestion_run_id} en {base}"
        )
    return matches[0]


def write_bronze_from_landing(ingestion_run_id: str) -> int:
    """
    Carga el Parquet de Landing en bronze.bronze_ais_position.

    Returns:
        Número de filas insertadas.
    """
    local_path = _resolve_local_path(ingestion_run_id)
    logger.info("Leyendo Parquet desde %s", local_path)
    df = pl.read_parquet(local_path)

    if df.height == 0:
        logger.warning("El archivo %s no contiene filas", local_path)
        return 0

    # ---------- Añadir columnas de auditoría ----------
    now = datetime.now(timezone.utc)
    row_ids = [str(uuid.uuid4()) for _ in range(df.height)]

    df = df.with_columns([
        pl.Series("ingestion_row_id", row_ids, dtype=pl.Utf8),
        pl.lit(ingestion_run_id, dtype=pl.Utf8).alias("ingestion_run_id"),
        pl.lit(str(local_path), dtype=pl.Utf8).alias("source_file"),
    ])

    # Orden final de columnas para que coincida con la tabla
    df = df.select(BRONZE_COLUMNS)

    # ---------- Insertar en PostgreSQL ----------
    logger.info("Insertando %d filas en %s", df.height, BRONZE_TABLE)
    df.write_database(
        table_name=BRONZE_TABLE,
        connection=get_engine(),
        if_table_exists="append",
    )

    # ---------- Actualizar metadata.ingestion_runs a estado 'bronze_loaded' ----------
    with get_engine().begin() as conn:
        conn.execute(
            text("""
                UPDATE metadata.ingestion_runs
                SET status = 'bronze_loaded'
                WHERE ingestion_run_id = :run_id
                  AND status IN ('landed', 'pending')
            """),
            {"run_id": ingestion_run_id},
        )

    logger.info("Bronze cargado: %d filas para run_id=%s", df.height, ingestion_run_id)
    return df.height


def count_bronze_rows(ingestion_run_id: str) -> int:
    """Cuenta las filas de una corrida en Bronze (útil para verificar)."""
    with get_engine().begin() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM bronze.bronze_ais_position WHERE ingestion_run_id = :rid"),
            {"rid": ingestion_run_id},
        )
    return int(result.scalar_one())

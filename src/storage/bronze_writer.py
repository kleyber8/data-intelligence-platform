import logging
import uuid
import io
from pathlib import Path
from datetime import datetime, timezone

import polars as pl
import psycopg2
from psycopg2 import sql

from src.config import settings

logger = logging.getLogger(__name__)
BRONZE_TABLE = "bronze.bronze_ais_position"

def _resolve_local_path(ingestion_run_id: str) -> Path:
    base_dir = Path(settings.data_lake_raw_dir) / "maritime"
    matches = list(base_dir.rglob(f"*{ingestion_run_id}*.parquet"))
    if not matches:
        raise FileNotFoundError(f"No se encontró el Parquet para run_id={ingestion_run_id}")
    return max(matches, key=lambda p: p.stat().st_mtime)

def write_bronze_from_landing(ingestion_run_id: str) -> int:
    local_path = _resolve_local_path(ingestion_run_id)
    logger.info(f"Leyendo archivo: {local_path}")

    conn = psycopg2.connect(
        dbname=settings.postgres_db, user=settings.postgres_user,
        password=settings.postgres_password, host=settings.postgres_host, port=settings.postgres_port
    )
    cursor = conn.cursor()

    cursor.execute("SET LOCAL synchronous_commit = OFF;")
    cursor.execute("SET LOCAL maintenance_work_mem = '512MB';")
    
    expected_cols = [
        "ingestion_row_id", "mmsi", "latitude", "longitude", 
        "speed_over_ground", "course_over_ground", "heading", 
        "position_ts", "vessel_name", "vessel_type", "nav_status", 
        "ingestion_run_id", "source_file", "created_at", "quality_status"
    ]
    
    total_inserted = 0
    chunk_size = 250_000

    try:
        for df_chunk in pl.read_parquet(local_path).iter_slices(n_rows=chunk_size):
            df_chunk = df_chunk.with_columns([
                pl.Series("ingestion_row_id", [str(uuid.uuid4()) for _ in range(len(df_chunk))]),
                pl.lit(ingestion_run_id).alias("ingestion_run_id"),
                pl.lit(str(local_path)).alias("source_file"),
                pl.lit(datetime.now(timezone.utc)).alias("created_at"),
                pl.lit("pending").alias("quality_status")
            ])

            for col in expected_cols:
                if col not in df_chunk.columns:
                    df_chunk = df_chunk.with_columns(pl.lit(None).alias(col))
            
            # ¡AQUÍ ESTÁ LA CORRECCIÓN! Forzamos los tipos antes del COPY
            df_chunk = df_chunk.select([
                pl.col("ingestion_row_id").cast(pl.Utf8),
                pl.col("mmsi").cast(pl.Utf8),
                pl.col("latitude").cast(pl.Float64),
                pl.col("longitude").cast(pl.Float64),
                pl.col("speed_over_ground").cast(pl.Float64),
                pl.col("course_over_ground").cast(pl.Float64),
                pl.col("heading").cast(pl.Int32, strict=False), # Convierte 511.0 a 511. Si falla, pone null
                pl.col("position_ts").cast(pl.Datetime),
                pl.col("vessel_name").cast(pl.Utf8),
                pl.col("vessel_type").cast(pl.Utf8),
                pl.col("nav_status").cast(pl.Utf8),
                pl.col("ingestion_run_id").cast(pl.Utf8),
                pl.col("source_file").cast(pl.Utf8),
                pl.col("created_at").cast(pl.Datetime),
                pl.col("quality_status").cast(pl.Utf8)
            ])

            csv_buffer = io.StringIO()
            df_chunk.write_csv(csv_buffer)
            csv_buffer.seek(0)

            cols_str = ", ".join(expected_cols)
            copy_sql = sql.SQL("COPY {} ({}) FROM STDIN WITH CSV HEADER").format(
                sql.Identifier(*BRONZE_TABLE.split('.')),
                sql.SQL(cols_str)
            )
            
            cursor.copy_expert(copy_sql, csv_buffer)
            total_inserted += len(df_chunk)
            logger.info(f"Lote insertado: {len(df_chunk)} filas. Total: {total_inserted}")

        conn.commit()
        logger.info(f"✅ Carga finalizada. Total insertado: {total_inserted} filas.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error en la carga: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

    return total_inserted

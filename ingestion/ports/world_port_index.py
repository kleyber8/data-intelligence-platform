"""Ingesta del World Port Index desde el espejo de Hugging Face -> Bronze."""
import hashlib
import io
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
import polars as pl
import psycopg2
from psycopg2 import sql
from src.config import settings

logger = logging.getLogger("ingestion.ports")
PORTS_CSV_URL = "https://huggingface.co/datasets/programmer47/world-seaports-and-airports/resolve/main/ports.csv"
SOURCE_SYSTEM = "ports"
BRONZE_SCHEMA, BRONZE_TABLE = "bronze", "bronze_ports"

COLUMN_ALIASES = {
    "port_index": ("port_index", "index_no", "index", "porto_index", "id"),
    "region_name": ("region_name", "region_no", "region"),
    "port_name": ("port_name", "name", "port"),
    "country": ("country", "country_code", "country_iso3"),
    "latitude": ("latitude", "lat", "lattitude"),
    "longitude": ("longitude", "lon", "lng", "long"),
    "harbor_size": ("harbor_size", "harborsize", "size"),
    "harbor_type": ("harbor_type", "harbortype", "type", "port_type"),
}
REQUIRED = ("port_index", "port_name", "latitude", "longitude")
COPY_COLUMNS = ("port_index", "region_name", "port_name", "country", "latitude", "longitude", "harbor_size", "harbor_type", "ingested_at")

SQL_MARK_PROCESSED = """
    SELECT ingestion_run_id, rows_ingested FROM metadata.ingestion_runs
    WHERE source_system = %s AND status = 'completed' AND rows_ingested > 0
      AND ( source_url = %s OR checksum_sha256 = %s ) LIMIT 1
"""
INSERT_RUN = """
    INSERT INTO metadata.ingestion_runs
    (ingestion_run_id, source_system, source_url, source_file, download_timestamp, file_size_bytes, checksum_sha256, rows_ingested, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

def _ddl_statements() -> tuple[sql.SQL, ...]:
    return (
        sql.SQL("CREATE SCHEMA IF NOT EXISTS {};").format(sql.Identifier(BRONZE_SCHEMA)),
        sql.SQL("CREATE TABLE IF NOT EXISTS {}.{} (port_index VARCHAR(50), region_name VARCHAR(100), port_name VARCHAR(255), country VARCHAR(10), latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, harbor_size VARCHAR(50), harbor_type VARCHAR(50), ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW());").format(sql.Identifier(BRONZE_SCHEMA), sql.Identifier(BRONZE_TABLE)),
        sql.SQL("CREATE UNIQUE INDEX IF NOT EXISTS idx_bronze_ports_port_index ON {}.{} (port_index);").format(sql.Identifier(BRONZE_SCHEMA), sql.Identifier(BRONZE_TABLE)),
    )

def compute_sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()

def _download_csv(url: str) -> Path:
    local = Path("/tmp") / f"ports_{uuid.uuid4()}.csv"
    with httpx.stream("GET", url, timeout=120.0, follow_redirects=True) as resp:
        resp.raise_for_status()
        with open(local, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=1024 * 256):
                f.write(chunk)
    return local

def _load_and_clean(csv_path: Path) -> pl.DataFrame:
    raw = pl.read_csv(csv_path, infer_schema_length=0, truncate_ragged_lines=True)
    headers = {c.lower(): c for c in raw.columns}
    resolved = {target: next((headers[a] for a in aliases if a in headers), None) for target, aliases in COLUMN_ALIASES.items()}
    
    missing = [t for t in REQUIRED if resolved[t] is None]
    if missing:
        raise ValueError(f"El CSV no tiene columnas requeridas {missing}.")

    def opt_col(target: str, default: str) -> pl.Expr:
        col = resolved.get(target)
        if col:
            return pl.col(col).cast(pl.Utf8).str.strip_chars(None).fill_null(default).alias(target)
        return pl.lit(default).alias(target)

    select_exprs = [
        pl.col(resolved["port_index"]).cast(pl.Utf8).str.strip_chars(None).fill_null("").alias("port_index"),
        opt_col("region_name", ""),
        opt_col("port_name", "UNKNOWN"),
        opt_col("country", "UNK"),
        pl.col(resolved["latitude"]).cast(pl.Float64, strict=False).alias("latitude"),
        pl.col(resolved["longitude"]).cast(pl.Float64, strict=False).alias("longitude"),
        opt_col("harbor_size", "Unknown"),
        opt_col("harbor_type", "Unknown"),
    ]

    return raw.select(select_exprs).filter(
        pl.col("latitude").is_not_null() & pl.col("longitude").is_not_null()
        & pl.col("latitude").is_between(-90.0, 90.0) & pl.col("longitude").is_between(-180.0, 180.0)
        & (pl.col("port_index") != "")
    ).unique(subset=["port_index"], keep="first")

def run() -> dict:
    run_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    logger.info("Iniciando ingesta del World Port Index (mirror Hugging Face)...")

    conn = psycopg2.connect(dbname=settings.postgres_db, user=settings.postgres_user, password=settings.postgres_password, host=settings.postgres_host, port=settings.postgres_port)
    cursor = conn.cursor()
    try:
        cursor.execute(SQL_MARK_PROCESSED, (SOURCE_SYSTEM, PORTS_CSV_URL, "--unused--"))
        prev = cursor.fetchone()
        if prev:
            logger.info("SKIP: los puertos ya fueron cargados en run=%s", prev[0])
            return {"ingestion_run_id": str(prev[0]), "status": "already_processed", "rows_loaded": int(prev[1])}

        local_csv = _download_csv(PORTS_CSV_URL)
        try:
            checksum = compute_sha256(local_csv)
            cursor.execute(SQL_MARK_PROCESSED, (SOURCE_SYSTEM, "--unused--", checksum))
            prev = cursor.fetchone()
            if prev:
                logger.info("SKIP: checksum ya procesado en run=%s", prev[0])
                return {"ingestion_run_id": str(prev[0]), "status": "already_processed", "rows_loaded": int(prev[1])}

            df = _load_and_clean(local_csv)
            if df.height == 0:
                raise RuntimeError("El CSV no contiene registros válidos.")
            df = df.with_columns(pl.lit(start_time).alias("ingested_at"))
            logger.info("Puertos válidos a cargar: %d", df.height)

            cursor.execute("SET LOCAL synchronous_commit = OFF;")
            cursor.execute("SET LOCAL maintenance_work_mem = '256MB';")
            for ddl in _ddl_statements():
                cursor.execute(ddl)

            cursor.execute(sql.SQL("TRUNCATE TABLE {}.{};").format(sql.Identifier(BRONZE_SCHEMA), sql.Identifier(BRONZE_TABLE)))

            buffer = io.StringIO()
            df.select(COPY_COLUMNS).write_csv(buffer, include_header=False)
            buffer.seek(0)

            copy_sql = sql.SQL("COPY {}.{} ({}) FROM STDIN WITH (FORMAT csv)").format(
                sql.Identifier(BRONZE_SCHEMA), sql.Identifier(BRONZE_TABLE),
                sql.SQL(", ").join(sql.Identifier(c) for c in COPY_COLUMNS),
            )
            cursor.copy_expert(copy_sql, buffer)

            cursor.execute(INSERT_RUN, (run_id, SOURCE_SYSTEM, PORTS_CSV_URL, local_csv.name, start_time, local_csv.stat().st_size, checksum, df.height, "completed"))
            conn.commit()
            logger.info("✅ Carga en bronze.bronze_ports completada: %d puertos.", df.height)
            return {"ingestion_run_id": run_id, "status": "completed", "rows_loaded": int(df.height)}
        finally:
            local_csv.unlink(missing_ok=True)
    except Exception as exc:
        conn.rollback()
        logger.error("Error en la ingesta de puertos: %s", exc)
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run()

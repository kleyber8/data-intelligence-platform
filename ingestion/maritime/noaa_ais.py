"""Ingesta NOAA AIS -> Data Lake (Parquet en MinIO) con IDEMPOTENCIA por checksum."""
import hashlib
import logging
import uuid
import zipfile
from pathlib import Path
from datetime import datetime, timezone

import httpx
import polars as pl
from sqlalchemy import text

from src.config import settings
from src.storage.db import get_engine
from src.storage.s3_lake import upload_file

logger = logging.getLogger(__name__)
RAW_DIR = Path(settings.data_lake_raw_dir) / "maritime"
DEFAULT_URL = "https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2023/AIS_2023_01_01.zip"

SQL_SELECT_PROCESSED = text("""
    SELECT ingestion_run_id, source_url, checksum_sha256, download_timestamp, rows_ingested
    FROM metadata.ingestion_runs
    WHERE status IN ('completed', 'validated')
      AND rows_ingested > 0
      AND ( source_system = :source_system
            AND ( source_url = :source_url OR checksum_sha256 = :checksum_sha256 ) )
    LIMIT 1
""")

def compute_sha256(path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def _select_processed_run(source_url: str | None = None, checksum_sha256: str | None = None, source_system: str = "noaa") -> dict | None:
    params = {
        "source_system": source_system,
        "source_url": source_url or "--unused--",
        "checksum_sha256": checksum_sha256 or "--unused--",
    }
    try:
        with get_engine().begin() as conn:
            row = conn.execute(SQL_SELECT_PROCESSED, params).mappings().first()
    except Exception as exc:
        logger.warning("No se pudo consultar metadata.ingestion_runs: %s", exc)
        return None
    return dict(row) if row else None

def run_ingestion(source: str = "noaa", url: str | None = None) -> dict:
    run_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    if not url:
        url = DEFAULT_URL

    prev = _select_processed_run(source_url=url, source_system=source)
    if prev:
        logger.info("SKIP (pre-descarga): %s ya fue procesado como run=%s", url, prev["ingestion_run_id"])
        return {"ingestion_run_id": str(prev["ingestion_run_id"]), "local_path": None, "rows_ingested": 0, "status": "already_processed"}

    logger.info("Descargando ZIP de NOAA: %s", url)
    local_zip = Path("/tmp") / f"noaa_{run_id}.zip"
    try:
        with httpx.stream("GET", url, timeout=300.0, follow_redirects=True) as response:
            response.raise_for_status()
            with open(local_zip, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                    f.write(chunk)
    except httpx.HTTPError as exc:
        local_zip.unlink(missing_ok=True)
        raise

    checksum = compute_sha256(local_zip)
    prev = _select_processed_run(checksum_sha256=checksum, source_system=source)
    if prev:
        local_zip.unlink(missing_ok=True)
        logger.info("SKIP (post-descarga): checksum ya procesado en run=%s", prev["ingestion_run_id"])
        return {"ingestion_run_id": str(prev["ingestion_run_id"]), "local_path": None, "rows_ingested": 0, "status": "already_processed"}

    with zipfile.ZipFile(local_zip) as z:
        csv_name = z.namelist()[0]
        csv_path = Path("/tmp") / f"noaa_{run_id}.csv"
        z.extract(csv_name, path="/tmp")
        Path("/tmp", csv_name).rename(csv_path)
    local_zip.unlink(missing_ok=True)

    partition_dir = RAW_DIR / f"year={start_time.year}" / f"month={start_time.month:02d}" / f"day={start_time.day:02d}"
    partition_dir.mkdir(parents=True, exist_ok=True)
    local_parquet = partition_dir / f"ais_{run_id}.parquet"

    lf = pl.scan_csv(csv_path, try_parse_dates=True, schema_overrides={"MMSI": pl.Utf8}).select([
        pl.col("MMSI").alias("mmsi"), pl.col("BaseDateTime").alias("position_ts"),
        pl.col("LAT").alias("latitude"), pl.col("LON").alias("longitude"),
        pl.col("SOG").alias("speed_over_ground"), pl.col("COG").alias("course_over_ground"),
        pl.col("Heading").alias("heading"), pl.col("VesselName").alias("vessel_name"),
        pl.col("VesselType").alias("vessel_type"), pl.col("Status").alias("nav_status"),
    ])
    lf.sink_parquet(local_parquet, compression="zstd")
    csv_path.unlink(missing_ok=True)

    file_size = local_parquet.stat().st_size
    s3_key = f"raw/maritime/year={start_time.year}/month={start_time.month:02d}/day={start_time.day:02d}/{local_parquet.name}"
    upload_file(local_parquet, settings.s3_bucket_raw, s3_key)

    with get_engine().begin() as conn:
        conn.execute(text("""
            INSERT INTO metadata.ingestion_runs
            (ingestion_run_id, source_system, source_url, source_file, download_timestamp, file_size_bytes, checksum_sha256, rows_ingested, status)
            VALUES (:run_id, :source, :url, :local_path, :start_time, :file_size, :checksum, 0, 'landed')
        """), {"run_id": run_id, "source": source, "url": url, "local_path": str(local_parquet), "start_time": start_time, "file_size": file_size, "checksum": checksum})

    logger.info("Run %s registrado (status=landed).", run_id)
    return {"ingestion_run_id": run_id, "local_path": str(local_parquet), "rows_ingested": 0, "status": "created", "checksum_sha256": checksum}

def mark_run_completed(ingestion_run_id: str, rows_ingested: int) -> None:
    with get_engine().begin() as conn:
        conn.execute(text("UPDATE metadata.ingestion_runs SET rows_ingested = :rows, status = 'completed', error_message = NULL WHERE ingestion_run_id = :run_id AND status IN ('landed', 'completed')"), {"run_id": ingestion_run_id, "rows": int(rows_ingested)})
    logger.info("Run %s marcado como COMPLETED (%d filas).", ingestion_run_id, rows_ingested)

def mark_run_failed(ingestion_run_id: str, error_message: str) -> None:
    with get_engine().begin() as conn:
        conn.execute(text("UPDATE metadata.ingestion_runs SET status = 'failed', error_message = :error_message WHERE ingestion_run_id = :run_id AND status = 'landed'"), {"run_id": ingestion_run_id, "error_message": error_message[:1000]})

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_ingestion(source="noaa")

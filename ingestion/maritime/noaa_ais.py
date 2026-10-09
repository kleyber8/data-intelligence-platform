"""
Extractor de posiciones AIS.

Descarga (o genera sintéticamente) un dataset de posiciones AIS,
calcula su checksum SHA-256, lo persiste en el Data Lake local
particionado estilo Hive y lo sube a MinIO (bucket maritime-raw).
Registra los metadatos de la corrida en PostgreSQL.

Uso desde terminal:
    python -m ingestion.maritime.noaa_ais --source synthetic
    python -m ingestion.maritime.noaa_ais --source noaa --url <URL>
"""
from __future__ import annotations

import argparse
import hashlib
import io
import logging
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import polars as pl
from sqlalchemy import text

from src.config import settings
from src.storage.db import get_engine
from src.storage.s3_lake import upload_file

logger = logging.getLogger("ingestion.noaa_ais")


# ---------- Columnas esperadas tras normalización ----------
EXPECTED_COLUMNS = [
    "mmsi", "latitude", "longitude", "speed_over_ground",
    "course_over_ground", "heading", "position_ts",
    "vessel_name", "vessel_type", "nav_status",
]

# ---------- Mapeo desde columnas NOAA a nuestro esquema ----------
NOAA_COLUMN_MAPPING = {
    "sog": "speed_over_ground",
    "cog": "course_over_ground",
    "base_date_time": "position_ts",
    "status": "nav_status",
    "vesselname": "vessel_name",
    "vesseltype": "vessel_type",
}


# ============================================================
# Utilidades
# ============================================================
def compute_sha256(path: Path) -> str:
    """Calcula el SHA-256 de un archivo en streaming."""
    sha = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _normalize_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Renombra columnas NOAA a nuestro esquema y valida presencia."""
    lower_map = {c.lower(): c for c in df.columns}
    rename: dict[str, str] = {}
    for src, dst in NOAA_COLUMN_MAPPING.items():
        if src in lower_map:
            rename[lower_map[src]] = dst
    df = df.rename(rename)

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas obligatorias tras normalizar: {missing}")

    return df.select(EXPECTED_COLUMNS)


# ============================================================
# Generación sintética
# ============================================================
def generate_synthetic_ais_data(num_rows: int = 200, num_invalid: int = 30) -> pl.DataFrame:
    """Genera un DataFrame de posiciones AIS con casos válidos e inválidos."""
    rng = random.Random(42)
    now = datetime.now(timezone.utc)
    num_valid = max(num_rows - num_invalid, 0)
    rows: list[dict[str, Any]] = []

    for i in range(num_valid):
        rows.append({
            "mmsi": f"{rng.randint(200000000, 799999999)}",
            "latitude": rng.uniform(-60.0, 70.0),
            "longitude": rng.uniform(-170.0, 170.0),
            "speed_over_ground": round(rng.uniform(0.0, 25.0), 2),
            "course_over_ground": round(rng.uniform(0.0, 359.9), 1),
            "heading": rng.randint(0, 359),
            "position_ts": now - timedelta(minutes=rng.randint(1, 1440)),
            "vessel_name": f"VESSEL_{i:04d}",
            "vessel_type": rng.choice(["Cargo", "Tanker", "Passenger", "Fishing"]),
            "nav_status": rng.choice(["Under way", "At anchor", "Moored"]),
        })

    patterns = ["mmsi_null", "mmsi_short", "lat_out", "lon_out", "sog_neg", "sog_high", "future"]
    for i in range(num_invalid):
        pattern = patterns[i % len(patterns)]
        row: dict[str, Any] = {
            "mmsi": f"{rng.randint(200000000, 799999999)}",
            "latitude": rng.uniform(-60.0, 70.0),
            "longitude": rng.uniform(-170.0, 170.0),
            "speed_over_ground": round(rng.uniform(0.0, 25.0), 2),
            "course_over_ground": round(rng.uniform(0.0, 359.9), 1),
            "heading": rng.randint(0, 359),
            "position_ts": now - timedelta(minutes=rng.randint(1, 1440)),
            "vessel_name": f"INVALID_{i:04d}",
            "vessel_type": "Unknown",
            "nav_status": "Unknown",
        }
        if pattern == "mmsi_null":
            row["mmsi"] = None
        elif pattern == "mmsi_short":
            row["mmsi"] = "12345"
        elif pattern == "lat_out":
            row["latitude"] = 95.0
        elif pattern == "lon_out":
            row["longitude"] = 200.0
        elif pattern == "sog_neg":
            row["speed_over_ground"] = -1.5
        elif pattern == "sog_high":
            row["speed_over_ground"] = 150.0
        elif pattern == "future":
            row["position_ts"] = now + timedelta(days=1)
        rows.append(row)

    rng.shuffle(rows)

    schema = {
        "mmsi": pl.Utf8,
        "latitude": pl.Float64,
        "longitude": pl.Float64,
        "speed_over_ground": pl.Float64,
        "course_over_ground": pl.Float64,
        "heading": pl.Int32,
        "position_ts": pl.Datetime("us", "UTC"),
        "vessel_name": pl.Utf8,
        "vessel_type": pl.Utf8,
        "nav_status": pl.Utf8,
    }
    return pl.DataFrame(rows, schema=schema)


# ============================================================
# Descarga NOAA
# ============================================================
def download_noaa_ais(url: str) -> pl.DataFrame:
    """Descarga un archivo CSV o Parquet desde una URL pública."""
    logger.info("Descargando NOAA AIS desde %s", url)
    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()

    if url.lower().endswith(".parquet"):
        df = pl.read_parquet(io.BytesIO(resp.content))
    else:
        df = pl.read_csv(io.BytesIO(resp.content), try_parse_dates=True, infer_schema_length=10000)

    return _normalize_columns(df)


# ============================================================
# Registro de metadatos
# ============================================================
def record_ingestion_metadata(
    *,
    ingestion_run_id: str,
    source_system: str,
    source_url: str | None,
    source_file: str,
    download_timestamp: datetime,
    file_size_bytes: int,
    checksum_sha256: str,
    data_period_start: datetime | None,
    data_period_end: datetime | None,
    rows_ingested: int,
    status: str,
    error_message: str | None = None,
) -> None:
    """Inserta (o actualiza) el registro de la corrida en metadata.ingestion_runs."""
    sql = text("""
        INSERT INTO metadata.ingestion_runs (
            ingestion_run_id, source_system, source_url, source_file,
            download_timestamp, file_size_bytes, checksum_sha256,
            data_period_start, data_period_end, rows_ingested, status, error_message
        ) VALUES (
            :ingestion_run_id, :source_system, :source_url, :source_file,
            :download_timestamp, :file_size_bytes, :checksum_sha256,
            :data_period_start, :data_period_end, :rows_ingested, :status, :error_message
        )
        ON CONFLICT (ingestion_run_id) DO UPDATE SET
            status = EXCLUDED.status,
            rows_ingested = EXCLUDED.rows_ingested,
            error_message = EXCLUDED.error_message
    """)
    with get_engine().begin() as conn:
        conn.execute(sql, {
            "ingestion_run_id": ingestion_run_id,
            "source_system": source_system,
            "source_url": source_url,
            "source_file": source_file,
            "download_timestamp": download_timestamp,
            "file_size_bytes": file_size_bytes,
            "checksum_sha256": checksum_sha256,
            "data_period_start": data_period_start,
            "data_period_end": data_period_end,
            "rows_ingested": rows_ingested,
            "status": status,
            "error_message": error_message,
        })


# ============================================================
# Función principal invocable desde Airflow o CLI
# ============================================================
def run_ingestion(source: str = "synthetic", source_url: str | None = None) -> dict[str, Any]:
    """Ejecuta el pipeline de ingestión completo y devuelve los metadatos."""
    ingestion_run_id = str(uuid.uuid4())
    download_ts = datetime.now(timezone.utc)

    try:
        if source == "synthetic":
            df = generate_synthetic_ais_data()
            source_system = "synthetic"
            resolved_url = None
        elif source == "noaa":
            if not source_url:
                raise ValueError("source='noaa' requiere source_url explícita")
            df = download_noaa_ais(source_url)
            source_system = "NOAA_AIS"
            resolved_url = source_url
        else:
            raise ValueError(f"source desconocido: {source}")
    except Exception as exc:
        logger.exception("Fallo en la extracción")
        record_ingestion_metadata(
            ingestion_run_id=ingestion_run_id,
            source_system=source,
            source_url=source_url,
            source_file="",
            download_timestamp=download_ts,
            file_size_bytes=0,
            checksum_sha256="",
            data_period_start=None,
            data_period_end=None,
            rows_ingested=0,
            status="failed",
            error_message=str(exc),
        )
        raise

    # Particionado Hive
    year = download_ts.strftime("%Y")
    month = download_ts.strftime("%m")
    day = download_ts.strftime("%d")
    filename = f"ais_positions_{ingestion_run_id}.parquet"
    partition_dir = (
        settings.data_lake_raw_dir / "maritime"
        / f"year={year}" / f"month={month}" / f"day={day}"
    )
    partition_dir.mkdir(parents=True, exist_ok=True)
    local_path = partition_dir / filename

    df.write_parquet(local_path, compression="zstd")

    checksum = compute_sha256(local_path)
    file_size = local_path.stat().st_size

    if df.height > 0:
        data_period_start = df["position_ts"].min()
        data_period_end = df["position_ts"].max()
    else:
        data_period_start = data_period_end = None

    # Subir a MinIO
    s3_key = f"raw/maritime/year={year}/month={month}/day={day}/{filename}"
    upload_file(local_path, settings.s3_bucket_raw, s3_key)

    # Registrar metadatos
    record_ingestion_metadata(
        ingestion_run_id=ingestion_run_id,
        source_system=source_system,
        source_url=resolved_url,
        source_file=str(local_path),
        download_timestamp=download_ts,
        file_size_bytes=file_size,
        checksum_sha256=checksum,
        data_period_start=data_period_start,
        data_period_end=data_period_end,
        rows_ingested=df.height,
        status="landed",
    )

    logger.info(
        "Ingestión OK → run_id=%s, filas=%d, tamaño=%d bytes, checksum=%s…",
        ingestion_run_id, df.height, file_size, checksum[:12],
    )

    return {
        "ingestion_run_id": ingestion_run_id,
        "local_path": str(local_path),
        "s3_key": s3_key,
        "checksum_sha256": checksum,
        "file_size_bytes": file_size,
        "rows_ingested": df.height,
        "source_system": source_system,
        "download_timestamp": download_ts.isoformat(),
    }


# ============================================================
# CLI
# ============================================================
def _cli() -> int:
    parser = argparse.ArgumentParser(description="Extractor de AIS (NOAA / sintético)")
    parser.add_argument("--source", choices=["synthetic", "noaa"], default="synthetic")
    parser.add_argument("--url", type=str, default=None, help="URL directa si source=noaa")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    try:
        meta = run_ingestion(source=args.source, source_url=args.url)
        print("\n=== Resumen de ingestión ===")
        for k, v in meta.items():
            print(f"  {k}: {v}")
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(_cli())

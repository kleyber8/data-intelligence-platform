"""
Quality Gate 1 — Integridad estructural de la Capa Bronze.

Aplica cinco reglas sobre los registros de bronze.bronze_ais_position:

    1. valid_mmsi        → MMSI no nulo y con 9 dígitos exactos
    2. valid_coordinates → Lat ∈ [-90, 90] y Lon ∈ [-180, 180]
    3. valid_speed       → SOG ≥ 0 y < 100
    4. valid_timestamp   → position_ts no nulo y no futuro

Los registros que pasan quedan con quality_status='validated'.
Los que fallan quedan con quality_status='quarantined' y se replican
en quarantine.quarantine_records con motivo y regla violada.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import polars as pl
from sqlalchemy import text

from src.storage.db import get_engine

logger = logging.getLogger("validation.quality_gate_1")

BRONZE_TABLE = "bronze.bronze_ais_position"
QUARANTINE_TABLE = "quarantine.quarantine_records"

RULE_COLUMNS = [
    "rule_valid_mmsi_present",
    "rule_valid_mmsi_format",
    "rule_valid_latitude",
    "rule_valid_longitude",
    "rule_valid_speed",
    "rule_valid_timestamp",
]


# ============================================================
# Carga desde Bronze
# ============================================================
def _load_bronze(ingestion_run_id: str) -> pl.DataFrame:
    """Carga desde PostgreSQL las filas pendientes de una corrida."""
    sql = f"""
        SELECT ingestion_row_id, record_id, mmsi, latitude, longitude,
               speed_over_ground, course_over_ground, heading,
               position_ts, vessel_name, vessel_type, nav_status,
               ingestion_run_id, source_file
        FROM {BRONZE_TABLE}
        WHERE ingestion_run_id = :rid
          AND quality_status = 'pending'
    """
    with get_engine().begin() as conn:
        rows = conn.execute(text(sql), {"rid": ingestion_run_id}).mappings().all()

    if not rows:
        return pl.DataFrame()

    return pl.DataFrame([dict(r) for r in rows])


# ============================================================
# Aplicación de reglas
# ============================================================
def _apply_rules(df: pl.DataFrame) -> pl.DataFrame:
    """Añade columnas booleanas con el resultado de cada regla."""
    now = datetime.now(timezone.utc)

    return df.with_columns([
        pl.col("mmsi").is_not_null().alias("rule_valid_mmsi_present"),
        pl.col("mmsi").cast(pl.Utf8, strict=False)
            .str.contains(r"^\d{9}$")
            .fill_null(False)
            .alias("rule_valid_mmsi_format"),
        pl.col("latitude").cast(pl.Float64, strict=False)
            .is_between(-90.0, 90.0, closed="both")
            .fill_null(False)
            .alias("rule_valid_latitude"),
        pl.col("longitude").cast(pl.Float64, strict=False)
            .is_between(-180.0, 180.0, closed="both")
            .fill_null(False)
            .alias("rule_valid_longitude"),
        pl.col("speed_over_ground").cast(pl.Float64, strict=False)
            .is_between(0.0, 100.0, closed="left")
            .fill_null(False)
            .alias("rule_valid_speed"),
        (
            pl.col("position_ts").is_not_null()
            & (pl.col("position_ts").dt.replace_time_zone("UTC") <= pl.lit(now))
        ).alias("rule_valid_timestamp"),
    ])


def _classify(df: pl.DataFrame) -> pl.DataFrame:
    """Añade la columna 'is_valid' (todas las reglas deben pasar)."""
    return df.with_columns(
        pl.all_horizontal([pl.col(c) for c in RULE_COLUMNS]).alias("is_valid")
    )


def _failed_rules_expr() -> pl.Expr:
    """Construye una lista de reglas falladas por fila."""
    # Concatenamos los nombres de las reglas que fallaron
    return pl.concat_str(
        [
            pl.when(~pl.col(c)).then(pl.lit(c.replace("rule_", "") + ";")).otherwise(pl.lit(""))
            for c in RULE_COLUMNS
        ],
        separator="",
    ).alias("failed_rules")


# ============================================================
# Persistencia de la clasificación
# ============================================================
def _mark_validated(ingestion_run_id: str) -> int:
    sql = text(f"""
        UPDATE {BRONZE_TABLE}
        SET quality_status = 'validated',
            quality_checked_at = NOW()
        WHERE ingestion_run_id = :rid
          AND quality_status = 'pending'
          AND mmsi IS NOT NULL
          AND LENGTH(mmsi) = 9
          AND mmsi ~ '^[0-9]+$'
          AND latitude BETWEEN -90 AND 90
          AND longitude BETWEEN -180 AND 180
          AND speed_over_ground >= 0 AND speed_over_ground < 100
          AND position_ts IS NOT NULL
          AND position_ts <= NOW()
    """)
    with get_engine().begin() as conn:
        res = conn.execute(sql, {"rid": ingestion_run_id})
        return res.rowcount or 0


def _mark_quarantined_in_bronze(ingestion_run_id: str) -> int:
    sql = text(f"""
        UPDATE {BRONZE_TABLE}
        SET quality_status = 'quarantined',
            quality_checked_at = NOW()
        WHERE ingestion_run_id = :rid
          AND quality_status = 'pending'
    """)
    with get_engine().begin() as conn:
        res = conn.execute(sql, {"rid": ingestion_run_id})
        return res.rowcount or 0


def _insert_quarantine(ingestion_run_id: str, invalid_df: pl.DataFrame) -> int:
    """Inserta los registros inválidos en quarantine.quarantine_records."""
    if invalid_df.height == 0:
        return 0

    sql = text(f"""
        INSERT INTO {QUARANTINE_TABLE} (
            source_record_id, failure_reason, quality_rule,
            ingestion_run_id, source_table, original_payload
        ) VALUES (
            :source_record_id, :failure_reason, :quality_rule,
            :ingestion_run_id, :source_table, CAST(:original_payload AS JSONB)
        )
    """)

    inserted = 0
    with get_engine().begin() as conn:
        for row in invalid_df.iter_rows(named=True):
            failed = [c.replace("rule_", "") for c in RULE_COLUMNS if not row[c]]
            failure_reason = "Reglas violadas: " + ", ".join(failed)
            payload = {
                "mmsi": row["mmsi"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "speed_over_ground": row["speed_over_ground"],
                "course_over_ground": row["course_over_ground"],
                "heading": row["heading"],
                "position_ts": row["position_ts"].isoformat() if row["position_ts"] else None,
                "vessel_name": row["vessel_name"],
                "vessel_type": row["vessel_type"],
                "nav_status": row["nav_status"],
            }
            conn.execute(sql, {
                "source_record_id": str(row["ingestion_row_id"]),
                "failure_reason": failure_reason,
                "quality_rule": ";".join(failed),
                "ingestion_run_id": ingestion_run_id,
                "source_table": BRONZE_TABLE,
                "original_payload": json.dumps(payload),
            })
            inserted += 1

    return inserted


# ============================================================
# Función principal
# ============================================================
def run_quality_gate_1(ingestion_run_id: str) -> dict[str, Any]:
    """
    Ejecuta el Quality Gate 1 sobre una corrida concreta.

    Returns:
        Diccionario con conteos: total, valid, invalid.
    """
    logger.info("Quality Gate 1 → run_id=%s", ingestion_run_id)
    df = _load_bronze(ingestion_run_id)

    if df.height == 0:
        logger.info("Sin filas pendientes para run_id=%s", ingestion_run_id)
        return {"ingestion_run_id": ingestion_run_id, "total": 0, "valid": 0, "invalid": 0}

    evaluated = _classify(_apply_rules(df))
    total = evaluated.height

    # Marcar todas como validadas primero (optimización: una sola pasada SQL)
    validated_n = _mark_validated(ingestion_run_id)

    # Las que quedan 'pending' se convierten en cuarentena
    quarantined_n = _mark_quarantined_in_bronze(ingestion_run_id)

    # Insertar payloads en cuarentena
    invalid_rows = evaluated.filter(~pl.col("is_valid"))
    inserted = _insert_quarantine(ingestion_run_id, invalid_rows)

    logger.info(
        "QG1 → total=%d, valid=%d, invalid=%d (insertados en cuarentena=%d)",
        total, validated_n, quarantined_n, inserted,
    )

    return {
        "ingestion_run_id": ingestion_run_id,
        "total": total,
        "valid": validated_n,
        "invalid": quarantined_n,
    }

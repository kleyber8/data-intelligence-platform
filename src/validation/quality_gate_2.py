"""
Quality Gate 2 — Integridad referencial y analítica de la capa Silver.

Valida tres reglas sobre las tablas Silver:

    1. referential_consistency: todo ingestion_row_id en int_vessel_tracks
       existe en stg_ais_position (integridad entre capas Silver).
    2. temporal_continuity: no hay duplicados (mmsi, position_ts) ni time_deltas
       negativos.
    3. spatial_continuity: ninguna velocidad calculada excede 60 nudos
       (límite físico razonable para embarcaciones comerciales).

Si falla alguna regla, se registra la incidencia en logs y se devuelve un
diccionario con los conteos.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text

from src.storage.db import get_engine

logger = logging.getLogger("validation.quality_gate_2")


def _check_referential_consistency() -> dict[str, Any]:
    sql = text("""
        SELECT COUNT(*) AS huérfanos
        FROM silver.int_vessel_tracks t
        WHERE NOT EXISTS (
            SELECT 1 FROM silver.stg_ais_position s
            WHERE s.ingestion_row_id = t.ingestion_row_id
        )
    """)
    with get_engine().begin() as conn:
        huérfanos = int(conn.execute(sql).scalar_one())
    return {
        "rule": "referential_consistency",
        "violations": huérfanos,
        "passed": huérfanos == 0,
    }


def _check_temporal_continuity() -> dict[str, Any]:
    sql = text("""
        WITH dups AS (
            SELECT mmsi, position_ts, COUNT(*) AS n
            FROM silver.stg_ais_position
            GROUP BY mmsi, position_ts
            HAVING COUNT(*) > 1
        ),
        neg_deltas AS (
            SELECT COUNT(*) AS n
            FROM silver.int_vessel_position_deltas
            WHERE time_delta_seconds IS NOT NULL AND time_delta_seconds < 0
        )
        SELECT
            (SELECT COUNT(*) FROM dups) AS duplicados,
            (SELECT n FROM neg_deltas)  AS deltas_negativos
    """)
    with get_engine().begin() as conn:
        row = conn.execute(sql).mappings().one()
    violaciones = int(row["duplicados"]) + int(row["deltas_negativos"])
    return {
        "rule": "temporal_continuity",
        "violations": violaciones,
        "duplicates": int(row["duplicados"]),
        "negative_deltas": int(row["deltas_negativos"]),
        "passed": violaciones == 0,
    }


def _check_spatial_continuity() -> dict[str, Any]:
    sql = text("""
        SELECT COUNT(*) AS excesos
        FROM silver.int_vessel_position_deltas
        WHERE calculated_speed_knots IS NOT NULL
          AND calculated_speed_knots > 60.0
    """)
    with get_engine().begin() as conn:
        excesos = int(conn.execute(sql).scalar_one())
    return {
        "rule": "spatial_continuity",
        "violations": excesos,
        "passed": excesos == 0,
    }


def run_quality_gate_2() -> dict[str, Any]:
    """Ejecuta las tres reglas y devuelve un resumen consolidado."""
    logger.info("Quality Gate 2 → iniciando validación de capa Silver")
    results = [
        _check_referential_consistency(),
        _check_temporal_continuity(),
        _check_spatial_continuity(),
    ]

    all_passed = all(r["passed"] for r in results)
    total_violations = sum(r["violations"] for r in results)

    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        logger.info("[QG2] %-28s %s (violations=%d)", r["rule"], status, r["violations"])

    summary = {
        "all_passed": all_passed,
        "total_violations": total_violations,
        "checks": results,
    }

    if not all_passed:
        logger.error("Quality Gate 2 FALLÓ con %d violaciones", total_violations)
    else:
        logger.info("Quality Gate 2 OK — sin violaciones")

    return summary

"""
Quality Gate 3 — Validación analítica de la capa Gold.

Tres reglas:

    1. gold_completeness: las métricas clave no contienen nulos
       ni ceros inconsistentes.
    2. cross_layer_consistency: la suma de distancias en
       gold.fact_vessel_voyage coincide con silver.int_vessel_tracks.
    3. freshness_check: Gold refleja el último estado de Silver
       sin un lag superior a 24 horas.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text

from src.storage.db import get_engine

logger = logging.getLogger("validation.quality_gate_3")

FRESHNESS_THRESHOLD_SECONDS = 86400  # 24 horas


def _check_gold_completeness() -> dict[str, Any]:
    """Verifica que fact_vessel_voyage no tenga nulos en columnas clave."""
    sql = text("""
        SELECT COUNT(*) AS inconsistentes
        FROM gold.fact_vessel_voyage
        WHERE mmsi IS NULL
           OR track_id IS NULL
           OR total_distance_km IS NULL
           OR duration_seconds IS NULL
           OR start_ts IS NULL
           OR end_ts IS NULL
           OR num_positions IS NULL
           OR num_positions <= 0
    """)
    with get_engine().begin() as conn:
        violaciones = int(conn.execute(sql).scalar_one())
    return {
        "rule": "gold_completeness",
        "violations": violaciones,
        "passed": violaciones == 0,
    }


def _check_cross_layer_consistency() -> dict[str, Any]:
    """Verifica que la suma de distancias cuadre entre Gold y Silver."""
    sql = text("""
        WITH silver_total AS (
            SELECT COALESCE(SUM(distance_km), 0) AS total
            FROM silver.int_vessel_tracks
            WHERE distance_km IS NOT NULL
        ),
        gold_total AS (
            SELECT COALESCE(SUM(total_distance_km), 0) AS total
            FROM gold.fact_vessel_voyage
        )
        SELECT ABS(silver_total.total - gold_total.total) AS diff
        FROM silver_total, gold_total
    """)
    with get_engine().begin() as conn:
        diff = float(conn.execute(sql).scalar_one())

    # Aceptamos hasta 1% de diferencia por redondeos
    silver_sql = text("SELECT COALESCE(SUM(distance_km), 0) FROM silver.int_vessel_tracks")
    with get_engine().begin() as conn:
        silver_total = float(conn.execute(silver_sql).scalar_one())

    tolerance = max(silver_total * 0.01, 0.001)
    passed = diff <= tolerance

    return {
        "rule": "cross_layer_consistency",
        "violations": 0 if passed else 1,
        "absolute_diff": diff,
        "tolerance": tolerance,
        "passed": passed,
    }


def _check_freshness() -> dict[str, Any]:
    """Verifica que Gold no esté más de 24h detrás de Silver."""
    sql = text("""
        SELECT EXTRACT(EPOCH FROM (
            (SELECT MAX(position_ts) FROM silver.stg_ais_position)
            -
            (SELECT MAX(end_ts) FROM gold.fact_vessel_voyage)
        ))::DOUBLE PRECISION AS lag_seconds
    """)
    with get_engine().begin() as conn:
        lag = conn.execute(sql).scalar_one()

    lag_seconds = float(lag) if lag is not None else 0.0
    passed = abs(lag_seconds) <= FRESHNESS_THRESHOLD_SECONDS

    return {
        "rule": "freshness_check",
        "violations": 0 if passed else 1,
        "lag_seconds": lag_seconds,
        "threshold_seconds": FRESHNESS_THRESHOLD_SECONDS,
        "passed": passed,
    }


def run_quality_gate_3() -> dict[str, Any]:
    """Ejecuta las tres reglas y devuelve el resumen consolidado."""
    logger.info("Quality Gate 3 → iniciando validación analítica de Gold")
    results = [
        _check_gold_completeness(),
        _check_cross_layer_consistency(),
        _check_freshness(),
    ]

    all_passed = all(r["passed"] for r in results)
    total_violations = sum(r["violations"] for r in results)

    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        logger.info("[QG3] %-28s %s (violations=%d)", r["rule"], status, r["violations"])

    summary = {
        "all_passed": all_passed,
        "total_violations": total_violations,
        "checks": results,
    }

    if not all_passed:
        logger.error("Quality Gate 3 FALLÓ con %d violaciones", total_violations)
    else:
        logger.info("Quality Gate 3 OK — sin violaciones")

    return summary

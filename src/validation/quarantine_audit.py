"""
Auditoría estadística de sesgo en la tabla quarantine.quarantine_records.

Analiza la distribución de rechazos del Quality Gate 1 para detectar
sesgos de selección que puedan distorsionar los entrenamientos de ML.

Métodos estadísticos aplicados:

    1. Distribución por regla (Chi-cuadrado de uniformidad).
    2. Concentración por MMSI (Gini de rechazos).
    3. Distribución temporal (ventanas de 6 horas).
    4. Concentración geográfica aproximada (grid 10x10 de lat/lon).

Salida: diccionario con métricas y alertas si hay sesgo significativo.
"""
from __future__ import annotations

import json
import logging
import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import numpy as np
from scipy import stats
from sqlalchemy import text

from src.storage.db import get_engine

logger = logging.getLogger("validation.quarantine_audit")

# Umbrales de significancia estadística
CHI_SQUARE_ALPHA = 0.05
GINI_ALERT_THRESHOLD = 0.6
MIN_RECORDS_FOR_AUDIT = 10


def _load_quarantine_records() -> list[dict[str, Any]]:
    """Carga todos los registros de cuarentena como diccionarios."""
    sql = text("""
        SELECT
            source_record_id,
            failure_reason,
            quality_rule,
            ingestion_run_id,
            original_payload,
            quarantine_timestamp
        FROM quarantine.quarantine_records
        ORDER BY quarantine_timestamp
    """)
    with get_engine().begin() as conn:
        rows = conn.execute(sql).mappings().all()
    return [dict(r) for r in rows]


def _compute_rule_distribution(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Distribución de violaciones por regla + test chi-cuadrado de uniformidad."""
    rule_counter: Counter[str] = Counter()
    for rec in records:
        rules = (rec.get("quality_rule") or "").split(";")
        for r in rules:
            r = r.strip()
            if r:
                rule_counter[r] += 1

    total = sum(rule_counter.values())
    if total == 0:
        return {"total_violations": 0, "rules": {}, "chi_square": None}

    # Chi-cuadrado de uniformidad: ¿se distribuyen las violaciones por igual?
    observed = np.array(list(rule_counter.values()), dtype=float)
    expected = np.full_like(observed, observed.mean())
    chi2, p_value = stats.chisquare(observed, expected)

    return {
        "total_violations": int(total),
        "rules": dict(rule_counter),
        "chi_square": {
            "statistic": float(chi2),
            "p_value": float(p_value),
            "is_uniform": bool(p_value > CHI_SQUARE_ALPHA),
        },
    }


def _compute_mmsi_concentration(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Índice de Gini de la concentración de rechazos por MMSI."""
    mmsi_counter: Counter[str] = Counter()
    for rec in records:
        payload = rec.get("original_payload") or {}
        mmsi = payload.get("mmsi")
        if mmsi:
            mmsi_counter[str(mmsi)] += 1

    if not mmsi_counter:
        return {"gini": None, "distinct_mmsi": 0}

    counts = np.array(sorted(mmsi_counter.values()), dtype=float)
    n = len(counts)

    # Gini clásico: G = (2 * sum(i * x_i) / (n * sum(x_i))) - (n + 1) / n
    sorted_c = np.sort(counts)
    cumulative = np.cumsum(sorted_c)
    gini = (2 * np.sum(np.arange(1, n + 1) * sorted_c) / (n * cumulative[-1])) - (n + 1) / n

    return {
        "gini": float(gini),
        "distinct_mmsi": int(n),
        "top_offenders": mmsi_counter.most_common(5),
        "is_concentrated": bool(gini > GINI_ALERT_THRESHOLD),
    }


def _compute_temporal_distribution(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Distribución de rechazos por ventana de 6 horas."""
    window_counter: Counter[str] = Counter()
    for rec in records:
        ts = rec.get("quarantine_timestamp")
        if ts is None:
            continue
        window = ts.replace(hour=(ts.hour // 6) * 6, minute=0, second=0, microsecond=0)
        window_counter[window.isoformat()] += 1

    if not window_counter:
        return {"windows": {}, "is_uniform": None}

    observed = np.array(list(window_counter.values()), dtype=float)
    if len(observed) > 1:
        expected = np.full_like(observed, observed.mean())
        chi2, p_value = stats.chisquare(observed, expected)
        is_uniform = bool(p_value > CHI_SQUARE_ALPHA)
    else:
        chi2, p_value, is_uniform = 0.0, 1.0, True

    return {
        "windows": dict(window_counter),
        "chi_square": {"statistic": float(chi2), "p_value": float(p_value)},
        "is_uniform": is_uniform,
    }


def _compute_geographic_distribution(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Distribución geográfica en grid 10x10 de lat/lon."""
    grid_counter: Counter[str] = Counter()
    for rec in records:
        payload = rec.get("original_payload") or {}
        lat = payload.get("latitude")
        lon = payload.get("longitude")
        if lat is None or lon is None:
            continue
        try:
            lat_i = int(float(lat) // 10) * 10
            lon_i = int(float(lon) // 10) * 10
            grid_counter[f"{lat_i},{lon_i}"] += 1
        except (ValueError, TypeError):
            continue

    return {
        "grid_cells": dict(grid_counter),
        "distinct_cells": len(grid_counter),
        "top_cells": grid_counter.most_common(5),
    }


def run_quarantine_audit() -> dict[str, Any]:
    """
    Ejecuta la auditoría completa y devuelve el reporte estructurado.

    Returns:
        Diccionario con todas las métricas y una lista de alertas.
    """
    logger.info("Iniciando auditoría de sesgo en cuarentena")

    records = _load_quarantine_records()
    total = len(records)

    if total < MIN_RECORDS_FOR_AUDIT:
        logger.warning(
            "Muy pocos registros (%d) para un análisis estadístico confiable",
            total,
        )

    rules = _compute_rule_distribution(records)
    mmsi = _compute_mmsi_concentration(records)
    temporal = _compute_temporal_distribution(records)
    geo = _compute_geographic_distribution(records)

    alerts: list[str] = []
    if rules.get("chi_square") and not rules["chi_square"]["is_uniform"]:
        alerts.append(
            f"Distribución de reglas NO uniforme (p={rules['chi_square']['p_value']:.4f}). "
            f"Algunas reglas rechazan más que otras."
        )
    if mmsi.get("is_concentrated"):
        alerts.append(
            f"Alta concentración de rechazos por MMSI (Gini={mmsi['gini']:.3f}). "
            f"Posible sesgo hacia embarcaciones específicas."
        )
    if temporal.get("is_uniform") is False:
        alerts.append(
            "Distribución temporal NO uniforme. "
            "Puede indicar problemas de sincronización o ventanas de ingestión."
        )
    if geo["distinct_cells"] > 0 and geo["distinct_cells"] < 3:
        alerts.append(
            f"Baja diversidad geográfica en rechazos ({geo['distinct_cells']} celdas). "
            f"Posible sesgo por zona."
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_records": total,
        "rule_distribution": rules,
        "mmsi_concentration": mmsi,
        "temporal_distribution": temporal,
        "geographic_distribution": geo,
        "alerts": alerts,
        "has_significant_bias": len(alerts) > 0,
    }

    logger.info(
        "Auditoría completa: %d registros, %d alertas",
        total, len(alerts),
    )
    for alert in alerts:
        logger.warning("[AUDIT] %s", alert)

    return report


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    print(json.dumps(run_quarantine_audit(), indent=2, default=str))

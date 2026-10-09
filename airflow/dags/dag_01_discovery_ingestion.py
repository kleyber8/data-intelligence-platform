"""
DAG 01 — Discovery & Ingestion → Bronze → Quality Gate 1.

Orquesta la cadena completa:
    check_source
        → download_and_store_raw
        → load_to_bronze
        → run_quality_gate_1
        → generate_ingestion_summary
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from airflow.decorators import dag, task

from ingestion.maritime.noaa_ais import run_ingestion
from src.storage.bronze_writer import count_bronze_rows, write_bronze_from_landing
from src.validation.quality_gate_1 import run_quality_gate_1

logger = logging.getLogger(__name__)

DEFAULT_ARGS: dict[str, Any] = {
    "owner": "data-eng",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "email_on_failure": False,
}


@dag(
    dag_id="dag_01_discovery_ingestion",
    description="Ingesta AIS → Bronze → Quality Gate 1",
    schedule=None,             # trigger manual en Fase 2
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["maritime", "ingestion", "bronze", "quality-gate-1"],
    doc_md=__doc__,
)
def dag_discovery_ingestion():

    @task(task_id="check_source")
    def check_source() -> dict[str, str]:
        """Comprueba configuración mínima antes de arrancar la cadena."""
        from src.config import settings
        logger.info("Verificando configuración del pipeline…")
        return {
            "data_lake": str(settings.data_lake_root),
            "s3_endpoint": settings.s3_endpoint_url,
            "postgres_host": settings.postgres_host,
        }

    @task(task_id="download_and_store_raw", execution_timeout=timedelta(minutes=10))
    def download_and_store_raw(_: dict[str, str]) -> dict[str, Any]:
        """Descarga (o genera) el dataset AIS y lo sube a Landing."""
        meta = run_ingestion(source="synthetic")
        logger.info("Ingestión completada: %s", meta["ingestion_run_id"])
        return meta

    @task(task_id="load_to_bronze", execution_timeout=timedelta(minutes=15))
    def load_to_bronze(meta: dict[str, Any]) -> dict[str, Any]:
        """Carga el Parquet de Landing en bronze.bronze_ais_position."""
        run_id = meta["ingestion_run_id"]
        rows = write_bronze_from_landing(run_id)
        logger.info("Bronze cargado: %d filas", rows)
        return {"ingestion_run_id": run_id, "bronze_rows": rows}

    @task(task_id="run_quality_gate_1", execution_timeout=timedelta(minutes=10))
    def run_qg1(meta: dict[str, Any]) -> dict[str, Any]:
        """Aplica las reglas de Quality Gate 1."""
        return run_quality_gate_1(meta["ingestion_run_id"])

    @task(task_id="generate_ingestion_summary")
    def generate_ingestion_summary(
        meta: dict[str, Any],
        qg1: dict[str, Any],
    ) -> dict[str, Any]:
        """Composición final: log resumen y verificación de persistencia."""
        run_id = meta["ingestion_run_id"]
        bronze_count = count_bronze_rows(run_id)
        summary = {
            "ingestion_run_id": run_id,
            "rows_landed": meta.get("bronze_rows", 0),
            "rows_in_bronze": bronze_count,
            "rows_valid": qg1.get("valid", 0),
            "rows_quarantined": qg1.get("invalid", 0),
        }
        logger.info("=== Resumen del pipeline ===")
        for k, v in summary.items():
            logger.info("  %s: %s", k, v)
        return summary

    src = check_source()
    raw = download_and_store_raw(src)
    bronze = load_to_bronze(raw)
    qg1 = run_qg1(bronze)
    generate_ingestion_summary(bronze, qg1)


dag_discovery_ingestion()

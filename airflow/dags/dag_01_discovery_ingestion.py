from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import Any
from airflow.decorators import dag, task

from ingestion.maritime.noaa_ais import run_ingestion
from ingestion.ports.world_port_index import run as run_wpi
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
    description="Ingesta AIS y Puertos WPI → Bronze → Quality Gate 1",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["maritime", "ingestion", "bronze", "quality-gate-1"],
)
def dag_discovery_ingestion():

    @task(task_id="check_source")
    def check_source() -> dict[str, str]:
        from src.config import settings
        logger.info("Verificando configuración del pipeline…")
        return {"data_lake": str(settings.data_lake_root)}

    @task(task_id="ingest_wpi_ports", execution_timeout=timedelta(minutes=5))
    def ingest_wpi_ports(_: dict[str, str]) -> None:
        """Descarga los puertos oficiales de la NGA y los carga en bronze.bronze_ports."""
        logger.info("Iniciando ingesta del World Port Index (NGA)…")
        try:
            run_wpi()
            logger.info("Ingesta de puertos WPI completada con éxito.")
        except Exception as e:
            logger.error(f"Error en la ingesta WPI: {e}")
            raise

    @task(task_id="download_and_store_raw", execution_timeout=timedelta(minutes=10))
    def download_and_store_raw(_: dict[str, str]) -> dict[str, Any]:
        meta = run_ingestion(source="synthetic")
        return meta

    @task(task_id="load_to_bronze", execution_timeout=timedelta(minutes=15))
    def load_to_bronze(meta: dict[str, Any]) -> dict[str, Any]:
        run_id = meta["ingestion_run_id"]
        rows = write_bronze_from_landing(run_id)
        return {"ingestion_run_id": run_id, "bronze_rows": rows}

    @task(task_id="run_quality_gate_1", execution_timeout=timedelta(minutes=10))
    def run_qg1(meta: dict[str, Any]) -> dict[str, Any]:
        return run_quality_gate_1(meta["ingestion_run_id"])

    @task(task_id="generate_ingestion_summary")
    def generate_ingestion_summary(meta: dict[str, Any], qg1: dict[str, Any]) -> dict[str, Any]:
        run_id = meta["ingestion_run_id"]
        bronze_count = count_bronze_rows(run_id)
        return {
            "ingestion_run_id": run_id,
            "rows_landed": meta.get("bronze_rows", 0),
            "rows_in_bronze": bronze_count,
            "rows_valid": qg1.get("valid", 0),
            "rows_quarantined": qg1.get("invalid", 0),
        }

    # Orquestación
    src = check_source()
    ports = ingest_wpi_ports(src)
    raw = download_and_store_raw(src)
    bronze = load_to_bronze(raw)
    qg1 = run_qg1(bronze)
    
    # La ingesta de puertos y la de AIS corren en paralelo, luego el resumen
    generate_ingestion_summary(bronze, qg1)

dag_discovery_ingestion()
